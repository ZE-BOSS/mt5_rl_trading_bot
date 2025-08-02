"""
FastAPI server for MT5 Trading Bot
Provides REST API and WebSocket endpoints for frontend communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime
import threading
import queue
import os
import sys
import traceback

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.core.bot import TradingBot
from src.utils.logger import Logger
from src.backtesting.engine import BacktestEngine, fetch_mt5_data, HybridStrategyWrapper
from src.core.orb_strategy import OpeningRangeBreakout
from src.core.risk_manager import RiskManager
from src.core.pattern_detector import PatternDetector
from src.core.sr_levels import SupportResistance as SRLevels
from src.reinforcement.agent import DQNAgent
from src.reinforcement.environment import TradingEnvironment
import MetaTrader5 as mt5

app = FastAPI(title="MT5 Trading Bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
trading_bot = None
bot_thread = None
bot_status = {"running": False, "connected": False, "error": None}
websocket_connections: List[WebSocket] = []
message_queue = queue.Queue()
logger = Logger('api_server.log')

# Pydantic models
class BotConfig(BaseModel):
    symbols: List[str]
    risk_per_trade: float
    max_drawdown: float
    stop_loss: int
    take_profit: int

class TradeRequest(BaseModel):
    symbol: str
    action: str  # 'buy' or 'sell'
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    episodes: int = 100

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.log(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.log(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

# Background task to broadcast bot updates
async def broadcast_bot_updates():
    while True:
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                await manager.broadcast(message)
        except Exception as e:
            logger.log_error(f"Broadcast error: {e}")
        await asyncio.sleep(0.1)

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_bot_updates())

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for now - can be extended for client commands
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API Endpoints

@app.get("/")
async def root():
    return {"message": "MT5 Trading Bot API", "status": "running"}

@app.get("/bot/status")
async def get_bot_status():
    """Get current bot status"""
    global bot_status
    if trading_bot:
        # Update MT5 connection status
        bot_status["connected"] = trading_bot.mt5_connected
    return bot_status

@app.post("/bot/start")
async def start_bot(config: Optional[BotConfig] = None):
    """Start the trading bot"""

    if config is None:
        raise HTTPException(status_code=400, detail="Bot config is required")

    if not config.symbols:
        raise HTTPException(status_code=400, detail="At least one symbol must be provided")
    
    try:
        logger.log(f"Received config: {config}")
    
        if bot_status["running"]:
            raise HTTPException(status_code=400, detail="Bot is already running")
        
        # Initialize bot
        trading_bot = TradingBot()
        
        # Update config if provided
        if config:
            trading_bot.config['symbols'] = config.symbols
            trading_bot.config['risk_parameters']['risk_per_trade'] = config.risk_per_trade
            trading_bot.config['risk_parameters']['max_drawdown'] = config.max_drawdown
            trading_bot.config['risk_parameters']['stop_loss'] = config.stop_loss
            trading_bot.config['risk_parameters']['take_profit'] = config.take_profit
        
        # Start bot in separate thread
        def run_bot():
            try:
                trading_bot.run()
            except Exception as e:
                tb = traceback.format_exc()
                bot_status["error"] = str(e)
                bot_status["running"] = False
                logger.log_error(f"Bot error: {e}\n{tb}")
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        bot_status["running"] = True
        bot_status["error"] = None
        
        # Broadcast status update
        message_queue.put({
            "type": "bot_status",
            "data": bot_status
        })
        
        return {"message": "Bot started successfully", "status": bot_status}
        
    except Exception as e:
        tb = traceback.format_exc()
        bot_status["error"] = str(e)
        logger.log_error(f"Failed to start bot: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    global trading_bot, bot_thread, bot_status
    
    try:
        if not bot_status["running"]:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        bot_status["running"] = False
        
        # Disconnect from MT5
        if trading_bot and trading_bot.mt5_connected:
            mt5.shutdown()
            trading_bot.mt5_connected = False
        
        # Broadcast status update
        message_queue.put({
            "type": "bot_status",
            "data": bot_status
        })
        
        return {"message": "Bot stopped successfully", "status": bot_status}
        
    except Exception as e:
        logger.log_error(f"Failed to stop bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bot/config")
async def get_bot_config():
    """Get current bot configuration"""
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Bot not initialized")
    
    return {
        "symbols": trading_bot.config.get('symbols', []),
        "risk_parameters": trading_bot.config.get('risk_parameters', {}),
        "trading_settings": trading_bot.config.get('trading_settings', {})
    }

@app.post("/bot/config")
async def update_bot_config(config: BotConfig):
    """Update bot configuration"""
    if not trading_bot:
        raise HTTPException(status_code=400, detail="Bot not initialized")
    
    # Update configuration
    trading_bot.config['symbols'] = config.symbols
    trading_bot.config['risk_parameters']['risk_per_trade'] = config.risk_per_trade
    trading_bot.config['risk_parameters']['max_drawdown'] = config.max_drawdown
    trading_bot.config['risk_parameters']['stop_loss'] = config.stop_loss
    trading_bot.config['risk_parameters']['take_profit'] = config.take_profit
    
    return {"message": "Configuration updated successfully"}

@app.get("/positions")
async def get_positions():
    """Get current open positions"""
    try:
        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="Failed to connect to MT5")
        
        positions = mt5.positions_get()
        mt5.shutdown()
        
        if positions is None:
            return {"positions": []}
        
        positions_list = []
        for pos in positions:
            positions_list.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "buy" if pos.type == 0 else "sell",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "profit": pos.profit,
                "sl": pos.sl,
                "tp": pos.tp
            })
        
        return {"positions": positions_list}
        
    except Exception as e:
        logger.log_error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    """Execute a manual trade"""
    try:
        if not trading_bot:
            raise HTTPException(status_code=400, detail="Bot not initialized")
        
        # Create order signal
        current_price = trading_bot.data_fetcher.fetch_live_price(trade.symbol)
        if not current_price:
            raise HTTPException(status_code=500, detail="Failed to get current price")
        
        order_signal = {
            'symbol': trade.symbol,
            'direction': trade.action,
            'price': current_price,
            'stop_loss': trade.stop_loss or (current_price - 0.001 if trade.action == 'buy' else current_price + 0.001),
            'take_profit': trade.take_profit or (current_price + 0.002 if trade.action == 'buy' else current_price - 0.002)
        }
        
        # Execute trade
        result = trading_bot.trader.execute_order(order_signal, trade.volume)
        
        # Broadcast trade update
        message_queue.put({
            "type": "trade_executed",
            "data": {
                "symbol": trade.symbol,
                "action": trade.action,
                "volume": trade.volume,
                "price": current_price,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return {"message": "Trade executed successfully", "result": result}
        
    except Exception as e:
        logger.log_error(f"Failed to execute trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str, bars: int = 100):
    """Get market data for a symbol"""
    try:
        if not trading_bot:
            raise HTTPException(status_code=400, detail="Bot not initialized")
        
        data = trading_bot.data_fetcher.fetch_ohlc_data(symbol, bars)
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Convert to JSON-serializable format
        data_dict = data.to_dict('records')
        for record in data_dict:
            if 'time' in record:
                record['time'] = record['time'].isoformat()
        
        return {"symbol": symbol, "data": data_dict}
        
    except Exception as e:
        logger.log_error(f"Failed to get market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a backtest"""
    try:
        from datetime import datetime
        
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # Fetch historical data
        historical_data = fetch_mt5_data(request.symbol, mt5.TIMEFRAME_M15, start_date, end_date)
        
        if historical_data is None or historical_data.empty:
            raise HTTPException(status_code=404, detail="No historical data available")
        
        # Initialize components
        orb_strategy = OpeningRangeBreakout('07:30', '08:00')
        risk_manager = RiskManager(risk_per_trade=0.02, account_balance=10000)
        pattern_detector = PatternDetector()
        sr_levels = SRLevels(symbol=request.symbol, timeframe=mt5.TIMEFRAME_M15)
        
        env = TradingEnvironment(historical_data, initial_balance=10000)
        agent = DQNAgent(state_size=env.observation_space.shape[0], action_size=env.action_space.n, config={
            "memory_size": 1000,
            "discount_factor": 0.95,
            "exploration_strategy": {"initial_epsilon": 0.1, "final_epsilon": 0.01, "decay_steps": 100},
            "batch_size": 32,
            "update_target_frequency": 10,
            "learning_rate": 0.001,
            "network_architecture": {"layers": [64, 64], "activation": "relu"}
        })
        
        strategy = HybridStrategyWrapper(
            orb_strategy, risk_manager, pattern_detector, sr_levels,
            rl_agent=agent, env=env, historical_data=historical_data, symbol=request.symbol
        )
        
        # Run backtest
        engine = BacktestEngine(strategy, historical_data, 10000, risk_manager, agent, env, request.symbol)
        engine.run_backtest()
        report = engine.generate_report()
        
        # Convert report to JSON-serializable format
        if not report.empty:
            report_dict = report.to_dict('records')
            for record in report_dict:
                for key, value in record.items():
                    if hasattr(value, 'isoformat'):
                        record[key] = value.isoformat()
        else:
            report_dict = []
        
        return {
            "symbol": request.symbol,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "results": report_dict,
            "summary": {
                "total_trades": len(report_dict),
                "final_balance": engine.balance,
                "total_return": engine.balance - 10000,
                "max_drawdown": engine.max_drawdown
            }
        }
        
    except Exception as e:
        logger.log_error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance")
async def get_performance():
    """Get bot performance metrics"""
    try:
        # Read performance data from logs/files
        # This is a simplified version - in production, you'd have a proper database
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_error(f"Failed to get performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
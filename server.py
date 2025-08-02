"""
Enhanced FastAPI server for MT5 Trading Bot
Provides REST API and WebSocket endpoints with comprehensive real-time monitoring
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime, timedelta
import threading
import queue
import os
import sys
import traceback
import uuid
from contextlib import asynccontextmanager

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.bot import TradingBot
from src.utils.logger import Logger
from src.backtesting.engine import BacktestEngine, fetch_mt5_data, HybridStrategyWrapper
from src.core.orb_strategy import OpeningRangeBreakout
from src.core.risk_manager import RiskManager
from src.core.pattern_detector import PatternDetector
from src.core.sr_levels import SupportResistance as SRLevels
from src.reinforcement.agent import DQNAgent
from src.reinforcement.environment import TradingEnvironment
from src.backtesting.optimizer import StrategyOptimizer
from src.reinforcement.trainer import Trainer
import MetaTrader5 as mt5

# Global variables for real-time monitoring
websocket_connections: List[WebSocket] = []
message_queue = asyncio.Queue()
trading_bot = None
bot_thread = None
bot_status = {
    "running": False, 
    "connected": False, 
    "error": None,
    "trades_this_week": 0,
    "last_trade_time": None,
    "performance_metrics": {}
}

# Enhanced logger for real-time streaming
class RealTimeLogger:
    def __init__(self, base_logger: Logger):
        self.base_logger = base_logger
        self.session_id = str(uuid.uuid4())
    
    async def log_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """Log event and broadcast to WebSocket clients"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "event_type": event_type,
            "level": level,
            "data": data
        }
        
        # Log to file
        self.base_logger.log(f"[{event_type}] {json.dumps(data)}")
        
        # Broadcast to WebSocket clients
        await message_queue.put(log_entry)
    
    async def log_trade_entry(self, trade_data: Dict[str, Any]):
        await self.log_event("TRADE_ENTRY", trade_data)
    
    async def log_trade_exit(self, trade_data: Dict[str, Any]):
        await self.log_event("TRADE_EXIT", trade_data)
    
    async def log_decision(self, decision_data: Dict[str, Any]):
        await self.log_event("DECISION", decision_data)
    
    async def log_error(self, error_data: Dict[str, Any]):
        await self.log_event("ERROR", error_data, "ERROR")
    
    async def log_performance(self, metrics: Dict[str, Any]):
        await self.log_event("PERFORMANCE", metrics)

# Initialize enhanced logger
base_logger = Logger('enhanced_api_server.log')
rt_logger = RealTimeLogger(base_logger)

# Pydantic models
class BotConfig(BaseModel):
    symbols: List[str]
    risk_per_trade: float
    max_drawdown: float
    stop_loss: int
    take_profit: int
    min_trades_per_week: int = 3
    max_trades_per_week: int = 10

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
    optimize: bool = False

class OptimizationRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    parameter_grid: Dict[str, List[Any]]
    metric: str = "sharpe"

# WebSocket connection manager with enhanced features
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_stats = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections.append(websocket)
        self.connection_stats[connection_id] = {
            "connected_at": datetime.now().isoformat(),
            "messages_sent": 0
        }
        
        await rt_logger.log_event("WEBSOCKET_CONNECT", {
            "connection_id": connection_id,
            "total_connections": len(self.active_connections)
        })
        
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "bot_status": bot_status
        }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        asyncio.create_task(rt_logger.log_event("WEBSOCKET_DISCONNECT", {
            "total_connections": len(self.active_connections)
        }))

    async def broadcast(self, message: dict):
        if self.active_connections:
            message_str = json.dumps(message, default=str)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

# Enhanced Trading Bot with real-time monitoring
class EnhancedTradingBot(TradingBot):
    def __init__(self, config_path='config/bot_config.yaml'):
        super().__init__(config_path)
        self.rt_logger = rt_logger
        self.trades_this_week = 0
        self.week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.min_trades_per_week = 3
        self.max_trades_per_week = 10
        self.trade_frequency_adjustment = 1.0
    
    async def log_initialization(self):
        """Log bot initialization with configuration"""
        await self.rt_logger.log_event("BOT_INITIALIZATION", {
            "config": {
                "symbols": self.config['symbols'],
                "risk_parameters": self.config['risk_parameters'],
                "trading_settings": self.config['trading_settings']
            },
            "rl_enabled": self.rl_agent is not None,
            "mt5_connected": self.mt5_connected
        })
    
    def update_weekly_trade_count(self):
        """Update weekly trade count and adjust frequency if needed"""
        current_week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        current_week_start -= timedelta(days=current_week_start.weekday())
        
        if current_week_start > self.week_start:
            # New week started
            asyncio.create_task(self.rt_logger.log_event("WEEK_SUMMARY", {
                "previous_week_trades": self.trades_this_week,
                "target_range": f"{self.min_trades_per_week}-{self.max_trades_per_week}",
                "performance": "within_range" if self.min_trades_per_week <= self.trades_this_week <= self.max_trades_per_week else "outside_range"
            }))
            
            self.trades_this_week = 0
            self.week_start = current_week_start
    
    def should_increase_aggression(self) -> bool:
        """Determine if trading should be more aggressive"""
        days_into_week = (datetime.now() - self.week_start).days
        if days_into_week >= 3 and self.trades_this_week < self.min_trades_per_week:
            return True
        return False
    
    def should_decrease_aggression(self) -> bool:
        """Determine if trading should be less aggressive"""
        return self.trades_this_week >= self.max_trades_per_week
    
    async def execute_enhanced_trading_logic(self):
        """Enhanced trading logic with real-time monitoring"""
        self.update_weekly_trade_count()
        
        for symbol in self.config['symbols']:
            try:
                if self.should_decrease_aggression():
                    await self.rt_logger.log_decision({
                        "symbol": symbol,
                        "decision": "skip_max_trades_reached",
                        "trades_this_week": self.trades_this_week,
                        "max_trades": self.max_trades_per_week
                    })
                    continue
                
                market_data = self.data_fetcher.fetch_ohlc_data(symbol, bars=100)
                if market_data is None or market_data.empty:
                    await self.rt_logger.log_decision({
                        "symbol": symbol,
                        "decision": "skip_no_data",
                        "reason": "No market data available"
                    })
                    continue
                
                # Skip during news events
                if self.news_filter.is_high_impact_event(symbol):
                    await self.rt_logger.log_decision({
                        "symbol": symbol,
                        "decision": "skip_news_event",
                        "reason": "High impact news event detected"
                    })
                    continue
                
                # Enhanced ORB Strategy with frequency adjustment
                s_r_levels = self.data_fetcher.get_sr_levels(symbol)
                patterns = self.pattern_detector.analyze_patterns(market_data)
                current_row = market_data.iloc[-1].to_dict()
                
                # Adjust aggression based on weekly trade count
                aggression_multiplier = 1.0
                if self.should_increase_aggression():
                    aggression_multiplier = 1.5
                    await self.rt_logger.log_decision({
                        "symbol": symbol,
                        "decision": "increase_aggression",
                        "reason": f"Only {self.trades_this_week} trades this week, need minimum {self.min_trades_per_week}",
                        "aggression_multiplier": aggression_multiplier
                    })
                
                if self.orb_strategy.is_setup_valid(current_row, s_r_levels, patterns):
                    entry_signal = self.orb_strategy.get_entry_signal(current_row)
                    if entry_signal:
                        # Apply aggression multiplier to position sizing
                        base_lot_size = self.risk_manager.calculate_position_size(
                            symbol, 
                            entry_signal['price'], 
                            entry_signal['stop_loss']
                        )
                        lot_size = base_lot_size * aggression_multiplier
                        
                        # Execute trade
                        result = self.trader.execute_order(entry_signal, lot_size)
                        self.trades_this_week += 1
                        
                        await self.rt_logger.log_trade_entry({
                            "symbol": entry_signal['symbol'],
                            "direction": entry_signal['direction'],
                            "price": entry_signal['price'],
                            "lot_size": lot_size,
                            "stop_loss": entry_signal['stop_loss'],
                            "take_profit": entry_signal.get('take_profit', 0),
                            "patterns_detected": patterns,
                            "sr_levels": s_r_levels,
                            "aggression_multiplier": aggression_multiplier,
                            "trades_this_week": self.trades_this_week,
                            "execution_result": result
                        })
                        
                        # Update global status
                        bot_status["trades_this_week"] = self.trades_this_week
                        bot_status["last_trade_time"] = datetime.now().isoformat()
                
                # RL Strategy with enhanced logging
                if self.rl_agent:
                    state = self.prepare_rl_state(market_data)
                    action = self.rl_agent.act(state)
                    
                    await self.rt_logger.log_decision({
                        "symbol": symbol,
                        "decision": "rl_action",
                        "action": action,
                        "state_features": state.tolist()[:10],  # Log first 10 features
                        "epsilon": getattr(self.rl_agent, 'epsilon', 0)
                    })
                    
                    if action != 0:  # Not hold
                        self.execute_rl_action(action, symbol)
                        
            except Exception as e:
                await self.rt_logger.log_error({
                    "symbol": symbol,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

# Enhanced Backtest Engine with real-time monitoring
class EnhancedBacktestEngine(BacktestEngine):
    def __init__(self, strategy, historical_data, starting_balance, risk_manager, agent, env, symbol):
        super().__init__(strategy, historical_data, starting_balance, risk_manager, agent, env, symbol)
        self.rt_logger = rt_logger
        self.session_id = str(uuid.uuid4())
        self.trades_this_week = 0
        self.current_week = None
        self.min_trades_per_week = 3
        self.max_trades_per_week = 10
    
    async def run_enhanced_backtest(self):
        """Enhanced backtest with real-time monitoring and trade frequency constraints"""
        await self.rt_logger.log_event("BACKTEST_START", {
            "session_id": self.session_id,
            "symbol": self.symbol,
            "data_points": len(self.historical_data),
            "starting_balance": self.starting_balance,
            "trade_constraints": {
                "min_trades_per_week": self.min_trades_per_week,
                "max_trades_per_week": self.max_trades_per_week
            }
        })
        
        trade_count = 0
        weekly_stats = {}
        
        for index, row in self.historical_data.iterrows():
            row_week = row['Time'].isocalendar().week
            
            # Track weekly trades
            if self.current_week is None:
                self.current_week = row_week
                self.trades_this_week = 0
            
            if row_week != self.current_week:
                # Log weekly summary
                weekly_stats[self.current_week] = {
                    "trades": self.trades_this_week,
                    "within_target": self.min_trades_per_week <= self.trades_this_week <= self.max_trades_per_week,
                    "balance": self.balance
                }
                
                await self.rt_logger.log_event("WEEKLY_SUMMARY", {
                    "week": self.current_week,
                    "trades": self.trades_this_week,
                    "target_range": f"{self.min_trades_per_week}-{self.max_trades_per_week}",
                    "balance": self.balance,
                    "within_target": weekly_stats[self.current_week]["within_target"]
                })
                
                self.current_week = row_week
                self.trades_this_week = 0
            
            # Check balance
            if self.balance <= 0:
                await self.rt_logger.log_error({
                    "session_id": self.session_id,
                    "error": "Account balance depleted",
                    "final_balance": self.balance,
                    "total_trades": trade_count
                })
                break
            
            # Apply trade frequency constraints
            if self.trades_this_week >= self.max_trades_per_week:
                await self.rt_logger.log_decision({
                    "session_id": self.session_id,
                    "decision": "skip_max_weekly_trades",
                    "trades_this_week": self.trades_this_week,
                    "max_allowed": self.max_trades_per_week
                })
                continue
            
            # Check for entry
            if not self.in_trade and self.strategy.should_enter(row):
                entry_price = row['Close']
                
                # Adjust position size based on weekly trade frequency
                base_position_size = self.strategy.calculate_position_size(entry_price)
                
                # Increase aggression if under minimum trades
                days_into_week = (row['Time'] - row['Time'].replace(hour=0, minute=0, second=0, microsecond=0)).days % 7
                if days_into_week >= 3 and self.trades_this_week < self.min_trades_per_week:
                    position_size = base_position_size * 1.3  # 30% more aggressive
                    await self.rt_logger.log_decision({
                        "session_id": self.session_id,
                        "decision": "increase_position_size",
                        "reason": "Under minimum weekly trades",
                        "base_size": base_position_size,
                        "adjusted_size": position_size
                    })
                else:
                    position_size = base_position_size
                
                self.execute_trade(entry_price, position_size, row)
                
                await self.rt_logger.log_trade_entry({
                    "session_id": self.session_id,
                    "trade_id": len(self.results),
                    "symbol": self.symbol,
                    "entry_price": entry_price,
                    "position_size": position_size,
                    "balance_before": self.balance,
                    "trades_this_week": self.trades_this_week,
                    "timestamp": row['Time'].isoformat()
                })
                
                self.in_trade = True
                trade_count += 1
                self.trades_this_week += 1
            
            # Check for exit
            if self.in_trade:
                exit_signal = self.strategy.should_exit(row)
                if isinstance(exit_signal, dict):
                    exit_price = exit_signal.get("exit_price", row['Close'])
                    self.close_trade(exit_price, row)
                    
                    # Calculate P&L for logging
                    if self.results:
                        last_trade = self.results[-1]
                        pnl = last_trade.get('outcome', 0)
                        
                        await self.rt_logger.log_trade_exit({
                            "session_id": self.session_id,
                            "trade_id": len(self.results),
                            "symbol": self.symbol,
                            "exit_price": exit_price,
                            "exit_reason": exit_signal.get("reason", "Unknown"),
                            "pnl": pnl,
                            "balance_after": self.balance,
                            "timestamp": row['Time'].isoformat()
                        })
                    
                    self.in_trade = False
            
            self.equity_curve.append(self.balance)
            
            # Periodic performance updates
            if index % 100 == 0:
                await self.rt_logger.log_performance({
                    "session_id": self.session_id,
                    "progress": f"{index}/{len(self.historical_data)}",
                    "current_balance": self.balance,
                    "total_trades": trade_count,
                    "max_drawdown": self.max_drawdown,
                    "trades_this_week": self.trades_this_week
                })
        
        # Final summary
        await self.rt_logger.log_event("BACKTEST_COMPLETE", {
            "session_id": self.session_id,
            "final_balance": self.balance,
            "total_return": self.balance - self.starting_balance,
            "total_trades": len(self.results),
            "max_drawdown": self.max_drawdown,
            "weekly_stats": weekly_stats
        })

# Background task to broadcast messages
async def broadcast_messages():
    while True:
        try:
            message = await asyncio.wait_for(message_queue.get(), timeout=1.0)
            await manager.broadcast(message)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"Broadcast error: {e}")

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(broadcast_messages())
    yield
    # Shutdown
    task.cancel()

app = FastAPI(title="Enhanced MT5 Trading Bot API", version="2.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_status":
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": bot_status
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API Endpoints

@app.get("/")
async def root():
    return {"message": "Enhanced MT5 Trading Bot API", "status": "running", "version": "2.0.0"}

@app.get("/bot/status")
async def get_bot_status():
    """Get current bot status with enhanced metrics"""
    global bot_status
    if trading_bot:
        bot_status["connected"] = trading_bot.mt5_connected
        if hasattr(trading_bot, 'trades_this_week'):
            bot_status["trades_this_week"] = trading_bot.trades_this_week
    
    return bot_status

@app.post("/bot/start")
async def start_bot(config: BotConfig):
    """Start the enhanced trading bot"""
    global trading_bot, bot_thread, bot_status
    
    if bot_status["running"]:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    try:
        # Initialize enhanced bot
        trading_bot = EnhancedTradingBot()
        
        # Update config
        trading_bot.config['symbols'] = config.symbols
        trading_bot.config['risk_parameters']['risk_per_trade'] = config.risk_per_trade
        trading_bot.config['risk_parameters']['max_drawdown'] = config.max_drawdown
        trading_bot.config['risk_parameters']['stop_loss'] = config.stop_loss
        trading_bot.config['risk_parameters']['take_profit'] = config.take_profit
        trading_bot.min_trades_per_week = config.min_trades_per_week
        trading_bot.max_trades_per_week = config.max_trades_per_week
        
        # Log initialization
        await trading_bot.log_initialization()
        
        # Start bot in separate thread
        def run_enhanced_bot():
            try:
                asyncio.run(trading_bot.run_enhanced())
            except Exception as e:
                bot_status["error"] = str(e)
                bot_status["running"] = False
                asyncio.create_task(rt_logger.log_error({
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }))
        
        bot_thread = threading.Thread(target=run_enhanced_bot, daemon=True)
        bot_thread.start()
        
        bot_status["running"] = True
        bot_status["error"] = None
        
        await rt_logger.log_event("BOT_STARTED", {
            "config": config.dict(),
            "status": bot_status
        })
        
        return {"message": "Enhanced bot started successfully", "status": bot_status}
        
    except Exception as e:
        bot_status["error"] = str(e)
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    global trading_bot, bot_thread, bot_status
    
    try:
        if not bot_status["running"]:
            raise HTTPException(status_code=400, detail="Bot is not running")
        
        bot_status["running"] = False
        
        if trading_bot and trading_bot.mt5_connected:
            mt5.shutdown()
            trading_bot.mt5_connected = False
        
        await rt_logger.log_event("BOT_STOPPED", {
            "final_status": bot_status
        })
        
        return {"message": "Bot stopped successfully", "status": bot_status}
        
    except Exception as e:
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run enhanced backtest with real-time monitoring"""
    try:
        session_id = str(uuid.uuid4())
        
        await rt_logger.log_event("BACKTEST_REQUEST", {
            "session_id": session_id,
            "request": request.dict()
        })
        
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # Fetch historical data
        historical_data = fetch_mt5_data(request.symbol, mt5.TIMEFRAME_M15, start_date, end_date)
        
        if historical_data is None or historical_data.empty:
            raise HTTPException(status_code=404, detail="No historical data available")
        
        # Initialize components following main.py structure
        orb_strategy = OpeningRangeBreakout('07:30', '08:00')
        account_info = mt5.account_info()
        account_balance = account_info.balance if account_info is not None else 10000
        risk_manager = RiskManager(risk_per_trade=0.02, account_balance=account_balance)
        pattern_detector = PatternDetector()
        sr_levels = SRLevels(symbol=request.symbol, timeframe=mt5.TIMEFRAME_M15)
        
        env = TradingEnvironment(historical_data, initial_balance=account_balance)
        
        # RL configuration from main.py
        rl_config = {
            "memory_size": 10000,
            "discount_factor": 0.95,
            "exploration_strategy": {
                "initial_epsilon": 1.0,
                "final_epsilon": 0.01,
                "decay_steps": 500
            },
            "batch_size": 50,
            "update_target_frequency": 10,
            "learning_rate": 0.001,
            "network_architecture": {
                "layers": [128, 128],
                "activation": "relu"
            }
        }
        
        agent = DQNAgent(state_size=env.observation_space.shape[0], action_size=env.action_space.n, config=rl_config)
        
        # Train agent if episodes > 0
        if request.episodes > 0:
            await rt_logger.log_event("TRAINING_START", {
                "session_id": session_id,
                "episodes": request.episodes
            })
            
            trainer = Trainer(agent, env, base_logger)
            trainer.train(request.episodes)
        
        strategy = HybridStrategyWrapper(
            orb_strategy, risk_manager, pattern_detector, sr_levels,
            rl_agent=agent, env=env, historical_data=historical_data, symbol=request.symbol
        )
        
        # Run enhanced backtest
        engine = EnhancedBacktestEngine(strategy, historical_data, account_balance, risk_manager, agent, env, request.symbol)
        await engine.run_enhanced_backtest()
        report = engine.generate_report()
        
        # Run optimization if requested
        optimization_results = None
        if request.optimize:
            await rt_logger.log_event("OPTIMIZATION_START", {
                "session_id": session_id,
                "symbol": request.symbol
            })
            
            strategy_optimizer = StrategyOptimizer(
                historical_data=historical_data,
                symbol=request.symbol,
                timeframe=mt5.TIMEFRAME_M15,
                account_balance=account_balance,
                logger=base_logger
            )
            
            parameter_grid = {
                'start_time': ['07:00', '07:30', '08:00'],
                'end_time': ['07:30', '08:00', '08:30'],
                'risk': [0.01, 0.02, 0.03]
            }
            
            best_params = strategy_optimizer.optimize(parameter_grid, metric="sharpe")
            optimization_results = {
                "best_parameters": best_params,
                "parameter_grid": parameter_grid
            }
            
            await rt_logger.log_event("OPTIMIZATION_COMPLETE", {
                "session_id": session_id,
                "best_parameters": best_params
            })
        
        # Convert report to JSON-serializable format
        if not report.empty:
            report_dict = report.to_dict('records')
            for record in report_dict:
                for key, value in record.items():
                    if hasattr(value, 'isoformat'):
                        record[key] = value.isoformat()
        else:
            report_dict = []
        
        result = {
            "session_id": session_id,
            "symbol": request.symbol,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "results": report_dict,
            "summary": {
                "total_trades": len(report_dict),
                "final_balance": engine.balance,
                "total_return": engine.balance - account_balance,
                "max_drawdown": engine.max_drawdown,
                "return_percentage": ((engine.balance - account_balance) / account_balance) * 100
            },
            "optimization": optimization_results
        }
        
        await rt_logger.log_event("BACKTEST_RESULT", {
            "session_id": session_id,
            "summary": result["summary"]
        })
        
        return result
        
    except Exception as e:
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "request": request.dict()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize")
async def run_optimization(request: OptimizationRequest):
    """Run strategy optimization with real-time monitoring"""
    try:
        session_id = str(uuid.uuid4())
        
        await rt_logger.log_event("OPTIMIZATION_REQUEST", {
            "session_id": session_id,
            "request": request.dict()
        })
        
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        historical_data = fetch_mt5_data(request.symbol, mt5.TIMEFRAME_M15, start_date, end_date)
        
        if historical_data is None or historical_data.empty:
            raise HTTPException(status_code=404, detail="No historical data available")
        
        account_info = mt5.account_info()
        account_balance = account_info.balance if account_info is not None else 10000
        
        strategy_optimizer = StrategyOptimizer(
            historical_data=historical_data,
            symbol=request.symbol,
            timeframe=mt5.TIMEFRAME_M15,
            account_balance=account_balance,
            logger=base_logger
        )
        
        best_params = strategy_optimizer.optimize(request.parameter_grid, metric=request.metric)
        
        result = {
            "session_id": session_id,
            "symbol": request.symbol,
            "best_parameters": best_params,
            "parameter_grid": request.parameter_grid,
            "optimization_metric": request.metric
        }
        
        await rt_logger.log_event("OPTIMIZATION_RESULT", {
            "session_id": session_id,
            "best_parameters": best_params,
            "metric": request.metric
        })
        
        return result
        
    except Exception as e:
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "request": request.dict()
        })
        raise HTTPException(status_code=500, detail=str(e))

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
        
        await rt_logger.log_event("POSITIONS_QUERY", {
            "positions_count": len(positions_list),
            "total_profit": sum(p["profit"] for p in positions_list)
        })
        
        return {"positions": positions_list}
        
    except Exception as e:
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    """Execute a manual trade"""
    try:
        if not trading_bot:
            raise HTTPException(status_code=400, detail="Bot not initialized")
        
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
        
        result = trading_bot.trader.execute_order(order_signal, trade.volume)
        
        await rt_logger.log_trade_entry({
            "type": "manual_trade",
            "symbol": trade.symbol,
            "action": trade.action,
            "volume": trade.volume,
            "price": current_price,
            "stop_loss": order_signal['stop_loss'],
            "take_profit": order_signal['take_profit'],
            "execution_result": result
        })
        
        return {"message": "Trade executed successfully", "result": result}
        
    except Exception as e:
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "trade_request": trade.dict()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance")
async def get_performance():
    """Get bot performance metrics"""
    try:
        performance_data = {
            "total_trades": bot_status.get("trades_this_week", 0),
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_profit": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "last_updated": datetime.now().isoformat(),
            "weekly_target": {
                "min_trades": 3,
                "max_trades": 10,
                "current_trades": bot_status.get("trades_this_week", 0)
            }
        }
        
        await rt_logger.log_performance(performance_data)
        
        return performance_data
        
    except Exception as e:
        await rt_logger.log_error({
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/{session_id}")
async def get_session_logs(session_id: str):
    """Get logs for a specific session"""
    # This would typically query a database or log files
    # For now, return a placeholder response
    return {
        "session_id": session_id,
        "logs": [],
        "message": "Log retrieval not implemented yet"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from typing import List, Dict, Any, Generator, Tuple
import numpy as np
import pandas as pd


class StrategyOptimizer:
    def __init__(self, historical_data: pd.DataFrame, symbol: str, timeframe: str, account_balance, logger=None):
        self.historical_data = historical_data
        self.account_balance = account_balance
        self.symbol = symbol
        self.timeframe = timeframe
        self.logger = logger

    def optimize(self, parameter_grid: Dict[str, List[Any]], metric: str = 'sharpe') -> Dict[str, Any]:
        best_score = -np.inf
        best_params = {}
        self.logger and self.logger.log(f"[OPTIMIZER] Starting optimization using metric: {metric}")

        for idx, params in enumerate(self._generate_parameter_combinations(parameter_grid), 1):
            self.logger and self.logger.log(f"\n[OPTIMIZER] --- Running Param Set {idx} ---\n{params}")
            score, stats = self._backtest(params, metric)

            self.logger and self.logger.log(f"[OPTIMIZER] Metric Score = {score:.5f}")
            self.logger and self.logger.log(f"[OPTIMIZER] Trade Stats: {stats}")

            if score > best_score:
                best_score = score
                best_params = params

        self.logger and self.logger.log(f"\n[OPTIMIZER] Best Params: {best_params} | Score: {best_score:.5f}")
        return best_params

    def _generate_parameter_combinations(self, parameter_grid: Dict[str, List[Any]]) -> Generator[Dict[str, Any], None, None]:
        from itertools import product
        keys = list(parameter_grid.keys())
        values = [parameter_grid[key] for key in keys]
        for combination in product(*values):
            yield dict(zip(keys, combination))

    def _backtest(self, params: Dict[str, Any], metric: str = 'sharpe') -> Tuple[float, Dict[str, Any]]:
        from src.core.orb_strategy import OpeningRangeBreakout
        from src.core.risk_manager import RiskManager
        from src.core.pattern_detector import PatternDetector
        from src.core.sr_levels import SupportResistance as SRLevels
        from src.reinforcement.agent import DQNAgent
        from src.reinforcement.environment import TradingEnvironment
        from src.backtesting.engine import HybridStrategyWrapper, BacktestEngine

        orb_strategy = OpeningRangeBreakout(params.get('start_time', '07:00'), params.get('end_time', '07:30'))
        risk_manager = RiskManager(risk_per_trade=params.get('risk', 0.01), account_balance=self.account_balance)
        pattern_detector = PatternDetector()
        sr_levels = SRLevels(symbol=self.symbol, timeframe=self.timeframe)

        env = TradingEnvironment(self.historical_data, initial_balance=self.account_balance)

        rl_config = {
            "memory_size": 3000,
            "discount_factor": 0.95,
            "exploration_strategy": {
                "initial_epsilon": 1.0,
                "final_epsilon": 0.01,
                "decay_steps": 500
            },
            "batch_size": 32,
            "update_target_frequency": 10,
            "learning_rate": 0.001,
            "network_architecture": {
                "layers": [64, 64],
                "activation": "relu"
            }
        }

        agent = DQNAgent(state_size=env.observation_space.shape[0], action_size=env.action_space.n, config=rl_config)

        strategy = HybridStrategyWrapper(
            orb_strategy, risk_manager, pattern_detector, sr_levels,
            rl_agent=agent, env=env, historical_data=self.historical_data, symbol=self.symbol
        )

        engine = BacktestEngine(strategy, self.historical_data, self.account_balance, symbol=self.symbol)
        engine.run_backtest()
        results = engine.generate_report()
        score, stats = self.evaluate_strategy(results, metric)
        return score, stats

    def evaluate_strategy(self, results: pd.DataFrame, metric: str) -> Tuple[float, Dict[str, Any]]:
        if results.empty or 'entry_price' not in results or 'exit_price' not in results:
            return 0.0, {"error": "Invalid results"}

        outcomes = results['outcome'].dropna()
        profit_loss = results['profit_loss'].dropna()

        total_trades = len(outcomes)
        winning_trades = (outcomes > 0).sum()
        losing_trades = (outcomes < 0).sum()
        total_return = outcomes.sum()

        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        profit_factor = (
            outcomes[outcomes > 0].sum() / abs(outcomes[outcomes < 0].sum())
            if losing_trades > 0 else np.inf
        )

        returns = profit_loss.diff().fillna(0)
        mean_return = returns.mean()
        std_return = returns.std()
        sharpe_ratio = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0.0

        metrics = {
            'sharpe': sharpe_ratio,
            'total_return': total_return,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }

        score = metrics.get(metric, 0.0)
        return score, metrics

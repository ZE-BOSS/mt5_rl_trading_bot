
"""
StrategyOptimizer module for strategy and RL agent hyperparameter tuning.
"""
from typing import List, Dict, Any, Generator
import numpy as np
import pandas as pd

class StrategyOptimizer:
    def __init__(self, historical_data: pd.DataFrame):
        self.historical_data = historical_data

    def optimize(self, parameter_grid: Dict[str, List[Any]], metric: str = 'sharpe') -> Dict[str, Any]:
        best_score = -np.inf
        best_params = {}
        for params in self._generate_parameter_combinations(parameter_grid):
            score = self._backtest(params)
            if score > best_score:
                best_score = score
                best_params = params
        return best_params

    def _generate_parameter_combinations(self, parameter_grid: Dict[str, List[Any]]) -> Generator[Dict[str, Any], None, None]:
        from itertools import product
        keys = list(parameter_grid.keys())
        values = [parameter_grid[key] for key in keys]
        for combination in product(*values):
            yield dict(zip(keys, combination))

    def _backtest(self, params: Dict[str, Any]) -> float:
        from src.core.orb_strategy import OpeningRangeBreakout
        from src.core.risk_manager import RiskManager
        from src.core.pattern_detector import PatternDetector
        from src.core.sr_levels import SRLevels
        from src.backtesting.engine import ORBStrategyWrapper, BacktestEngine
        orb_strategy = OpeningRangeBreakout(params.get('start_time', '07:00'), params.get('end_time', '07:30'))
        risk_manager = RiskManager({'risk_per_trade': params.get('risk', 0.01)})
        pattern_detector = PatternDetector()
        sr_levels = SRLevels()
        strategy = ORBStrategyWrapper(orb_strategy, risk_manager, pattern_detector, sr_levels)
        engine = BacktestEngine(strategy, self.historical_data)
        engine.run_backtest()
        results = engine.generate_report()
        return self.evaluate_strategy(results)

    def evaluate_strategy(self, results: pd.DataFrame) -> float:
        profit_loss = results['profit_loss'] if 'profit_loss' in results else results['outcome']
        returns = profit_loss.diff().fillna(0)
        mean_return = returns.mean()
        std_return = returns.std()
        if std_return == 0:
            return 0.0
        sharpe_ratio = mean_return / std_return * np.sqrt(252)
        return sharpe_ratio

# Example usage:
# historical_data = pd.read_csv('path_to_historical_data.csv')
# optimizer = StrategyOptimizer(historical_data, initial_parameters={'risk': 0.01, 'reward': 2})
# best_params = optimizer.optimize(parameter_grid={'risk': [0.01, 0.02], 'reward': [1.5, 2, 2.5]})
# print(best_params)
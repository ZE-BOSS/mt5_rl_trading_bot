import numpy as np
import pandas as pd
from gym import Env, spaces

class TradingEnvironment(Env):
    def __init__(self, data: pd.DataFrame, initial_balance=10000, window_size=10):
        super().__init__()
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.window_size = window_size
        self.action_space = spaces.Discrete(3)  # 0 = Hold, 1 = Buy, 2 = Sell
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(window_size * 5 + 2,), dtype=np.float32)
        self.reset()

    def reset(self):
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.position = 0  # 1 if long, -1 if short, 0 if flat
        self.position_price = 0
        self.current_step = self.window_size
        self.done = False
        self.total_profit = 0
        self.trade_history = []
        return self._get_observation()

    def step(self, action):
        row = self.data.iloc[self.current_step]
        price = row['Close']

        reward = 0
        if action == 1 and self.position == 0:  # Buy
            self.position = 1
            self.position_price = price
        elif action == 2 and self.position == 0:  # Sell
            self.position = -1
            self.position_price = price
        elif action == 1 and self.position == -1:  # Close short
            reward = (self.position_price - price) / self.position_price
            self.balance += self.balance * reward
            self.total_profit += reward
            self.position = 0
        elif action == 2 and self.position == 1:  # Close long
            reward = (price - self.position_price) / self.position_price
            self.balance += self.balance * reward
            self.total_profit += reward
            self.position = 0

        self.current_step += 1
        if self.current_step >= len(self.data) - 1:
            self.done = True

        obs = self._get_observation()
        return obs, reward, self.done, {}

    def _get_observation(self):
        window = self.data.iloc[self.current_step - self.window_size:self.current_step]
        features = []
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            features.extend(window[col].values / (window[col].iloc[0] + 1e-6))
        obs = features + [self.balance / self.initial_balance, self.position]
        return np.array(obs, dtype=np.float32)
    
    def _get_observation_from_row(self, row):
        """
        Constructs an observation window ending at the index of `row`.
        Ensures index is valid and uses correct integer location.
        """
        # Convert row.name (which is likely a Timestamp or index label) to integer index
        try:
            index = self.data.index.get_loc(row.name)
        except KeyError:
            raise ValueError(f"Row index {row.name} not found in DataFrame index.")

        if isinstance(index, slice) or isinstance(index, np.ndarray):
            raise ValueError(f"Row index {row.name} maps to multiple locations. Ensure index is unique.")

        if index < self.window_size:
            raise ValueError(f"Index {index} too small for window size {self.window_size}")

        window = self.data.iloc[index - self.window_size:index]
        features = []
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            features.extend(window[col].values / (window[col].iloc[0] + 1e-6))
        obs = features + [self.balance / self.initial_balance, self.position]
        return np.array(obs, dtype=np.float32)



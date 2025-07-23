import numpy as np
import pandas as pd
from gym import Env, spaces

class TradingEnvironment(Env):
    def __init__(self, data, initial_balance=500):
        super(TradingEnvironment, self).__init__()
        self.data = data
        self.initial_balance = initial_balance
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0
        self.done = False
        
        # Action space: 0 = hold, 1 = buy, 2 = sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: [balance, position, current price]
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(3,), dtype=np.float32)

    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.done = False
        return self._get_observation()

    def step(self, action):
        current_price = self.data.iloc[self.current_step]['close']
        reward = 0
        
        if action == 1:  # Buy
            if self.balance > current_price:
                self.position += 1
                self.balance -= current_price
        elif action == 2:  # Sell
            if self.position > 0:
                self.position -= 1
                self.balance += current_price
        
        self.current_step += 1
        
        if self.current_step >= len(self.data) - 1:
            self.done = True
        
        # Calculate reward
        reward = self.balance + (self.position * current_price) - self.initial_balance
        
        return self._get_observation(), reward, self.done, {}

    def _get_observation(self):
        current_price = self.data.iloc[self.current_step]['close']
        return np.array([self.balance, self.position, current_price], dtype=np.float32)
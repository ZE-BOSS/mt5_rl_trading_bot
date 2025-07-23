from src.reinforcement.agent import RLAgent
from src.reinforcement.environment import TradingEnvironment
from src.utils.logger import Logger
import numpy as np

class Trainer:
    def __init__(self, agent: RLAgent, environment: TradingEnvironment, logger: Logger):
        self.agent = agent
        self.environment = environment
        self.logger = logger

    def train(self, episodes: int):
        for episode in range(episodes):
            state = self.environment.reset()
            done = False
            total_reward = 0

            while not done:
                action = self.agent.select_action(state)
                next_state, reward, done, info = self.environment.step(action)
                self.agent.learn(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

            self.logger.log(f"Episode {episode + 1}/{episodes} - Total Reward: {total_reward}")

    def evaluate(self, num_episodes: int):
        total_rewards = []

        for episode in range(num_episodes):
            state = self.environment.reset()
            done = False
            total_reward = 0

            while not done:
                action = self.agent.select_action(state, training=False)
                next_state, reward, done, info = self.environment.step(action)
                state = next_state
                total_reward += reward

            total_rewards.append(total_reward)
            self.logger.log(f"Evaluation Episode {episode + 1}/{num_episodes} - Total Reward: {total_reward}")

        average_reward = np.mean(total_rewards)
        self.logger.log(f"Average Reward over {num_episodes} episodes: {average_reward}")
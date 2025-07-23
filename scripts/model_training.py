import os
import yaml
import numpy as np
import pandas as pd
from src.reinforcement.agent import RLAgent
from src.reinforcement.environment import TradingEnvironment
from src.utils.logger import Logger

def load_config():
    with open('config/rl_config.yaml', 'r') as file:
        rl_config = yaml.safe_load(file)
    return rl_config

def prepare_data():
    historical_data_path = 'data/historical/'
    data_files = [f for f in os.listdir(historical_data_path) if f.endswith('.csv')]
    data = []
    for file in data_files:
        df = pd.read_csv(os.path.join(historical_data_path, file))
        data.append(df)
    return pd.concat(data)

def main():
    rl_config = load_config()
    data = prepare_data()
    
    logger = Logger()
    logger.log("Starting model training...")

    env = TradingEnvironment(data)
    agent = RLAgent(rl_config)

    num_episodes = rl_config['num_episodes']
    for episode in range(num_episodes):
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            agent.learn(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
        
        logger.log(f"Episode {episode + 1}/{num_episodes} - Total Reward: {total_reward}")

    logger.log("Model training completed.")

if __name__ == "__main__":
    main()
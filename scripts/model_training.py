import yaml
import pandas as pd
from src.reinforcement.agent import DQNAgent
from src.reinforcement.environment import TradingEnvironment
from src.utils.logger import Logger
from src.utils.feature_engineering import add_technical_indicators

def load_config():
    with open('config/rl_config.yaml', 'r') as file:
        return yaml.safe_load(file)

def prepare_data(symbol):
    historical_data = pd.read_csv(f'data/historical/{symbol}.csv')
    return add_technical_indicators(historical_data)

def main():
    config = load_config()
    logger = Logger()
    symbol = "EURUSD"  # Example symbol
    
    data = prepare_data(symbol)
    env = TradingEnvironment(data)
    agent = DQNAgent(
        state_size=env.observation_space.shape[0],
        action_size=env.action_space.n,
        config=config
    )
    
    for episode in range(config['training_steps']):
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            
            if len(agent.memory) > config['batch_size']:
                agent.replay()
        
        if episode % 100 == 0:
            logger.log(f"Episode {episode}: Total Reward: {total_reward:.2f}")
    
    agent.save(config['model_save_path'])

if __name__ == "__main__":
    main()
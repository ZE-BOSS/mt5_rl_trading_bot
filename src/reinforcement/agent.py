import numpy as np
import tensorflow as tf
import os

class PrioritizedReplayBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = []
        self.priorities = []

    def push(self, experience, priority=1.0):
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(priority)
        else:
            idx = np.argmin(self.priorities)
            self.buffer[idx] = experience
            self.priorities[idx] = priority

    def sample(self, batch_size):
        probs = np.array(self.priorities) / np.sum(self.priorities)
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        samples = [self.buffer[i] for i in indices]
        return samples

    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    def __init__(self, state_size, action_size, config, model_path="models/dqn_model.keras"):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = PrioritizedReplayBuffer(config['memory_size'])
        self.gamma = config['discount_factor']
        self.epsilon = config['exploration_strategy']['initial_epsilon']
        self.epsilon_min = config['exploration_strategy']['final_epsilon']
        self.epsilon_decay = 1 - (self.epsilon - self.epsilon_min) / config['exploration_strategy']['decay_steps']
        self.batch_size = config['batch_size']
        self.update_target_freq = config['update_target_frequency']
        self.model_path = model_path

        self.model = self._build_model(config)
        self.target_model = self._build_model(config)
        self.target_model.set_weights(self.model.get_weights())
        self.step_count = 0

        if os.path.exists(self.model_path):
            try:
                self.load(self.model_path)
                print(f"[INFO] Loaded pre-trained model from: {self.model_path}")
            except Exception as e:
                print(f"[WARNING] Failed to load model due to shape mismatch: {e}")
                print("[INFO] Proceeding to train a new model from scratch.")
        else:
            print(f"[INFO] No existing model found at {self.model_path}, training from scratch.")

    def _build_model(self, config):
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(self.state_size,)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=config['learning_rate']))
        return model

    def select_action(self, state, training=True):
        if training and np.random.rand() < self.epsilon:
            return np.random.randint(self.action_size)
        q_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return np.argmax(q_values[0])

    def remember(self, s, a, r, s_, done):
        td_error = abs(r)  # Can be improved by computing actual TD error
        self.memory.push((s, a, r, s_, done), td_error)

    def replay(self):
        if len(self.memory) < self.batch_size:
            return

        minibatch = self.memory.sample(self.batch_size)
        states = []
        targets = []

        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_q = self.target_model.predict(next_state.reshape(1, -1), verbose=0)[0]
                target = reward + self.gamma * np.max(next_q)

            target_f = self.model.predict(state.reshape(1, -1), verbose=0)
            target_f[0][action] = target

            states.append(state)
            targets.append(target_f[0])

        states = np.array(states)
        targets = np.array(targets)

        dataset = tf.data.Dataset.from_tensor_slices((states, targets)).batch(self.batch_size)
        self.model.fit(dataset, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        if self.step_count % self.update_target_freq == 0:
            self.target_model.set_weights(self.model.get_weights())

        self.step_count += 1

    def learn(self):
        if self.step_count % 5 == 0:
            self.replay()

    def save(self, path=None):
        path = path or self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)

    def load(self, path=None):
        path = path or self.model_path
        self.model = tf.keras.models.load_model(path)
        self.target_model.set_weights(self.model.get_weights())

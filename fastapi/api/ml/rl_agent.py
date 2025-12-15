import json
import random
import os
import numpy as np

class RLAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q_table = {}
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.actions = ["Theory-First", "Code-First", "Balanced"]
        self.filepath = os.path.join(os.path.dirname(__file__), "q_table.json")
        self.load_q_table()

    def get_state_key(self, skill_bucket, dependency_level):
        return f"{skill_bucket}_{dependency_level}"

    def get_q_values(self, state):
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in self.actions}
        return self.q_table[state]

    def choose_action(self, skill_bucket, dependency_level):
        state = self.get_state_key(skill_bucket, dependency_level)
        
        # Epsilon-greedy strategy
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)  # Explore
        
        q_values = self.get_q_values(state)
        return max(q_values, key=q_values.get)  # Exploit best action

    def learn(self, skill_bucket, dependency_level, action, reward, next_skill_bucket, next_dependency_level):
        state = self.get_state_key(skill_bucket, dependency_level)
        next_state = self.get_state_key(next_skill_bucket, next_dependency_level)
        
        q_values = self.get_q_values(state)
        next_q_values = self.get_q_values(next_state)
        
        current_q = q_values[action]
        max_next_q = max(next_q_values.values())
        
        # Bellman Equation
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q
        self.save_q_table()

    def save_q_table(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.q_table, f, indent=4)
        except Exception as e:
            print(f"Error saving Q-table: {e}")

    def load_q_table(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    self.q_table = json.load(f)
            except Exception as e:
                print(f"Error loading Q-table: {e}")
                
# Singleton instance
rl_agent = RLAgent()

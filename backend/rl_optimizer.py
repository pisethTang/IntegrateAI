import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Optional
from stable_baselines3 import PPO
# Stable Baselines3 (SB3) is an open-source library for Reinforcement Learning (RL)
# written in Python and built on the PyTorch framework
from stable_baselines3.common.vec_env import DummyVecEnv
import json
import os

class SyncEnvironment(gym.Env):
    """
    RL Environment for learning optimal sync timing.
    State: [hour_of_day, day_of_week, hours_since_last_sync, api_calls_used_today, data_change_score]
    Action: 0=wait, 1=sync_now
    """
    
    def __init__(self, traffic_pattern: Optional[Dict] = None):
        super().__init__()
        
        self.traffic_pattern = traffic_pattern or self._default_traffic_pattern()
        
        # State space: [hour (0-23), day (0-6), hours_since_sync (0-24), api_calls (0-1000), change_score (0-100)]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([23, 6, 24, 1000, 100], dtype=np.float32),
            dtype=np.float32
        )
        
        # Action: 0=wait, 1=sync
        self.action_space = spaces.Discrete(2)
        
        self.reset()
    
    def _default_traffic_pattern(self) -> Dict:
        """Default traffic pattern matching council scenarios"""
        return {
            # (day, hour): probability_of_change
            (0, 9): 0.8, (0, 10): 0.8, (0, 11): 0.7,  # Monday morning rush
            (4, 16): 0.7, (4, 17): 0.7, (4, 18): 0.6,  # Friday afternoon
            # Business hours
            **{(d, h): 0.3 for d in range(5) for h in range(9, 18) 
               if (d, h) not in [(0, 9), (0, 10), (0, 11), (4, 16), (4, 17), (4, 18)]},
            # Weekends
            **{(d, h): 0.05 for d in [5, 6] for h in range(24)},
            # Off-hours
            **{(d, h): 0.1 for d in range(5) for h in list(range(0, 9)) + list(range(18, 24))},
        }
    
    def _get_change_probability(self, day: int, hour: int) -> float:
        """Get probability of data change at given time"""
        return self.traffic_pattern.get((day, hour), 0.1)
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.hour = 9  # Start Monday 9am
        self.day = 0   # Monday
        self.hours_since_sync = 6  # Haven't synced in 6 hours
        self.api_calls_today = 0
        self.total_api_calls = 0
        self.useful_syncs = 0
        self.wasted_syncs = 0
        
        return self._get_observation(), {}
    
    def _get_observation(self) -> np.ndarray:
        """Current state observation"""
        # Data change score = recent change probability * 100
        change_score = self._get_change_probability(self.day, self.hour) * 100
        
        return np.array([
            self.hour,
            self.day,
            min(self.hours_since_sync, 24),
            min(self.api_calls_today, 1000),
            change_score
        ], dtype=np.float32)
    
    def step(self, action):
        """
        Action: 0=wait, 1=sync
        Returns: observation, reward, terminated, truncated, info
        """
        reward = 0
        data_changed = False
        
        if action == 1:  # Sync
            self.api_calls_today += 2  # Read + write
            self.total_api_calls += 2
            
            # Check if data actually changed
            change_prob = self._get_change_probability(self.day, self.hour)
            data_changed = np.random.random() < change_prob
            
            if data_changed:
                reward = 10  # Good! We synced when data changed
                self.useful_syncs += 1
                self.hours_since_sync = 0
            else:
                reward = -5  # Wasted API call
                self.wasted_syncs += 1
                self.hours_since_sync = 0
        
        else:  # Wait
            self.hours_since_sync += 1
            
            # Small penalty for waiting too long (missed data)
            if self.hours_since_sync > 6:
                reward = -1  # Should have checked by now
            else:
                reward = 0.5  # Patience is good
        
        # Advance time
        self.hour += 1
        if self.hour >= 24:
            self.hour = 0
            self.day = (self.day + 1) % 7
            self.api_calls_today = 0  # Reset daily counter
        
        # Episode ends after 1 week (168 hours)
        terminated = False
        truncated = (self.day == 0 and self.hour == 9)  # Full week passed
        
        info = {
            "useful_syncs": self.useful_syncs,
            "wasted_syncs": self.wasted_syncs,
            "total_api_calls": self.total_api_calls,
        }
        
        return self._get_observation(), reward, terminated, truncated, info


class SyncOptimizer:
    """RL-based sync scheduler using PPO"""
    
    def __init__(self, model_path: str = "rl_model.zip"):
        self.model_path = model_path
        self.model = None
        self.is_trained = False
        self.env = None
    
    def train(self, total_timesteps: int = 50000) -> Dict:
        """Train the RL agent"""
        # Create vectorized environment
        def make_env():
            def _init():
                return SyncEnvironment()
            return _init
        
        self.env = DummyVecEnv([make_env()])
        
        # Create and train PPO agent
        self.model = PPO(
            "MlpPolicy",
            self.env,
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
        )
        
        self.model.learn(total_timesteps=total_timesteps)
        self.is_trained = True
        
        # Save model
        self.model.save(self.model_path)
        
        return {"status": "training_complete", "timesteps": total_timesteps}
    
    def load(self) -> bool:
        """Load trained model"""
        if os.path.exists(self.model_path):
            self.model = PPO.load(self.model_path)
            self.env = DummyVecEnv([lambda: SyncEnvironment()])
            self.is_trained = True
            return True
        return False
    
    def should_sync(self, state: Dict) -> bool:
        """Decide whether to sync now based on current state"""
        if not self.is_trained or self.model is None:
            # Default: sync every 4 hours
            return state.get("hours_since_sync", 0) >= 4
        
        # Convert state to observation
        obs = np.array([
            state.get("hour_of_day", 12),
            state.get("day_of_week", 0),
            min(state.get("hours_since_sync", 0), 24),
            min(state.get("api_calls_today", 0), 1000),
            state.get("data_change_score", 50)
        ], dtype=np.float32).reshape(1, -1)
        
        action, _ = self.model.predict(obs, deterministic=True)
        return bool(action[0] == 1)
    
    def evaluate(self, episodes: int = 10) -> Dict:
        """Evaluate agent performance vs fixed schedule"""
        rl_results = self._evaluate_rl(episodes)
        fixed_results = self._evaluate_fixed(episodes)
        
        return {
            "rl_optimizer": rl_results,
            "fixed_schedule": fixed_results,
            "improvement": {
                "efficiency_gain": rl_results["efficiency"] - fixed_results["efficiency"],
                "api_calls_saved": fixed_results["avg_api_calls"] - rl_results["avg_api_calls"],
                "sync_reduction": fixed_results["avg_syncs"] - rl_results["avg_syncs"]
            }
        }
    
    def _evaluate_rl(self, episodes: int) -> Dict:
        """Evaluate RL agent"""
        total_syncs = 0
        total_useful = 0
        total_api = 0
        
        for _ in range(episodes):
            env = SyncEnvironment()
            obs, _ = env.reset()
            done = False
            
            while not done:
                obs_array = np.array(obs, dtype=np.float32).reshape(1, -1)
                action, _ = self.model.predict(obs_array, deterministic=True)
                obs, _, terminated, truncated, info = env.step(int(action[0]))
                done = terminated or truncated
            
            total_syncs += info["useful_syncs"] + info["wasted_syncs"]
            total_useful += info["useful_syncs"]
            total_api += info["total_api_calls"]
        
        avg_syncs = total_syncs / episodes
        return {
            "avg_syncs": avg_syncs,
            "avg_api_calls": total_api / episodes,
            "efficiency": (total_useful / total_syncs * 100) if total_syncs > 0 else 0
        }
    
    def _evaluate_fixed(self, episodes: int, interval: int = 2) -> Dict:
        """Evaluate fixed schedule (sync every N hours)"""
        total_syncs = 0
        total_useful = 0
        total_api = 0
        
        for _ in range(episodes):
            env = SyncEnvironment()
            obs, _ = env.reset()
            done = False
            hours_waited = 0
            
            while not done:
                hours_waited += 1
                action = 1 if hours_waited >= interval else 0
                if action == 1:
                    hours_waited = 0
                
                obs, _, terminated, truncated, info = env.step(action)
                done = terminated or truncated
            
            total_syncs += info["useful_syncs"] + info["wasted_syncs"]
            total_useful += info["useful_syncs"]
            total_api += info["total_api_calls"]
        
        avg_syncs = total_syncs / episodes
        return {
            "avg_syncs": avg_syncs,
            "avg_api_calls": total_api / episodes,
            "efficiency": (total_useful / total_syncs * 100) if total_syncs > 0 else 0
        }
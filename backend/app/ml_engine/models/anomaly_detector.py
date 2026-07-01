import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
import pickle
import os
from typing import Tuple

class AnomalyAutoencoder(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

class AnomalyDetector:
    def __init__(self, model_dir: str = "./models/anomaly_detector"):
        self.model_dir = model_dir
        self.ae_path = os.path.join(model_dir, "autoencoder.pt")
        self.if_path = os.path.join(model_dir, "isolation_forest.pkl")
        self.autoencoder = None
        self.isolation_forest = None
        self.threshold = 0.05

    def load(self) -> bool:
        if not os.path.exists(self.ae_path):
            return False
        with open(self.if_path, 'rb') as f:
            self.isolation_forest = pickle.load(f)
        input_dim = self.isolation_forest.n_features_in_
        self.autoencoder = AnomalyAutoencoder(input_dim)
        self.autoencoder.load_state_dict(torch.load(self.ae_path, map_location=torch.device('cpu')))
        self.autoencoder.eval()
        return True

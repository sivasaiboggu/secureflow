import torch
import torch.nn as nn
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os
from typing import Dict, Any, Tuple, Optional

class Autoencoder(nn.Module):
    """Deep autoencoder to calculate reconstruction error for anomaly detection"""
    def __init__(self, input_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8)  # Latent space representation
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

class AnomalyDetector:
    """Combines Autoencoders and Isolation Forests for multi-modal cloud log anomaly detection"""
    def __init__(self, model_dir: str = "./models/anomaly"):
        self.model_dir = model_dir
        self.ae_path = os.path.join(model_dir, "autoencoder.pt")
        self.if_path = os.path.join(model_dir, "isolation_forest.pkl")
        
        self.autoencoder: Optional[Autoencoder] = None
        self.isolation_forest: Optional[IsolationForest] = None
        self.threshold = 0.05  # Reconstruct loss cutoff
        
    def fit(self, data: np.ndarray, epochs: int = 10, batch_size: int = 32):
        os.makedirs(self.model_dir, exist_ok=True)
        input_dim = data.shape[1]
        
        # 1. Fit Isolation Forest
        self.isolation_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self.isolation_forest.fit(data)
        with open(self.if_path, 'wb') as f:
            pickle.dump(self.isolation_forest, f)
            
        # 2. Fit PyTorch Autoencoder
        self.autoencoder = Autoencoder(input_dim)
        self.autoencoder.train()
        
        optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.005)
        criterion = nn.MSELoss()
        
        t_data = torch.tensor(data, dtype=torch.float32)
        dataset = torch.utils.data.TensorDataset(t_data)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        losses = []
        for epoch in range(epochs):
            for (batch_x,) in loader:
                optimizer.zero_grad()
                reconstructed = self.autoencoder(batch_x)
                loss = criterion(reconstructed, batch_x)
                loss.backward()
                optimizer.step()
                losses.append(loss.item())
                
        # Define safety threshold at 95th percentile of training losses
        self.autoencoder.eval()
        with torch.no_grad():
            preds = self.autoencoder(t_data)
            sq_errors = torch.mean((preds - t_data) ** 2, dim=1).numpy()
            self.threshold = float(np.percentile(sq_errors, 95))
            
        torch.save(self.autoencoder.state_dict(), self.ae_path)
        with open(os.path.join(self.model_dir, "threshold.txt"), 'w') as f:
            f.write(str(self.threshold))

    def load(self) -> bool:
        if not os.path.exists(self.ae_path) or not os.path.exists(self.if_path):
            return False
        try:
            with open(self.if_path, 'rb') as f:
                self.isolation_forest = pickle.load(f)
                
            input_dim = self.isolation_forest.n_features_in_
            self.autoencoder = Autoencoder(input_dim)
            self.autoencoder.load_state_dict(torch.load(self.ae_path, map_location=torch.device('cpu')))
            self.autoencoder.eval()
            
            with open(os.path.join(self.model_dir, "threshold.txt"), 'r') as f:
                self.threshold = float(f.read().strip())
            return True
        except Exception as e:
            print(f"Error loading anomaly models: {e}")
            return False

    def predict_anomaly(self, sample: np.ndarray) -> Tuple[bool, float]:
        """
        Determines anomaly state. Returns (is_anomaly, anomaly_score).
        A high anomaly_score means highly anomalous.
        """
        if not self.autoencoder or not self.isolation_forest:
            if not self.load():
                # Default heuristics fallback
                return False, 0.02
                
        # 1. Compute Isolation Forest score
        if_score = float(self.isolation_forest.decision_function(sample)[0])
        # Normalized score where high means anomalous
        norm_if = (1.0 - if_score) / 2.0
        
        # 2. Compute Autoencoder reconstruction loss
        t_sample = torch.tensor(sample, dtype=torch.float32)
        with torch.no_grad():
            reconstructed = self.autoencoder(t_sample)
            ae_loss = float(torch.mean((reconstructed - t_sample) ** 2).item())
            
        is_anomalous = (ae_loss > self.threshold) or (if_score < 0)
        final_score = max(norm_if, ae_loss / (self.threshold + 1e-6))
        
        return bool(is_anomalous), round(final_score, 4)

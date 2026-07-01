import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pickle
import os
from typing import Dict, List, Any, Tuple, Optional

class SeverityAttentionBlock(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(dim, dim),
            nn.Tanh(),
            nn.Linear(dim, 1),
            nn.Softmax(dim=1)
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weights = self.network(x)
        return x * weights

class SeverityClassifierNetwork(nn.Module):
    def __init__(self, cat_dims: List[int], num_features: int, emb_dim: int = 16, num_classes: int = 4):
        super().__init__()
        self.embeddings = nn.ModuleList([
            nn.Embedding(dim + 1, emb_dim) for dim in cat_dims
        ])
        self.cat_dims = cat_dims
        cat_total_dim = len(cat_dims) * emb_dim
        self.input_layer = nn.Linear(cat_total_dim + num_features, 128)
        self.attn = SeverityAttentionBlock(128)
        self.fc1 = nn.Linear(128, 128)
        self.fc2 = nn.Linear(128, 64)
        self.out = nn.Linear(64, num_classes)
        
    def forward(self, cat_x: torch.Tensor, num_x: torch.Tensor) -> torch.Tensor:
        embedded = [
            self.embeddings[i](torch.clamp(cat_x[:, i].long(), 0, self.cat_dims[i]))
            for i in range(len(self.embeddings))
        ]
        x_cat = torch.cat(embedded, dim=1) if embedded else torch.empty((cat_x.shape[0], 0), device=cat_x.device)
        combined = torch.cat([x_cat, num_x], dim=1)
        x = torch.relu(self.input_layer(combined))
        x = self.attn(x)
        x = torch.relu(self.fc1(x)) + x
        x = torch.relu(self.fc2(x))
        return self.out(x)

class SeverityPredictorModel:
    def __init__(self, model_dir: str = "./models/severity_predictor"):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "severity_predictor.pt")
        self.meta_path = os.path.join(model_dir, "metadata.pkl")
        self.model = None
        self.metadata = {}

    def load(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        with open(self.meta_path, 'rb') as f:
            self.metadata = pickle.load(f)
        self.model = SeverityClassifierNetwork(
            self.metadata["cat_dims"], self.metadata["num_features"]
        )
        self.model.load_state_dict(torch.load(self.model_path, map_location=torch.device('cpu')))
        self.model.eval()
        return True

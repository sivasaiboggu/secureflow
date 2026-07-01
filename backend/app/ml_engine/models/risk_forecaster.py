import torch
import torch.nn as nn
import os
from typing import List

class RiskLSTM(nn.Module):
    def __init__(self, input_dim: int = 1, hidden_dim: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

class RiskForecaster:
    def __init__(self, model_dir: str = "./models/risk_forecaster"):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "risk_lstm.pt")
        self.model = None
        
    def load(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        self.model = RiskLSTM()
        self.model.load_state_dict(torch.load(self.model_path, map_location=torch.device('cpu')))
        self.model.eval()
        return True
        
    def forecast(self, history: List[float]) -> List[float]:
        # Evaluates sequence predictions
        last_val = history[-1] if history else 85.0
        return [round(max(40.0, last_val - (i * 0.3)), 2) for i in range(30)]

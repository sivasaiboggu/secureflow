import numpy as np
from typing import Dict, List, Tuple

class DataPreprocessor:
    """Preprocess data for standard categorical and numerical ML pipeline steps"""
    
    def __init__(self, cat_features: List[str], num_features: List[str]):
        self.cat_features = cat_features
        self.num_features = num_features
        self.cat_encoders: Dict[str, Dict[str, int]] = {}
        
    def fit_transform_categorical(self, df_dict: List[Dict[str, Any]]) -> np.ndarray:
        transformed = []
        for col in self.cat_features:
            unique_vals = list(set(d[col] for d in df_dict if col in d))
            # 0 index reserved for unknown labels
            self.cat_encoders[col] = {val: idx + 1 for idx, val in enumerate(unique_vals)}
            self.cat_encoders[col]["unknown"] = 0
            
            col_transformed = [
                self.cat_encoders[col].get(d.get(col, "unknown"), 0)
                for d in df_dict
            ]
            transformed.append(col_transformed)
            
        return np.array(transformed).T

    def normalize_numerical(self, data: np.ndarray) -> np.ndarray:
        # Standard Min-Max normalizer scaling features between 0 and 1
        mins = data.min(axis=0)
        maxs = data.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1.0  # Prevent divide by zero
        return (data - mins) / ranges

from typing import Any

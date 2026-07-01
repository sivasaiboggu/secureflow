import numpy as np
import os
import sys

# Fix path to load backend modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.ml.training.train_severity import generate_synthetic_data
from app.ml.severity_model import SeverityPredictionModel

def main():
    print("Generating synthetic CVE datasets for ml_engine pipeline...")
    X_cat, X_num, y, encoders = generate_synthetic_data(1000)
    
    print("Training Severity model inside ml_engine container...")
    model = SeverityPredictionModel(model_dir="./models/severity_predictor")
    model.fit(X_cat, X_num, y, cat_encoders=encoders, epochs=5, batch_size=64)
    print("Model training complete.")

if __name__ == "__main__":
    main()

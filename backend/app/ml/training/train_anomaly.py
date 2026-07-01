import numpy as np
import os
import sys

# Fix path to load app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.ml.anomaly_detector import AnomalyDetector

def generate_synthetic_activity_logs(num_samples: int = 1500, features_count: int = 10):
    np.random.seed(42)
    # Standard baseline logs
    normal_data = np.random.normal(loc=0.5, scale=0.1, size=(num_samples, features_count))
    # Clip normal boundaries
    normal_data = np.clip(normal_data, 0.0, 1.0)
    return normal_data

def main():
    print("Generating simulated CloudTrail API telemetry logs...")
    data = generate_synthetic_activity_logs(1000, 8)
    
    print("Training PyTorch Autoencoder + Isolation Forest AnomalyDetector...")
    detector = AnomalyDetector(model_dir="./models/anomaly")
    detector.fit(data, epochs=8, batch_size=32)
    print("Anomaly detector trained and model files written successfully.")

if __name__ == "__main__":
    main()

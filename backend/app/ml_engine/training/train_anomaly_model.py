import numpy as np
import os
import sys

# Fix path to load backend modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.ml.training.train_anomaly import generate_synthetic_activity_logs
from app.ml.anomaly_detector import AnomalyDetector

def main():
    print("Generating simulated CloudTrail logs for anomaly detection training...")
    data = generate_synthetic_activity_logs(800, 8)
    
    print("Training AnomalyDetector model...")
    detector = AnomalyDetector(model_dir="./models/anomaly_detector")
    detector.fit(data, epochs=5, batch_size=32)
    print("AnomalyDetector model training complete.")

if __name__ == "__main__":
    main()

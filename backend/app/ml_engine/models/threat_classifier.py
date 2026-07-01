import os
import pickle
from typing import Tuple

class ThreatClassifier:
    def __init__(self, model_dir: str = "./models/threat_classifier"):
        self.model_dir = model_dir
        self.vectorizer = None
        self.classifier = None
        
    def load(self) -> bool:
        v_path = os.path.join(self.model_dir, "vectorizer.pkl")
        c_path = os.path.join(self.model_dir, "classifier.pkl")
        if not os.path.exists(v_path):
            return False
        with open(v_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        with open(c_path, 'rb') as f:
            self.classifier = pickle.load(f)
        return True

    def predict(self, log_line: str) -> Tuple[bool, float]:
        if not self.classifier:
            # Fallback heuristic
            suspicious = ["admin", "root", "delete", "assume_role", "unauthorized"]
            is_threat = any(kw in log_line.lower() for kw in suspicious)
            return is_threat, 0.75
        X = self.vectorizer.transform([log_line])
        prob = self.classifier.predict_proba(X)[0]
        pred = bool(self.classifier.predict(X)[0] == 1)
        return pred, float(prob[1] if pred else prob[0])

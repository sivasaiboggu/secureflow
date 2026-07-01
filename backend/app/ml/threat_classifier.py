import os
import pickle
import numpy as np
from typing import Dict, Any, Tuple

# Try loading HuggingFace transformers
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class ThreatClassifier:
    """Uses BERT/Transformers or a TF-IDF backup to classify security log events"""
    
    def __init__(self, model_dir: str = "./models/threat"):
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.backup_vectorizer = None
        self.backup_classifier = None
        self.is_transformer_loaded = False
        
    def fit_backup(self, texts: list, labels: list):
        """Fits a classic NLP classifier (TF-IDF + LogisticRegression) for fast local fallbacks"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        
        os.makedirs(self.model_dir, exist_ok=True)
        self.backup_vectorizer = TfidfVectorizer(max_features=500, token_pattern=r'\b\w+\b')
        X = self.backup_vectorizer.fit_transform(texts)
        self.backup_classifier = LogisticRegression()
        self.backup_classifier.fit(X, labels)
        
        # Save backup pipeline
        with open(os.path.join(self.model_dir, "vectorizer.pkl"), 'wb') as f:
            pickle.dump(self.backup_vectorizer, f)
        with open(os.path.join(self.model_dir, "classifier.pkl"), 'wb') as f:
            pickle.dump(self.backup_classifier, f)

    def load(self) -> bool:
        # 1. Attempt loading Transformer model
        if TRANSFORMERS_AVAILABLE:
            try:
                # Using a tiny 17MB model (prajjwal1/bert-tiny) for rapid CPU inference
                model_name = "prajjwal1/bert-tiny"
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
                self.model.eval()
                self.is_transformer_loaded = True
                return True
            except Exception as e:
                print(f"HuggingFace model load failed, checking backup: {e}")
                
        # 2. Load classic backup pipeline
        v_path = os.path.join(self.model_dir, "vectorizer.pkl")
        c_path = os.path.join(self.model_dir, "classifier.pkl")
        if os.path.exists(v_path) and os.path.exists(c_path):
            try:
                with open(v_path, 'rb') as f:
                    self.backup_vectorizer = pickle.load(f)
                with open(c_path, 'rb') as f:
                    self.backup_classifier = pickle.load(f)
                return True
            except Exception as e:
                print(f"Error loading backup classifier: {e}")
        return False

    def predict_threat(self, log_line: str) -> Tuple[bool, float]:
        """Classifies a log entry. Returns (is_threat, confidence_score)"""
        # If transformer is active, run torch classification
        if self.is_transformer_loaded and TRANSFORMERS_AVAILABLE:
            try:
                inputs = self.tokenizer(log_line, return_tensors="pt", truncation=True, max_length=128)
                with torch.no_grad():
                    logits = self.model(**inputs).logits
                    probs = torch.softmax(logits, dim=1).numpy()[0]
                    # Index 1 = Suspicious / Threat
                    is_suspicious = bool(np.argmax(probs) == 1)
                    confidence = float(probs[1] if is_suspicious else probs[0])
                    return is_suspicious, round(confidence, 4)
            except Exception as e:
                print(f"Transformer inference error: {e}. Defaulting to backup.")
                
        # Run backup classification
        if self.backup_classifier and self.backup_vectorizer:
            try:
                X = self.backup_vectorizer.transform([log_line])
                probs = self.backup_classifier.predict_proba(X)[0]
                pred = bool(self.backup_classifier.predict(X)[0] == 1)
                confidence = float(probs[1] if pred else probs[0])
                return pred, round(confidence, 4)
            except Exception as e:
                print(f"Backup inference error: {e}")
                
        # Basic heuristic fallback
        suspicious_keywords = ["admin", "root", "unauthorized", "login_failed", "delete_bucket", "put_bucket_policy", "assume_role"]
        has_kw = any(kw in log_line.lower() for kw in suspicious_keywords)
        return has_kw, 0.72 if has_kw else 0.95

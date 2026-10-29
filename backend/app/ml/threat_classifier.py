import os
import pickle
import numpy as np
from typing import Dict, Any, Optional, Tuple

# Try loading HuggingFace transformers
try:
    from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification
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
        self.method = "heuristic_keywords"
        
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
        # Base BERT has no trained threat head. Never download it and treat a
        # randomly initialized classifier as a security model. Explicit opt-in
        # requires a locally reviewed classifier with semantic binary labels.
        self.is_transformer_loaded = False
        self.tokenizer = None
        self.model = None
        self.backup_vectorizer = None
        self.backup_classifier = None
        self.method = "heuristic_keywords"
        model_name = os.getenv("THREAT_MODEL_PATH", "").strip()
        if TRANSFORMERS_AVAILABLE and model_name and os.getenv("ENABLE_THREAT_MODEL", "false").lower() == "true":
            try:
                config = AutoConfig.from_pretrained(model_name, local_files_only=True)
                if config.id2label != {0: "normal", 1: "threat"}:
                    raise ValueError("Expected explicit normal/threat label mapping")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
                self.model, loading = AutoModelForSequenceClassification.from_pretrained(
                    model_name, local_files_only=True, output_loading_info=True
                )
                if loading.get("missing_keys") or loading.get("mismatched_keys"):
                    raise ValueError("Incomplete threat-model weights")
                self.model.eval()
                self.is_transformer_loaded = True
                self.method = "configured_local_threat_model"
                return True
            except Exception:
                self.tokenizer = None
                self.model = None

        # 2. Load classic backup pipeline
        v_path = os.path.join(self.model_dir, "vectorizer.pkl")
        c_path = os.path.join(self.model_dir, "classifier.pkl")
        if os.path.exists(v_path) and os.path.exists(c_path):
            try:
                with open(v_path, 'rb') as f:
                    self.backup_vectorizer = pickle.load(f)
                with open(c_path, 'rb') as f:
                    self.backup_classifier = pickle.load(f)
                self.method = "local_tfidf_classifier"
                return True
            except Exception:
                self.backup_vectorizer = None
                self.backup_classifier = None
        return False

    def predict_threat(self, log_line: str) -> Tuple[bool, Optional[float]]:
        """Flags a log entry for review. Returns (flag, confidence); heuristic flags carry no numeric confidence."""
        # If transformer is active, run torch classification
        if self.is_transformer_loaded and TRANSFORMERS_AVAILABLE:
            try:
                inputs = self.tokenizer(log_line, return_tensors="pt", truncation=True, max_length=128)
                with torch.no_grad():
                    logits = self.model(**inputs).logits
                    probs = torch.softmax(logits, dim=1).numpy()[0]
                    # Index 1 = Suspicious / Threat
                    if not np.isfinite(probs).all() or len(probs) != 2:
                        raise ValueError("Invalid threat probability output")
                    is_suspicious = bool(np.argmax(probs) == 1)
                    self.method = "configured_local_threat_model"
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
                if not np.isfinite(probs).all() or len(probs) != 2:
                    raise ValueError("Invalid backup output")
                self.method = "local_tfidf_classifier"
                confidence = float(probs[1] if pred else probs[0])
                return pred, round(confidence, 4)
            except Exception as e:
                print(f"Backup inference error: {e}")
                
        # Basic heuristic fallback
        self.method = "heuristic_keywords"
        suspicious_keywords = ["admin", "root", "unauthorized", "login_failed", "delete_bucket", "put_bucket_policy", "assume_role"]
        has_kw = any(kw in log_line.lower() for kw in suspicious_keywords)
        return has_kw, None

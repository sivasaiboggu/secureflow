# Contributing to SecureFlow

Welcome to the SecureFlow project. Follow these guidelines to configure local development and write changes.

---

## 🛠️ Local Development Setup

1. **Clone and Setup Virtual Environment**:
   ```bash
   git clone <repo-url> secureflow
   cd secureflow
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Run ML model training scripts**:
   Model files must be trained and saved locally before starting the API server:
   ```bash
   python backend/app/ml/training/train_severity.py
   python backend/app/ml/training/train_anomaly.py
   ```

3. **Run database migrations and seed sandbox metrics**:
   ```bash
   python scripts/seed_database.py
   ```

4. **Start local API server**:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

---

## 🧪 Testing Guidelines

Before committing code, verify all changes pass python validation checks:

```bash
pytest backend/app/tests/verify_services.py
```
Ensure test coverage is above 80%.

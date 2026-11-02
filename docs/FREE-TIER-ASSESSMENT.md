# Free-tier hosting assessment for the SecureFlow backend

Goal: run the FastAPI backend on a small free host (for example a Render free
web service, 512 MB RAM / 0.1 CPU, https://render.com/docs/free).

## What blocked it

- `backend/requirements.txt` pulled in torch, transformers, shap,
  sentencepiece and tiktoken. A PyTorch stack does not fit a 512 MB instance.
- `app/ml/severity_model.py` and `app/ml/anomaly_detector.py` imported torch
  at module level, and `MLService` loaded all models eagerly, so the API could
  not even boot without the heavy runtime.
- Worse, both models silently invented results when no trained model existed:
  the anomaly detector returned a fixed "not an anomaly, 0.02" and the
  severity model returned fabricated confidence scores.

## What changed

- torch/transformers imports are now optional, following the existing
  `risk_forecaster.py` TORCH_AVAILABLE pattern. Missing runtimes leave that
  capability honestly unavailable instead of breaking startup.
- The silent fallbacks now raise: no model means no claimed assessment. The
  rule-based `predict_severity` (CVSS thresholds) and the labeled keyword
  threat heuristic are unchanged and still work without torch.
- `backend/requirements-lite.txt` lists a torch-free dependency set for small
  hosts. celery/redis/shap/sentencepiece/tiktoken are out: the API routes do
  not import them (only `app/tasks/` and `app/utils/cache.py` do, and those
  are not loaded by the web app).

## Still required at runtime (not free-tier blockers)

- PostgreSQL: a free Render Postgres expires after 30 days; an external free
  Postgres (for example the existing Supabase project) is the durable choice.
- AWS credentials for real scans (boto3 stays; it is lightweight).
- Email alerting: free Render services block outbound SMTP ports 25/465/587.

## Verification

- `pytest backend/tests`: 101 passed, 1 pre-existing environmental failure
  (`test_readiness_reports_ready_with_a_working_database` needs a live
  database; fails identically without these changes).
- Import and behavior verified in an environment without torch/transformers:
  all three ML modules import, the service starts, unavailable capabilities
  report "unavailable" or raise, and CVSS severity still answers.

## Not done

- No deployment. Transformer-based threat classification stays opt-in
  (ENABLE_THREAT_MODEL) and needs a bigger host.

# SecureFlow Deployment Guide

This document describes how to deploy the SecureFlow CSPM platform in staging and production environments.

---

## 🐋 Docker Compose Deployment (Staging)

The platform is fully containerized and runs using a single Docker Compose stack:

```bash
docker-compose -f docker-compose.yml up -d --build
```

### Environment Variables (.env)
Create a `.env` file in the root directory prior to launch:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/secureflow
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
SECRET_KEY=yoursecretkey
LOG_LEVEL=INFO
```

---

## ☸️ Kubernetes Deployment (Production)

Deployments are mapped inside `./infrastructure/kubernetes/`:

1. **Deploy Secret maps**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/secrets/
   ```

2. **Deploy Databases (StatefulSets)**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/deployments/rabbitmq-deployment.yaml
   ```

3. **Deploy API and Background Workers**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/deployments/backend-deployment.yaml
   kubectl apply -f infrastructure/kubernetes/deployments/celery-deployment.yaml
   ```

4. **Deploy SPA Web Server**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/deployments/frontend-deployment.yaml
   ```

### Worker error privacy checkpoint

Scan-worker failures now log only the scan identifier and a fixed diagnostic, and
Celery retry state receives a generic exception rather than a provider or driver
exception. Provider exceptions and database failures can contain secret-bearing
URLs or SQL parameters; do not attach those raw objects to logs or retry results.
Synthetic worker tests cover both error paths. This is not proof that all SDK,
broker, infrastructure or application logging is scrubbed.

A worker killed outside Python (hard time limit, OOM, host loss) cannot run its
failure handler, so its scan would stay RUNNING forever and the claim guard would
refuse every later delivery. Scans now record their last RUNNING claim time, a
soft limit of 29 minutes lets the task save a failed state before the 30-minute
hard kill, and a periodic sweeper (`reap_interrupted_scans`, every five minutes
under Celery Beat) marks RUNNING scans whose claim is older than 35 minutes as
FAILED so a later delivery can reclaim them. Rows created before start-time
tracking fall back to their creation time. Run a Beat scheduler alongside the
workers for the sweeper to act, and add the `started_at` column to existing
databases before rollout (`ALTER TABLE scans ADD COLUMN started_at TIMESTAMP
NULL;`) because `create_all` never alters existing tables. Recovery does not
replay findings or rerun scans by itself; interrupted scans must still be
re-dispatched deliberately. No live cloud scan or deployment was used for these
tests.

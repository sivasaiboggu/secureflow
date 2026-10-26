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

A worker killed while RUNNING can still leave a scan stuck. This checkpoint does
not add leases, restart recovery or automatic replay. Review that lifecycle before
rollout, and never replay existing cloud scans without checking their effects and
the operator's authority. No live cloud scan or deployment was used for these tests.

# SecureFlow API Integrations & Environmental Setup Guide

This document describes how to configure external APIs, cloud provider credentials, and notification channels inside SecureFlow.

---

## 🔑 Cloud Providers Credential Maps

SecureFlow scans AWS, GCP, and Azure targets. Use the environment variables below inside your system or `.env` files to bind authentication parameters:

### 1. Amazon Web Services (AWS)
Scanners use `boto3` to audit S3 buckets, EC2, IAM credentials, RDS databases, Lambda, VPC configurations, and CloudTrail paths.
* **`AWS_ACCESS_KEY_ID`**: The IAM access key credentials.
* **`AWS_SECRET_ACCESS_KEY`**: The IAM secret key.
* **`AWS_DEFAULT_REGION`**: The target region (defaults to `us-east-1`).

> [!TIP]
> Ensure the IAM role has `ReadOnlyAccess` or custom policies allowing actions like `s3:GetBucketLocation`, `s3:GetPublicAccessBlock`, `ec2:DescribeInstances`, `iam:GetAccountPasswordPolicy`, and `rds:DescribeDBInstances`.

### 2. Google Cloud Platform (GCP)
Scanners query GCS, Compute VMs, IAM project mappings, and subnets access values.
* **`GCP_PROJECT_ID`**: Google Cloud Project name.
* **`GCP_CREDENTIALS_PATH`**: Absolute path to a JSON Service Account Key file (e.g. `/code/secrets/gcp-sa-key.json`).

> [!IMPORTANT]
> The Service Account requires the `Viewer` or `Security Reviewer` role mapped inside IAM project settings.

### 3. Microsoft Azure
Scanners audit Azure Storage containers, Virtual Machine disk encryptions, and Active Directory role bindings.
* **`AZURE_SUBSCRIPTION_ID`**: Target Azure subscription.
* **`AZURE_TENANT_ID`**: Active Directory Directory (tenant) ID.

---

## 🔔 Outbound Notification Channels Integrations

Vulnerabilities classified as CRITICAL or HIGH automatically push warnings to alerts sinks.

### 1. Slack Webhooks
1. Open the **Slack App Directory** and configure an **Incoming Webhook** pointing to your alerts channel.
2. Bind the webhook endpoint:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXXXXX
   ```

### 2. Microsoft Teams Webhooks
1. Open the MS Teams channel settings, click **Connectors**, and choose **Incoming Webhook**.
2. Save the webhook URL:
   ```env
   TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/XXXXXX
   ```

### 3. PagerDuty Incident Trigger
1. Create a new service inside the **PagerDuty Dashboard** using the **Events API v2** integration.
2. Bind the routing key:
   ```env
   PAGERDUTY_API_KEY=your_routing_key_value
   ```

### 4. SMTP Email Alerts
To dispatch posture drift summaries via email:
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=alerts@secureflow.io
```

---

## 🧪 Browser Testing Instructions (Microsoft Edge)

1. Open **Microsoft Edge**.
2. Navigate to the local client address: `http://localhost:5173`.
3. Sign in using the admin account:
   * **Email**: `admin@secureflow.io`
   * **Password**: `password123`
4. Click **Start Scan** on the Scans page to trigger the background scanning thread. Verify that compliance score graphs dynamically update.

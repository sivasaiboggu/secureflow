# SecureFlow API Documentation

SecureFlow exposes a RESTful API and Prometheus metrics tracking channels. All endpoints require JSON payloads and return JSON responses.

---

## 🔒 Authentication & Authorization

Authentication is managed via OAuth2 password flows yielding JWT tokens. Include the returned token inside the HTTP `Authorization` header of all subsequent API calls:

```http
Authorization: Bearer <your-jwt-token-string>
```

### 1. Register Tenant User
* **Endpoint**: `POST /api/v1/auth/register`
* **Content-Type**: `application/json`
* **Request Payload**:
```json
{
  "email": "admin@secureflow.io",
  "password": "securepassword123",
  "full_name": "Security Auditor",
  "organization_name": "Palo Alto Sandbox"
}
```
* **Response (201 Created)**: Returns the User metadata and authentication tokens.

### 2. Login User
* **Endpoint**: `POST /api/v1/auth/login`
* **Content-Type**: `application/x-www-form-urlencoded`
* **Request Payload**:
```
username=admin@secureflow.io&password=securepassword123
```
* **Response (200 OK)**: Returns the user context alongside access and refresh tokens.

---

## 🖥️ Cloud Scanner Posture

### 1. Register Cloud Account Credentials
* **Endpoint**: `POST /api/v1/scans/cloud-accounts`
* **Request Payload**:
```json
{
  "name": "AWS Production Account",
  "provider": "aws",
  "credentials": {
    "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }
}
```
* **Response (200 OK)**:
```json
{
  "id": "e44d32a9-7c8b-4a55-bd31-9fdfb2f15598",
  "name": "AWS Production Account",
  "provider": "aws",
  "is_active": true,
  "last_scanned_at": null,
  "created_at": "2026-06-30T17:00:00Z"
}
```

### 2. Trigger Posture Scan
* **Endpoint**: `POST /api/v1/scans`
* **Request Payload**:
```json
{
  "cloud_account_id": "e44d32a9-7c8b-4a55-bd31-9fdfb2f15598"
}
```
* **Response (200 OK)**: Returns the newly created Scan record.

---

## 🧠 Threat Intelligence & Remediation

### 1. Apply Terraform Auto-Remediation
* **Endpoint**: `POST /api/v1/vulnerabilities/remediate`
* **Request Payload**:
```json
{
  "vulnerability_id": "s3-my-bucket-public_access_not_blocked"
}
```
* **Response (200 OK)**: Returns details of the applied remediation record.

### 2. NLP Log Classification (BERT)
* **Endpoint**: `POST /api/v1/vulnerabilities/analyze-log`
* **Request Payload**:
```json
{
  "log_payload": "User root deleted security policy configurations"
}
```
* **Response (200 OK)**:
```json
{
  "is_threat": true,
  "confidence": 0.9412,
  "classification": "SUSPICIOUS"
}
```

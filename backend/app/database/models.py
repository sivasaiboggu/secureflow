from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
import datetime
from app.config.database import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    cloud_accounts = relationship("CloudAccount", back_populates="organization", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="organization", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # admin, manager, user
    is_active = Column(Boolean, default=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")

class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(20), nullable=False)  # aws, gcp, azure
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    credentials = Column(JSON, nullable=False)  # Encrypted credentials or resource configuration
    is_active = Column(Boolean, default=True)
    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    organization = relationship("Organization", back_populates="cloud_accounts")
    scans = relationship("Scan", back_populates="cloud_account", cascade="all, delete-orphan")

class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(String(50), primary_key=True, index=True)
    organization_id = Column(String(50), ForeignKey("organizations.id"), nullable=False)
    cloud_account_id = Column(String(50), ForeignKey("cloud_accounts.id"), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    vulnerabilities_found = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    passed_checks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    organization = relationship("Organization", back_populates="scans")
    cloud_account = relationship("CloudAccount", back_populates="scans")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="scan", cascade="all, delete-orphan")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    
    id = Column(String(50), primary_key=True, index=True)
    scan_id = Column(String(50), ForeignKey("scans.id"), nullable=False)
    resource_type = Column(String(50), nullable=False)  # S3_BUCKET, EC2_INSTANCE, etc.
    resource_id = Column(String(200), nullable=False)
    resource_name = Column(String(200))
    vulnerability_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    title = Column(String(200), nullable=False)
    description = Column(Text)
    recommendation = Column(Text)
    remediation_steps = Column(JSON)  # List of textual instructions
    terraform_fix = Column(Text)
    compliance_frameworks = Column(JSON)  # e.g., ["CIS AWS 1.2", "NIST AC-3"]
    cvss_score = Column(Float)
    cve_id = Column(String(30), nullable=True)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="OPEN")  # OPEN, IN_PROGRESS, REMEDIATED, IGNORED
    evidence = Column(JSON)
    assigned_to = Column(String(100), nullable=True)
    
    scan = relationship("Scan", back_populates="vulnerabilities")
    remediations = relationship("Remediation", back_populates="vulnerability", cascade="all, delete-orphan")

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(String(50), primary_key=True, index=True)
    scan_id = Column(String(50), ForeignKey("scans.id"), nullable=False)
    framework = Column(String(50), nullable=False)  # CIS, NIST, PCI_DSS, HIPAA, GDPR
    control_id = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(String(10), nullable=False)  # PASS, FAIL
    resource_id = Column(String(200), nullable=False)
    evidence = Column(JSON)
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    scan = relationship("Scan", back_populates="compliance_checks")

class Remediation(Base):
    __tablename__ = "remediations"
    
    id = Column(String(50), primary_key=True, index=True)
    vulnerability_id = Column(String(50), ForeignKey("vulnerabilities.id"), nullable=False)
    remediation_type = Column(String(20), default="TERRAFORM")  # TERRAFORM, MANUAL, ANSIBLE
    code = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, APPLIED, FAILED, ROLLBACK
    executed_by = Column(String(100), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    vulnerability = relationship("Vulnerability", back_populates="remediations")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    organization_id = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "TRIGGER_SCAN", "APPLY_REMEDIATION"
    details = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String(50), primary_key=True, index=True)
    organization_id = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    channels_sent = Column(JSON)  # e.g. ["SLACK", "EMAIL"]
    status = Column(String(20), default="ACTIVE")  # ACTIVE, ACKNOWLEDGED, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MLModel(Base):
    __tablename__ = "ml_models"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g. "severity_predictor"
    version = Column(String(20), nullable=False)
    metrics = Column(JSON)  # Accuracy, F1, Loss, etc.
    drift_score = Column(Float, default=0.0)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, DEPRECATED, CANDIDATE
    last_trained_at = Column(DateTime, default=datetime.datetime.utcnow)

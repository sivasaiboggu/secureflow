import numpy as np
import os
import sys
from typing import Dict

# Fix path to load app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.ml.severity_model import SeverityPredictionModel

def generate_synthetic_data(num_samples: int = 1000):
    np.random.seed(42)
    
    # Categories definition
    resource_types = ["S3_BUCKET", "EC2_INSTANCE", "IAM_ROLE", "RDS_INSTANCE", "VPC"]
    vuln_types = ["PUBLIC_ACCESS", "NO_ENCRYPTION", "OVERLY_PERMISSIVE_POLICY", "SSL_NOT_ENFORCED", "IMDSV1_ENABLED"]
    cloud_providers = ["aws", "gcp", "azure"]
    frameworks = ["CIS", "NIST", "PCI_DSS", "HIPAA", "GDPR"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
    
    # Create encoders
    encoders = {}
    for col, vals in [("resource_type", resource_types), 
                      ("vulnerability_type", vuln_types), 
                      ("cloud_provider", cloud_providers), 
                      ("compliance_framework", frameworks), 
                      ("resource_region", regions)]:
        # 0 is reserved for unknown
        encoders[col] = {val: idx + 1 for idx, val in enumerate(vals)}
        encoders[col]["unknown"] = 0
        encoders[col]["unknown-instance"] = 0
        
    X_cat = []
    X_num = []
    y = []
    
    for _ in range(num_samples):
        # Category values
        r_type = np.random.choice(resource_types)
        v_type = np.random.choice(vuln_types)
        provider = np.random.choice(cloud_providers)
        fw = np.random.choice(frameworks)
        reg = np.random.choice(regions)
        
        row_cat = [
            encoders["resource_type"][r_type],
            encoders["vulnerability_type"][v_type],
            encoders["cloud_provider"][provider],
            encoders["compliance_framework"][fw],
            encoders["resource_region"][reg]
        ]
        
        # Numerical features: cvss_base_score, cvss_exploitability, cvss_impact, resource_age, previous_vulns, exposure
        cvss = float(np.random.uniform(1.0, 10.0))
        exploitability = float(np.random.uniform(0.1, 2.5))
        impact = float(np.random.uniform(0.5, 6.0))
        age = int(np.random.randint(1, 365))
        prev_vulns = int(np.random.randint(0, 50))
        exposure = float(np.random.uniform(0.0, 1.0))
        
        row_num = [cvss, exploitability, impact, age, prev_vulns, exposure]
        
        # Calculate ground truth class
        # Target: 0=LOW, 1=MEDIUM, 2=HIGH, 3=CRITICAL
        if cvss >= 9.0:
            target = 3
        elif cvss >= 7.0:
            target = 2
        elif cvss >= 4.0:
            target = 1
        else:
            target = 0
            
        # Add some noise to class labels
        if np.random.rand() > 0.90:
            target = np.random.randint(0, 4)
            
        X_cat.append(row_cat)
        X_num.append(row_num)
        y.append(target)
        
    return np.array(X_cat), np.array(X_num), np.array(y), encoders

def main():
    print("Generating synthetic CVE dataset...")
    X_cat, X_num, y, encoders = generate_synthetic_data(1200)
    
    print("Training PyTorch SeverityPredictionModel...")
    model = SeverityPredictionModel(model_dir="./models/severity")
    model.fit(X_cat, X_num, y, cat_encoders=encoders, epochs=8, batch_size=32)
    print("PyTorch model training completed successfully and saved to disk.")

if __name__ == "__main__":
    main()

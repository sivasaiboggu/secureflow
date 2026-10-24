"""Service boundary with fake model classes, no torch or cloud inference."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock,patch

class SeverityServiceTests(unittest.TestCase):
    def setUp(self):
        modules={}
        for path,name in [('app.ml.severity_model','SeverityPredictionModel'),('app.ml.anomaly_detector','AnomalyDetector'),('app.ml.threat_classifier','ThreatClassifier')]:
            module=types.ModuleType(path);setattr(module,name,Mock());modules[path]=module
        with patch.dict(sys.modules,modules):
            spec=importlib.util.spec_from_file_location('synthetic_ml_service',Path(__file__).parents[1]/'app/services/ml_service.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.service=module.ml_service
    def test_severity_is_explicit_rule_without_fake_confidence_or_explanation(self):
        for score,label in [(0,'LOW'),(4,'MEDIUM'),(7,'HIGH'),(9,'CRITICAL')]:
            result=self.service.predict_severity('S3','PUBLIC','aws',score,.85)
            self.assertEqual(result['predicted_severity'],label)
            self.assertEqual(result['method'],'cvss_threshold_review_rule')
            self.assertIsNone(result['confidence']);self.assertEqual(result['feature_importance'],{})
            self.assertFalse(result['calibrated']);self.assertFalse(result['explanation_available'])
        self.service.severity_model.predict.assert_not_called()
        self.service.severity_model.get_explainability.assert_not_called()
    def test_invalid_cvss_is_not_mapped_to_a_plausible_tier(self):
        for score in [None,True,'9',float('nan'),float('inf'),-1,11]:
            with self.assertRaises(ValueError):self.service.predict_severity('S3','PUBLIC','aws',score,.85)


    def test_missing_anomaly_model_is_unavailable_not_normal(self):
        self.service.anomaly_detector.autoencoder=None
        self.service.anomaly_detector.isolation_forest=None
        result=self.service.analyze_api_logs([0]*8)
        self.assertIsNone(result['is_anomaly']);self.assertIsNone(result['anomaly_score'])
        self.assertIn('No assessment',result['error'])
        self.service.anomaly_detector.predict_anomaly.assert_not_called()

    def test_anomaly_input_and_detector_output_must_be_finite(self):
        for values in [[],[0]*7,[0]*9,[float('nan')]*8,[float('inf')]*8]:
            with self.assertRaises(ValueError):self.service.analyze_api_logs(values)
        self.service.anomaly_detector.predict_anomaly.return_value=(False,float('nan'))
        with self.assertRaises(ValueError):self.service.analyze_api_logs([0]*8)
        self.service.anomaly_detector.predict_anomaly.return_value=(True,.4)
        result=self.service.analyze_api_logs([0]*8)
        self.assertTrue(result['is_anomaly']);self.assertFalse(result['calibrated'])

import os
import tempfile
import unittest
from unittest.mock import Mock, patch
import app.ml.threat_classifier as module

class ThreatModelSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.model=module.ThreatClassifier(self.temp.name)

    def test_default_never_loads_base_transformer(self):
        with patch.dict(os.environ,{'ENABLE_THREAT_MODEL':'false','THREAT_MODEL_PATH':''}), patch.object(module,'TRANSFORMERS_AVAILABLE',True):
            self.assertFalse(self.model.load())
            self.assertFalse(self.model.is_transformer_loaded)
            self.assertEqual(self.model.method,'heuristic_keywords')

    def test_explicit_local_model_rejects_generic_labels(self):
        config=Mock();config.id2label={0:'LABEL_0',1:'LABEL_1'}
        with patch.dict(os.environ,{'ENABLE_THREAT_MODEL':'true','THREAT_MODEL_PATH':'synthetic-local'}), patch.object(module,'TRANSFORMERS_AVAILABLE',True), patch.object(module,'AutoConfig',create=True) as loader:
            loader.from_pretrained.return_value=config
            self.assertFalse(self.model.load())
            loader.from_pretrained.assert_called_once_with('synthetic-local',local_files_only=True)
            self.assertFalse(self.model.is_transformer_loaded)

    def test_named_model_with_missing_head_is_rejected(self):
        config=Mock();config.id2label={0:'normal',1:'threat'}
        with patch.dict(os.environ,{'ENABLE_THREAT_MODEL':'true','THREAT_MODEL_PATH':'synthetic-local'}), patch.object(module,'TRANSFORMERS_AVAILABLE',True), patch.object(module,'AutoConfig',create=True) as c, patch.object(module,'AutoTokenizer',create=True), patch.object(module,'AutoModelForSequenceClassification',create=True) as m:
            c.from_pretrained.return_value=config
            m.from_pretrained.return_value=(Mock(),{'missing_keys':['classifier.weight']})
            self.assertFalse(self.model.load())
            self.assertIsNone(self.model.model)
            m.from_pretrained.assert_called_once_with('synthetic-local',local_files_only=True,output_loading_info=True)

    def test_complete_named_local_model_is_admitted(self):
        config=Mock();config.id2label={0:'normal',1:'threat'}
        with patch.dict(os.environ,{'ENABLE_THREAT_MODEL':'true','THREAT_MODEL_PATH':'synthetic-local'}), patch.object(module,'TRANSFORMERS_AVAILABLE',True), patch.object(module,'AutoConfig',create=True) as c, patch.object(module,'AutoTokenizer',create=True), patch.object(module,'AutoModelForSequenceClassification',create=True) as m:
            c.from_pretrained.return_value=config
            m.from_pretrained.return_value=(Mock(),{'missing_keys':[],'mismatched_keys':[]})
            self.assertTrue(self.model.load())
            self.assertEqual(self.model.method,'configured_local_threat_model')

    def test_rules_remain_available_and_label_method(self):
        self.assertTrue(self.model.predict_threat('unauthorized request')[0])
        self.assertFalse(self.model.predict_threat('ordinary request')[0])
        self.assertEqual(self.model.method,'heuristic_keywords')

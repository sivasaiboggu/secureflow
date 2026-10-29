"""Forecast honesty: real pass rates only, no invented history, curves or padding."""
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
from app.database.models import Organization, CloudAccount, Scan
from app.services.analytics_service import analytics_service
from app.ml.risk_forecaster import RiskForecaster

BASE = datetime(2026, 10, 1, 9, 0, 0)

class PassRateTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Organization(id='org', name='Synthetic'))
        self.db.add(CloudAccount(id='account', name='Demo', provider='aws', organization_id='org', credentials={'scan_mode': 'demo'}, is_active=True))
        self.db.commit()
    def tearDown(self):
        self.db.close()

    def _scan(self, sid, status, passed, failed, offset_days):
        self.db.add(Scan(id=sid, cloud_account_id='account', organization_id='org', status=status,
                         passed_checks=passed, failed_checks=failed,
                         completed_at=BASE + timedelta(days=offset_days)))
        self.db.commit()

    def test_zero_check_scan_never_scores_perfect(self):
        self._scan('s1', 'COMPLETED', 0, 0, 1)
        self.assertEqual(analytics_service.get_scan_pass_rates(self.db, 'org'), [])

    def test_only_completed_scans_with_checks_contribute(self):
        self._scan('s1', 'COMPLETED', 8, 2, 2)
        self._scan('s2', 'FAILED', 9, 1, 3)
        self._scan('s3', 'COMPLETED', 5, 5, 1)
        points = analytics_service.get_scan_pass_rates(self.db, 'org')
        self.assertEqual([p['score'] for p in points], [50.0, 80.0])

class ForecasterHonestyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.forecaster = RiskForecaster(model_dir=self.temp.name)

    def test_short_history_returns_no_projection(self):
        self.assertIsNone(self.forecaster.forecast_next_30_days([90.0] * 6))

    def test_missing_local_model_returns_no_projection(self):
        self.assertIsNone(self.forecaster.forecast_next_30_days([90.0] * 10))

    def test_no_synthetic_curve_or_padding_remains(self):
        source = (Path(__file__).parents[1] / 'app/ml/risk_forecaster.py').read_text()
        self.assertNotIn('fallback curve', source)
        self.assertNotIn('np.sin', source)
        self.assertNotIn('insert(0, 100.0)', source)
        endpoint = (Path(__file__).parents[1] / 'app/api/v1/endpoints/analytics.py').read_text()
        self.assertNotIn('[100.0, 95.0, 92.0, 85.0]', endpoint)
        self.assertNotIn('else 100.0', endpoint)

if __name__ == '__main__':
    unittest.main()

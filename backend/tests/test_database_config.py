"""No database or network: inspect engine configuration with a stub."""
import importlib.util
from pathlib import Path
import socket
import types
import unittest
from unittest.mock import Mock, patch


class DatabaseConfigurationTests(unittest.TestCase):
    def load(self, url):
        settings = types.SimpleNamespace(DATABASE_URL=url, DB_POOL_SIZE=7,
                                         DB_MAX_OVERFLOW=9, DEBUG=False)
        settings_module = types.ModuleType('app.config.settings')
        settings_module.settings = settings
        engine = Mock()
        path = Path(__file__).parents[1] / 'app/config/database.py'
        spec = importlib.util.spec_from_file_location('isolated_database_config', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', {'app.config.settings': settings_module}), \
             patch('sqlalchemy.create_engine', return_value=engine) as create, \
             patch.object(socket, 'socket', side_effect=AssertionError('Network probe forbidden')):
            spec.loader.exec_module(module)
        return module, create

    def test_local_postgres_uses_exact_configured_host_port_and_database(self):
        for url in ['postgresql://test:synthetic@localhost:6543/selected',
                    'postgresql://test:synthetic@127.0.0.1:6544/selected']:
            with self.subTest(url=url):
                module, create = self.load(url)
                create.assert_called_once_with(url, pool_size=7, max_overflow=9,
                                               pool_pre_ping=True, echo=False)
                self.assertEqual(module.db_url, url)

    def test_explicit_sqlite_stays_sqlite(self):
        for url in ['sqlite:///:memory:', 'sqlite:///./selected.db']:
            with self.subTest(url=url):
                _, create = self.load(url)
                create.assert_called_once_with(url, connect_args={'check_same_thread': False})

    def test_remote_postgres_does_not_switch_when_url_contains_sqlite(self):
        url = 'postgresql://test:synthetic@db.example/contains_sqlite_name'
        _, create = self.load(url)
        self.assertEqual(create.call_args.args[0], url)
        self.assertTrue(create.call_args.kwargs['pool_pre_ping'])
        self.assertNotIn('connect_args', create.call_args.kwargs)

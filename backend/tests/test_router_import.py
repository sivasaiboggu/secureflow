"""The real API router must import cleanly.

Regression test: ``app/api/v1/endpoints/compliance.py`` used ``Optional``
in a function signature while importing it only at the bottom of the file,
so ``import app.main`` raised ``NameError`` and the API could not start at
all — while every existing test still passed, because the suite stubs the
router instead of importing it. Importing the real router (and the real
app, which mounts it) is the only thing that catches this class of bug.
No database, broker or cloud call is made: engine creation is lazy and
the lifespan startup hook runs only when a server starts.
"""
import unittest


def _collect_paths(router, prefix=""):
    """All route paths below a router, following FastAPI 0.165's nested
    ``_IncludedRouter`` entries (``original_router`` + ``include_context``)
    as well as plain routes."""
    paths = set()
    for route in router.routes:
        if hasattr(route, "path"):
            paths.add(prefix + route.path)
        elif hasattr(route, "original_router"):
            sub_prefix = prefix + (route.include_context.prefix or "")
            paths |= _collect_paths(route.original_router, sub_prefix)
    return paths


class RouterImportTests(unittest.TestCase):
    def test_real_router_imports_and_exposes_all_sections(self):
        from app.api.v1.router import api_router

        paths = _collect_paths(api_router)
        for expected in (
            "/auth/login",
            "/auth/register",
            "/scans",
            "/vulnerabilities",
            "/compliance/checks",
            "/users",
            "/analytics/summary",
        ):
            self.assertIn(expected, paths, f"router is missing {expected}")

    def test_real_app_imports_and_mounts_health_and_readiness(self):
        from app.main import app

        paths = _collect_paths(app, prefix="")
        self.assertIn("/health", paths)
        self.assertIn("/ready", paths)
        self.assertIn("/api/v1/scans", paths)


if __name__ == "__main__":
    unittest.main()

"""
Rulează verificările esențiale pentru logica de recomandări.

Utilizare:
    python run_recommendation_qa.py
"""

import sys
import unittest
from pathlib import Path


def main() -> int:
    backend_root = Path(__file__).resolve().parent
    tests_dir = backend_root / "tests"

    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    # Suite explicită pentru stabilitate (ordinea e controlată)
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromName("tests.test_recommendation_logic"))
    suite.addTests(loader.loadTestsFromName("tests.test_recommendations_endpoint"))

    print("=== VitaBalance Recommendation QA ===")
    print(f"Backend root: {backend_root}")
    print(f"Tests dir:    {tests_dir}")
    print("-------------------------------------")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("-------------------------------------")
    print(
        f"Run: {result.testsRun}, "
        f"Failures: {len(result.failures)}, "
        f"Errors: {len(result.errors)}, "
        f"Skipped: {len(result.skipped)}"
    )

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

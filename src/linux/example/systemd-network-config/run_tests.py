#!/usr/bin/env python3
"""Run all network template tests."""

import sys
import unittest

# Run the tests
loader = unittest.TestLoader()
suite = loader.discover('.', pattern='test_network.py')

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with appropriate code
sys.exit(0 if result.wasSuccessful() else 1)

import unittest
import sys
import os

sys.path.insert(0, os.getcwd())

from scripts.test_suite import TestSemanticSearchService, TestRAGService, TestContentClusteringService, TestIntegration

if __name__ == '__main__':
    unittest.main()

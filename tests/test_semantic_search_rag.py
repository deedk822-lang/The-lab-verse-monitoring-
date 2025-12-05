#!/usr/bin/env python3
"""
Tests for Semantic Search and RAG Services
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSemanticSearchService(unittest.TestCase):
    """Test Semantic Search Service"""

    def setUp(self):
        """Setup test fixtures"""
        from services.semantic_search_rag import SemanticSearchService

        # Mock environment
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

        self.service = SemanticSearchService()

        # Sample documents
        self.documents = [
            {"id": 1, "text": "Python programming tutorial", "title": "Learn Python"},
            {"id": 2, "text": "JavaScript web development", "title": "Web Dev Guide"},
            {"id": 3, "text": "Python data science basics", "title": "Data Science"},
            {"id": 4, "text": "Machine learning with Python", "title": "ML Guide"},
            {"id": 5, "text": "React frontend development", "title": "React Tutorial"}
        ]

    def tearDown(self):
        """Cleanup"""
        self.env_patcher.stop()

    def test_init_without_api_key(self):
        """Test initialization without API key"""
        from services.semantic_search_rag import SemanticSearchService
        with self.assertRaises(ValueError):
            SemanticSearchService()

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from services.semantic_search_rag import SemanticSearchService
            service = SemanticSearchService()
            self.assertTrue(service.available)

    def test_embed_texts_without_api_key(self):
        """Test text embedding without API key"""
        from services.semantic_search_rag import SemanticSearchService
        with self.assertRaises(ValueError):
            service = SemanticSearchService()
            service.embed_texts(["test1", "test2", "test3"])

    @patch('services.semantic_search_rag.cohere')
    def test_embed_texts_with_cohere(self, mock_cohere):
        """Test text embedding with Cohere API"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.embeddings = [[0.1] * 1024, [0.2] * 1024]
        mock_client.embed.return_value = mock_response
        mock_cohere.Client.return_value = mock_client

        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from services.semantic_search_rag import SemanticSearchService
            service = SemanticSearchService()

            embeddings = service.embed_texts(["test1", "test2"])
            self.assertEqual(embeddings.shape, (2, 1024))

    def test_build_index(self):
        """Test building search index"""
        self.service.build_index(self.documents, text_field="text")

        self.assertEqual(len(self.service.documents), 5)
        self.assertIsNotNone(self.service.embeddings)
        self.assertEqual(self.service.embeddings.shape[0], 5)

    def test_search_basic(self):
        """Test basic search functionality"""
        self.service.build_index(self.documents, text_field="text")

        results = self.service.search("Python programming", top_k=3)

        self.assertEqual(len(results), 3)
        self.assertIn('text', results[0])
        self.assertIn('similarity_score', results[0])

    def test_search_no_documents(self):
        """Test search with no documents indexed"""
        results = self.service.search("test query")
        self.assertEqual(len(results), 0)

    def test_search_relevance(self):
        """Test that search returns relevant results"""
        self.service.build_index(self.documents, text_field="text")

        results = self.service.search("Python data science", top_k=2)

        # Should return Python-related documents
        self.assertIn("Python", results[0]['text'])

    def test_find_similar(self):
        """Test finding similar documents"""
        self.service.build_index(self.documents, text_field="text")

        # Find documents similar to first document (Python tutorial)
        similar = self.service.find_similar(0, top_k=3)

        self.assertGreater(len(similar), 0)
        self.assertLessEqual(len(similar), 3)

    def test_brute_force_search(self):
        """Test brute force search fallback"""
        self.service.build_index(self.documents, text_field="text")
        self.service.search_index = None  # Disable Annoy

        query_embedding = self.service.embed_texts(["Python"], input_type="search_query")[0]
        results = self.service._search_brute_force(query_embedding, top_k=3, include_distances=True)

        self.assertEqual(len(results), 3)
        self.assertIn('similarity_score', results[0])


class TestRAGService(unittest.TestCase):
    """Test RAG Service"""

    def setUp(self):
        """Setup test fixtures"""
        from services.semantic_search_rag import RAGService

        # Mock environment
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

        self.service = RAGService()

        # Sample documents
        self.documents = [
            {
                "id": 1,
                "text": "The 2022 FIFA World Cup semi-finals were played on December 13 and 14.",
                "title": "World Cup 2022"
            },
            {
                "id": 2,
                "text": "Argentina defeated Croatia 3-0 in the first semi-final.",
                "title": "Argentina vs Croatia"
            },
            {
                "id": 3,
                "text": "France won against Morocco 2-0 in the second semi-final.",
                "title": "France vs Morocco"
            }
        ]

    def tearDown(self):
        """Cleanup"""
        self.env_patcher.stop()

    def test_init_without_api_key(self):
        """Test initialization without API key"""
        from services.semantic_search_rag import RAGService
        with self.assertRaises(ValueError):
            RAGService()

    def test_index_documents(self):
        """Test indexing documents"""
        self.service.index_documents(self.documents, text_field="text")

        self.assertEqual(len(self.service.search_service.documents), 3)
        self.assertIsNotNone(self.service.search_service.embeddings)

    def test_generate_response_without_api_key(self):
        """Test RAG response generation without API key"""
        from services.semantic_search_rag import RAGService
        with self.assertRaises(ValueError):
            service = RAGService()
            service.index_documents(self.documents, text_field="text")
            service.generate_response(
                "When were the World Cup semi-finals?",
                top_k=3
            )

    @patch('services.semantic_search_rag.cohere')
    def test_generate_response_with_api(self, mock_cohere):
        """Test RAG response with Cohere API"""
        mock_client = Mock()

        # Mock embedding
        mock_embed_response = Mock()
        mock_embed_response.embeddings = [[0.1] * 1024] * 3
        mock_client.embed.return_value = mock_embed_response

        # Mock chat
        mock_citation = Mock()
        mock_citation.text = "December 13 and 14"
        mock_citation.start = 0
        mock_citation.end = 20
        mock_citation.document_ids = ["0"]

        mock_chat_response = Mock()
        mock_chat_response.text = "The semi-finals were on December 13 and 14."
        mock_chat_response.citations = [mock_citation]
        mock_client.chat.return_value = mock_chat_response

        mock_cohere.Client.return_value = mock_client

        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from services.semantic_search_rag import RAGService
            service = RAGService()
            service.index_documents(self.documents, text_field="text")

            result = service.generate_response(
                "When were the World Cup semi-finals?",
                top_k=3,
                use_rerank=False
            )

            self.assertIn('response', result)
            self.assertIn('citations', result)
            self.assertEqual(len(result['citations']), 1)

    def test_rerank_documents_mock_mode(self):
        """Test document reranking in mock mode"""
        docs = self.documents.copy()
        reranked = self.service.rerank_documents(
            "World Cup semi-finals",
            docs,
            top_n=2
        )

        self.assertEqual(len(reranked), 2)

    @patch('services.semantic_search_rag.cohere')
    def test_rerank_documents_with_api(self, mock_cohere):
        """Test document reranking with API"""
        mock_client = Mock()

        mock_result = Mock()
        mock_result.index = 0
        mock_result.relevance_score = 0.95

        mock_response = Mock()
        mock_response.results = [mock_result]
        mock_client.rerank.return_value = mock_response
        mock_cohere.Client.return_value = mock_client

        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from services.semantic_search_rag import RAGService
            service = RAGService()

            reranked = service.rerank_documents(
                "test query",
                self.documents,
                top_n=1
            )

            self.assertEqual(len(reranked), 1)
            self.assertIn('rerank_score', reranked[0])


class TestContentClusteringService(unittest.TestCase):
    """Test Content Clustering Service"""

    def setUp(self):
        """Setup test fixtures"""
        from services.semantic_search_rag import ContentClusteringService

        # Mock environment
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

        self.service = ContentClusteringService()

        # Sample documents for clustering
        self.documents = [
            {"id": 1, "text": "Python programming basics"},
            {"id": 2, "text": "JavaScript web development"},
            {"id": 3, "text": "Python data science"},
            {"id": 4, "text": "React frontend framework"},
            {"id": 5, "text": "Machine learning Python"},
            {"id": 6, "text": "Vue.js JavaScript framework"},
            {"id": 7, "text": "Deep learning neural networks"},
            {"id": 8, "text": "Angular web framework"},
        ]

    def tearDown(self):
        """Cleanup"""
        self.env_patcher.stop()

    def test_cluster_documents(self):
        """Test document clustering"""
        result = self.service.cluster_documents(
            self.documents,
            n_clusters=3,
            text_field="text"
        )

        self.assertIn('documents', result)
        self.assertIn('n_clusters', result)
        self.assertIn('cluster_keywords', result)
        self.assertIn('cluster_sizes', result)

        self.assertEqual(result['n_clusters'], 3)
        self.assertEqual(len(result['documents']), 8)

        # Check cluster assignment
        for doc in result['documents']:
            self.assertIn('cluster', doc)
            self.assertIn('cluster_keywords', doc)

    def test_cluster_sizes(self):
        """Test cluster size calculation"""
        result = self.service.cluster_documents(
            self.documents,
            n_clusters=2,
            text_field="text"
        )

        sizes = result['cluster_sizes']
        total = sum(sizes.values())

        self.assertEqual(total, 8)
        self.assertEqual(len(sizes), 2)

    def test_extract_cluster_keywords(self):
        """Test keyword extraction"""
        result = self.service.cluster_documents(
            self.documents,
            n_clusters=2,
            text_field="text"
        )

        keywords = result['cluster_keywords']

        self.assertEqual(len(keywords), 2)
        for cluster_id, kws in keywords.items():
            self.assertIsInstance(kws, list)
            self.assertGreater(len(kws), 0)

    def test_visualize_clusters_no_umap(self):
        """Test visualization without UMAP installed"""
        # First cluster the documents
        self.service.cluster_documents(
            self.documents,
            n_clusters=2,
            text_field="text"
        )

        # Try to visualize
        with patch('services.semantic_search_rag.umap', None):
            result = self.service.visualize_clusters(self.documents)

            self.assertIn('documents', result)
            self.assertIn('success', result)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""

    def test_end_to_end_semantic_search(self):
        """Test complete semantic search workflow"""
        from services.semantic_search_rag import SemanticSearchService

        with patch.dict(os.environ, {}, clear=True):
            service = SemanticSearchService()

            # Create sample documents
            docs = [
                {"text": f"Document {i} about topic {i % 3}"}
                for i in range(20)
            ]

            # Build index
            service.build_index(docs)

            # Search
            results = service.search("topic 1", top_k=5)

            self.assertEqual(len(results), 5)
            self.assertIn('text', results[0])

    def test_end_to_end_rag(self):
        """Test complete RAG workflow"""
        from services.semantic_search_rag import RAGService

        with patch.dict(os.environ, {}, clear=True):
            service = RAGService()

            # Sample knowledge base
            docs = [
                {
                    "text": "Vaal AI Empire offers social media management for R600/month",
                    "title": "Pricing"
                },
                {
                    "text": "We generate 20 posts per month in Afrikaans or English",
                    "title": "Services"
                },
                {
                    "text": "Our clients include butcheries, cafes, and auto repair shops",
                    "title": "Clients"
                }
            ]

            # Index and query
            service.index_documents(docs)
            result = service.generate_response("What does Vaal AI Empire offer?")

            self.assertIn('response', result)
            self.assertIn('documents', result)

    def test_clustering_then_search(self):
        """Test clustering followed by search within clusters"""
        from services.semantic_search_rag import ContentClusteringService, SemanticSearchService

        with patch.dict(os.environ, {}, clear=True):
            # Create documents
            docs = [
                {"text": "Python machine learning"},
                {"text": "JavaScript React framework"},
                {"text": "Python data analysis"},
                {"text": "Vue.js web development"},
            ] * 3

            # Cluster
            cluster_service = ContentClusteringService()
            result = cluster_service.cluster_documents(docs, n_clusters=2)

            clustered_docs = result['documents']

            # Search within cluster 0
            cluster_0_docs = [d for d in clustered_docs if d['cluster'] == 0]

            if cluster_0_docs:
                search_service = SemanticSearchService()
                search_service.build_index(cluster_0_docs)

                search_results = search_service.search("machine learning", top_k=2)
                self.assertGreater(len(search_results), 0)


def run_semantic_search_tests():
    """Run all semantic search and RAG tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSemanticSearchService))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGService))
    suite.addTests(loader.loadTestsFromTestCase(TestContentClusteringService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("SEMANTIC SEARCH & RAG TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_semantic_search_tests() else 1)

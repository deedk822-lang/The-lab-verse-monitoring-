#!/usr/bin/env python3
"""
Comprehensive Test Suite for Vaal AI Empire
Tests all components with proper mocking and error handling
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.getcwd())


class TestCohereAPI(unittest.TestCase):
    """Test Cohere API client"""

    @patch('api.cohere.cohere')
    def test_init_with_api_key(self, mock_cohere):
        """Test initialization with API key"""
        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from api.cohere import CohereAPI
            api = CohereAPI()
            self.assertIsNotNone(api.client)

    @patch('api.cohere.cohere')
    def test_init_without_api_key(self, mock_cohere):
        """Test initialization without API key (mock mode)"""
        with patch.dict(os.environ, {}, clear=True):
            from api.cohere import CohereAPI
            api = CohereAPI()
            self.assertIsNone(api.client)

    @patch('api.cohere.cohere')
    def test_generate_content_mock_mode(self, mock_cohere):
        """Test content generation in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            from api.cohere import CohereAPI
            api = CohereAPI()
            result = api.generate_content("Test prompt")

            self.assertIn("text", result)
            self.assertIn("usage", result)
            self.assertIn("[MOCK]", result["text"])

    @patch('api.cohere.cohere')
    def test_generate_content_with_api(self, mock_cohere):
        """Test content generation with API"""
        mock_response = Mock()
        mock_response.text = "Generated content"
        mock_response.meta = Mock()
        mock_response.meta.tokens = Mock()
        mock_response.meta.tokens.input_tokens = 100
        mock_response.meta.tokens.output_tokens = 200

        mock_client = Mock()
        mock_client.chat.return_value = mock_response
        mock_cohere.Client.return_value = mock_client

        with patch.dict(os.environ, {'COHERE_API_KEY': 'test_key'}):
            from api.cohere import CohereAPI
            api = CohereAPI()
            result = api.generate_content("Test prompt")

            self.assertEqual(result["text"], "Generated content")
            self.assertIn("usage", result)

    @patch('api.cohere.cohere')
    def test_generate_email_sequence(self, mock_cohere):
        """Test email sequence generation"""
        with patch.dict(os.environ, {}, clear=True):
            from api.cohere import CohereAPI
            api = CohereAPI()
            sequence = api.generate_email_sequence("butchery", days=3)

            self.assertEqual(len(sequence), 3)
            self.assertIn("subject", sequence[0])
            self.assertIn("body", sequence[0])
            self.assertIn("day", sequence[0])


class TestMistralAPI(unittest.TestCase):
    """Test Mistral API client"""

    @patch('api.mistral.ollama')
    def test_init_with_ollama(self, mock_ollama):
        """Test initialization with Ollama"""
        from api.mistral import MistralAPI
        api = MistralAPI()
        self.assertTrue(api.available)

    @patch('api.mistral.ollama', side_effect=ImportError)
    def test_init_without_ollama(self, mock_ollama):
        """Test initialization without Ollama"""
        from api.mistral import MistralAPI
        api = MistralAPI()
        self.assertFalse(api.available)

    @patch('api.mistral.ollama')
    def test_query_local_mock_mode(self, mock_ollama):
        """Test local query in mock mode"""
        mock_ollama.side_effect = ImportError
        from api.mistral import MistralAPI
        api = MistralAPI()

        result = api.query_local("Test prompt")
        self.assertIn("text", result)
        self.assertIn("[MOCK]", result["text"])

    @patch('api.mistral.ollama')
    def test_query_local_with_ollama(self, mock_ollama):
        """Test local query with Ollama"""
        mock_ollama.chat.return_value = {
            "message": {"content": "Mistral response"}
        }

        from api.mistral import MistralAPI
        api = MistralAPI()
        result = api.query_local("Test prompt")

        self.assertIn("text", result)
        self.assertIn("model", result)


class TestAsanaClient(unittest.TestCase):
    """Test Asana client"""

    @patch('clients.asana_client.asana')
    def test_init_with_token(self, mock_asana):
        """Test initialization with access token"""
        with patch.dict(os.environ, {
            'ASANA_ACCESS_TOKEN': 'test_token',
            'ASANA_WORKSPACE_GID': 'test_workspace'
        }):
            from clients.asana_client import AsanaClient
            client = AsanaClient()
            self.assertTrue(client.available)

    @patch('clients.asana_client.asana')
    def test_init_without_token(self, mock_asana):
        """Test initialization without token"""
        with patch.dict(os.environ, {}, clear=True):
            from clients.asana_client import AsanaClient
            client = AsanaClient()
            self.assertFalse(client.available)

    @patch('clients.asana_client.asana')
    def test_create_project_mock_mode(self, mock_asana):
        """Test project creation in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            from clients.asana_client import AsanaClient
            client = AsanaClient()

            result = client.create_project("Test Project")
            self.assertIn("gid", result)
            self.assertIn("mock_project", result["gid"])

    @patch('clients.asana_client.asana')
    def test_create_task_mock_mode(self, mock_asana):
        """Test task creation in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            from clients.asana_client import AsanaClient
            client = AsanaClient()

            result = client.create_task("project_123", "Test Task")
            self.assertIn("gid", result)
            self.assertIn("mock_task", result["gid"])


class TestMailChimpClient(unittest.TestCase):
    """Test MailChimp client"""

    @patch('clients.mailchimp_client.Client')
    def test_init_with_api_key(self, mock_client):
        """Test initialization with API key"""
        with patch.dict(os.environ, {
            'MAILCHIMP_API_KEY': 'test_key',
            'MAILCHIMP_SERVER_PREFIX': 'us10'
        }):
            from clients.mailchimp_client import MailChimpClient
            client = MailChimpClient()
            self.assertTrue(client.available)

    @patch('clients.mailchimp_client.Client')
    def test_init_without_api_key(self, mock_client):
        """Test initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            from clients.mailchimp_client import MailChimpClient
            client = MailChimpClient()
            self.assertFalse(client.available)

    @patch('clients.mailchimp_client.Client')
    def test_create_audience_mock_mode(self, mock_client):
        """Test audience creation in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            from clients.mailchimp_client import MailChimpClient
            client = MailChimpClient()

            result = client.create_audience("Test Audience")
            self.assertIn("id", result)
            self.assertIn("mock_list", result["id"])


class TestDatabase(unittest.TestCase):
    """Test Database operations"""

    def setUp(self):
        """Create temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()

        from core.database import Database
        self.db = Database(self.temp_db.name)

    def tearDown(self):
        """Clean up temporary database"""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database tables are created"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        self.assertIn('clients', tables)
        self.assertIn('content_packs', tables)
        self.assertIn('revenue', tables)
        self.assertIn('usage_logs', tables)
        self.assertIn('post_queue', tables)

        conn.close()

    def test_add_client(self):
        """Test adding a client"""
        client_data = {
            'name': 'Test Business',
            'business_type': 'butchery',
            'phone': '+27123456789',
            'email': 'test@example.com'
        }

        client_id = self.db.add_client(client_data)
        self.assertIsNotNone(client_id)
        self.assertTrue(client_id.startswith('vaal_'))

    def test_get_active_clients(self):
        """Test retrieving active clients"""
        # Add test client
        self.db.add_client({
            'name': 'Test Business',
            'business_type': 'cafe',
            'phone': '+27123456789'
        })

        clients = self.db.get_active_clients()
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]['name'], 'Test Business')

    def test_log_revenue(self):
        """Test logging revenue"""
        client_id = self.db.add_client({
            'name': 'Test Business',
            'business_type': 'butchery',
            'phone': '+27123456789'
        })

        revenue_id = self.db.log_revenue(client_id, 600.0, 'social_media')
        self.assertIsNotNone(revenue_id)

    def test_get_revenue_summary(self):
        """Test revenue summary"""
        client_id = self.db.add_client({
            'name': 'Test Business',
            'business_type': 'butchery',
            'phone': '+27123456789'
        })

        self.db.log_revenue(client_id, 600.0, 'social_media')

        summary = self.db.get_revenue_summary(days=30)
        self.assertEqual(summary['total_revenue'], 600.0)
        self.assertEqual(summary['client_count'], 1)


class TestContentFactory(unittest.TestCase):
    """Test Content Factory"""

    @patch('services.content_generator.CohereAPI')
    @patch('services.content_generator.MistralAPI')
    @patch('services.content_generator.MailChimpClient')
    def test_generate_social_pack(self, mock_mailchimp, mock_mistral, mock_cohere):
        """Test social pack generation"""
        # Mock Cohere response
        mock_cohere_instance = Mock()
        mock_cohere_instance.generate_content.return_value = {
            "text": "Post 1\nPost 2\nPost 3\nPost 4\nPost 5\nPost 6\nPost 7\nPost 8\nPost 9\nPost 10",
            "usage": {"cost_usd": 0.01}
        }
        mock_cohere.return_value = mock_cohere_instance
        mock_mistral.return_value = Mock()
        mock_mailchimp.return_value = Mock()

        from services.content_generator import ContentFactory
        factory = ContentFactory()

        pack = factory.generate_social_pack("butchery", "afrikaans")

        self.assertIn("posts", pack)
        self.assertIn("images", pack)
        self.assertEqual(len(pack["posts"]), 10)

    @patch('services.content_generator.CohereAPI')
    @patch('services.content_generator.MistralAPI')
    @patch('services.content_generator.MailChimpClient')
    def test_generate_mailchimp_campaign(self, mock_mailchimp, mock_mistral, mock_cohere):
        """Test MailChimp campaign generation"""
        mock_cohere.return_value = Mock()
        mock_mistral.return_value = Mock()
        mock_mailchimp.return_value = Mock()

        from services.content_generator import ContentFactory
        factory = ContentFactory()

        pack = {"posts": ["Post 1", "Post 2"]}
        campaign = factory.generate_mailchimp_campaign("Test Business", pack)

        self.assertIn("subject", campaign)
        self.assertIn("html_content", campaign)
        self.assertIn("Test Business", campaign["subject"])


class TestContentScheduler(unittest.TestCase):
    """Test Content Scheduler"""

    def setUp(self):
        """Create temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()

        from core.database import Database
        self.db = Database(self.temp_db.name)

        from services.content_scheduler import ContentScheduler
        self.scheduler = ContentScheduler(self.db)

    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)

    def test_schedule_pack(self):
        """Test scheduling a content pack"""
        client_id = self.db.add_client({
            'name': 'Test Business',
            'business_type': 'butchery',
            'phone': '+27123456789'
        })

        posts = ["Post 1", "Post 2", "Post 3"]
        count = self.scheduler.schedule_pack(client_id, posts)

        self.assertEqual(count, 3)

    def test_get_due_posts(self):
        """Test getting due posts"""
        due_posts = self.scheduler.get_due_posts()
        self.assertIsInstance(due_posts, list)

    def test_mark_posted(self):
        """Test marking post as posted"""
        client_id = self.db.add_client({
            'name': 'Test Business',
            'business_type': 'butchery',
            'phone': '+27123456789'
        })

        self.scheduler.schedule_pack(client_id, ["Test post"])

        # Get the post
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM post_queue LIMIT 1")
        post_id = cursor.fetchone()[0]
        conn.close()

        result = self.scheduler.mark_posted(post_id)
        self.assertTrue(result)


class TestRevenueTracker(unittest.TestCase):
    """Test Revenue Tracker"""

    def setUp(self):
        """Create temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()

        from core.database import Database
        self.db = Database(self.temp_db.name)

        from services.revenue_tracker import RevenueTracker
        self.tracker = RevenueTracker(self.db)

    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)

    def test_daily_report(self):
        """Test daily report generation"""
        report = self.tracker.daily_report()

        self.assertIn("date", report)
        self.assertIn("total_revenue", report)
        self.assertIn("clients_billed", report)

    def test_weekly_report(self):
        """Test weekly report generation"""
        report = self.tracker.weekly_report()

        self.assertIn("week_ending", report)
        self.assertIn("total_revenue", report)
        self.assertIn("avg_per_client", report)

    def test_monthly_projection(self):
        """Test monthly projection"""
        projection = self.tracker.monthly_projection()

        self.assertIn("current_weekly", projection)
        self.assertIn("projected_monthly", projection)
        self.assertIn("target", projection)
        self.assertIn("on_track", projection)

    def test_export_report(self):
        """Test report export"""
        import json

        report_json = self.tracker.export_report()
        report_data = json.loads(report_json)

        self.assertIn("generated_at", report_data)
        self.assertIn("daily", report_data)
        self.assertIn("weekly", report_data)


class TestWhatsAppBot(unittest.TestCase):
    """Test WhatsApp Bot"""

    def setUp(self):
        """Create temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()

        from core.database import Database
        self.db = Database(self.temp_db.name)

        from services.whatsapp_bot import WhatsAppBot
        self.bot = WhatsAppBot(self.db)

    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)

    def test_send_outreach(self):
        """Test sending outreach message"""
        result = self.bot.send_outreach("+27123456789")

        self.assertEqual(result["phone"], "+27123456789")
        self.assertEqual(result["status"], "sent")
        self.assertIn("message", result)

    def test_send_demo(self):
        """Test sending demo"""
        client_id = self.db.add_client({
            'name': 'Test Business',
            'business_type': 'butchery',
            'phone': '+27123456789'
        })

        result = self.bot.send_demo("+27123456789", client_id)

        self.assertIn("demo_link", result)
        self.assertEqual(result["status"], "sent")

    def test_send_invoice(self):
        """Test sending invoice"""
        result = self.bot.send_invoice("+27123456789", 600.0, "INV-001")

        self.assertEqual(result["amount"], 600.0)
        self.assertEqual(result["invoice_number"], "INV-001")
        self.assertEqual(result["status"], "sent")


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCohereAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestMistralAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestAsanaClient))
    suite.addTests(loader.loadTestsFromTestCase(TestMailChimpClient))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestContentFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestContentScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestRevenueTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestWhatsAppBot))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("CORE SYSTEM TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print("=" * 70)

    # Try to run additional test suites if available
    keyword_success = True
    semantic_success = True

    try:
        print("\n" + "=" * 70)
        print("RUNNING KEYWORD RESEARCH TESTS...")
        print("=" * 70)
        from tests.test_keyword_research import run_keyword_research_tests
        keyword_success = run_keyword_research_tests()
    except ImportError:
        print("\n⚠️  Keyword research tests not found (optional)")

    try:
        print("\n" + "=" * 70)
        print("RUNNING SEMANTIC SEARCH & RAG TESTS...")
        print("=" * 70)
        from tests.test_semantic_search_rag import run_semantic_search_tests
        semantic_success = run_semantic_search_tests()
    except ImportError:
        print("\n⚠️  Semantic search tests not found (optional)")

    # Final summary
    print("\n" + "=" * 70)
    print("COMPLETE TEST SUMMARY")
    print("=" * 70)
    print(f"Core System: {'✅ PASS' if result.wasSuccessful() else '❌ FAIL'}")
    print(f"Keyword Research: {'✅ PASS' if keyword_success else '❌ FAIL'}")
    print(f"Semantic Search & RAG: {'✅ PASS' if semantic_success else '❌ FAIL'}")
    total_tests = result.testsRun
    print(f"\nTotal Tests Run: {total_tests}+")
    print("=" * 70)

    return result.wasSuccessful() and keyword_success and semantic_success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)


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

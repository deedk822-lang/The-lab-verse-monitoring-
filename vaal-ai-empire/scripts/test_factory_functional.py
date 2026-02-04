
import sys
import os
import logging

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))

from services.content_generator import ContentFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_factory_functional():
    print("=" * 60)
    print("RUNNING FUNCTIONAL TESTS FOR ContentFactory")
    print("=" * 60)

    # Mock DB if needed
    class MockDB:
        def log_api_usage(self, *args): pass
        def save_content_pack(self, *args, **kwargs): pass

    db = MockDB()
    factory = ContentFactory(db=db)

    # Mock generate_content to avoid real API calls
    def mocked_generate_content(prompt, max_tokens=500):
        return {
            "text": "Post 1 --- Post 2 --- Post 3 --- Post 4 --- Post 5 --- Post 6 --- Post 7 --- Post 8 --- Post 9 --- Post 10",
            "provider": "mock",
            "cost_usd": 0.0,
            "tokens": 0
        }
    factory.generate_content = mocked_generate_content

    # Test generate_social_pack
    print("\nTesting generate_social_pack...")
    num_posts = 10
    num_images = 5
    pack = factory.generate_social_pack("butchery", num_posts=num_posts, num_images=num_images)

    assert len(pack["posts"]) == num_posts, f"Expected {num_posts} posts, got {len(pack['posts'])}"
    assert len(pack["images"]) == num_images, f"Expected {num_images} images, got {len(pack['images'])}"
    assert "metadata" in pack
    print("✓ generate_social_pack functional")

    # Test _get_cached_providers unpacked values
    assert hasattr(factory, 'providers')
    assert hasattr(factory, 'image_generator')
    assert hasattr(factory, 'multimodal_provider')
    print("✓ _get_cached_providers unpacking functional")

    print("\nALL FUNCTIONAL TESTS PASSED")

if __name__ == "__main__":
    try:
        test_factory_functional()
    except Exception as e:
        logger.error(f"Functional test failed: {e}")
        sys.exit(1)

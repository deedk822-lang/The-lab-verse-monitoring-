# scripts/publish_content.py
"""
Publish content from HTML to multiple channels.
"""

import argparse
import logging
import os
import sys
from typing import Optional

from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ContentPublisher")

# Add project root to path
sys.path.insert(0, os.path.abspath('vaal-ai-empire'))


# === Make all tool imports optional ===
AVAILABLE_TOOLS = {}

try:
    import requests
    AVAILABLE_TOOLS['requests'] = True
    logger.info("✓ Requests loaded")
except ImportError:
    AVAILABLE_TOOLS['requests'] = False
    logger.error("✗ Requests not installed: pip install requests")

try:
    import mailchimp_marketing as MailchimpMarketing
    from mailchimp_marketing.api_client import ApiClientError
    AVAILABLE_TOOLS['mailchimp'] = True
    logger.info("✓ MailChimp SDK loaded")
except ImportError:
    AVAILABLE_TOOLS['mailchimp'] = False
    logger.warning("✗ MailChimp SDK not installed: pip install mailchimp-marketing")

# Import our content factory
try:
    from services.content_generator import ContentFactory
    AVAILABLE_TOOLS['content_factory'] = True
    logger.info("✓ ContentFactory loaded")
except ImportError as e:
    AVAILABLE_TOOLS['content_factory'] = False
    logger.error(f"✗ Failed to import ContentFactory: {e}. Ensure PYTHONPATH is set correctly.")


# === Publishing Tools ===
class AyrshareTool:
    def __init__(self):
        self.api_key = os.getenv("AYRSHARE_API_KEY")
        self.url = "https://app.ayrshare.com/api/post"

        if not self.api_key:
            logger.warning("AYRSHARE_API_KEY not set - social posting disabled")

    def post_to_socials(self, text: str, image_url: Optional[str] = None) -> str:
        if not self.api_key:
            return "SKIPPED: Ayrshare API key not configured"

        if not AVAILABLE_TOOLS.get('requests'):
            return "ERROR: requests library not installed"

        logger.info("🗣️ AYRSHARE: Broadcasting to Social Media...")

        payload = {
            "post": text,
            "platforms": ["twitter", "linkedin", "facebook"]
        }

        if image_url:
            payload["mediaUrls"] = [image_url]

        headers = {'Authorization': f'Bearer {self.api_key}'}

        try:
            r = requests.post(self.url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            result = r.json()
            if result.get('status') == 'success':
                 return "SUCCESS: Posted via Ayrshare."
            else:
                 return f"ERROR: Ayrshare responded with status '{result.get('status')}' - {result.get('message', 'No message')}"
        except requests.exceptions.RequestException as e:
            logger.error(f"Ayrshare request failed: {e}")
            return f"ERROR: {str(e)}"

class MailChimpTool:
    def __init__(self):
        self.api_key = os.getenv("MAILCHIMP_MARKETING__KEY")
        self.server = os.getenv("MAILCHIMP_SERVER_PREFIX")
        self.list_id = os.getenv("MAILCHIMP_LIST_ID")

        self.client = None

        if not all([self.api_key, self.server, self.list_id]):
            logger.warning("MailChimp credentials incomplete - newsletter disabled (need MAILCHIMP_MARKETING__KEY, MAILCHIMP_SERVER_PREFIX, MAILCHIMP_LIST_ID)")
            return

        if not AVAILABLE_TOOLS.get('mailchimp'):
            logger.warning("mailchimp-marketing library not installed")
            return

        try:
            self.client = MailchimpMarketing.Client()
            self.client.set_config({
                "api_key": self.api_key,
                "server": self.server
            })
        except Exception as e:
            logger.error(f"MailChimp client initialization failed: {e}")
            self.client = None

    def send_campaign(self, subject: str, html_content: str, plain_text: str) -> str:
        if not self.client:
            return "SKIPPED: MailChimp not configured"

        logger.info(f"📧 MAILCHIMP: Preparing Campaign '{subject}'...")

        try:
            campaign = self.client.campaigns.create({
                "type": "regular",
                "recipients": {"list_id": self.list_id},
                "settings": {
                    "subject_line": subject,
                    "title": f"Vaal Uprising Campaign - {subject}",
                    "from_name": os.getenv("MAILCHIMP_FROM_NAME", "Vaal AI Empire"),
                    "reply_to": os.getenv("MAILCHIMP_REPLY_TO", "deedk822@gmail.com")
                }
            })

            campaign_id = campaign['id']
            logger.info(f"MailChimp campaign created with ID: {campaign_id}")

            self.client.campaigns.set_content(campaign_id, {
                "html": html_content,
            })
            logger.info("MailChimp campaign content has been set.")

            logger.warning(f"MAILCHIMP: Campaign '{campaign_id}' is ready. Sending is disabled in this script for safety.")

            return f"SUCCESS: Campaign '{subject}' created for list {self.list_id}. Sending is disabled for safety."

        except ApiClientError as e:
            logger.error(f"MailChimp API Error: {e.text}")
            return f"ERROR: {e.text}"
        except Exception as e:
            logger.error(f"An unexpected MailChimp error occurred: {e}")
            return f"ERROR: {str(e)}"


class WordPressTool:
    def __init__(self):
        self.site_url = os.getenv("WORDPRESS_SITE_URL")
        self.username = os.getenv("WORDPRESS_USERNAME")
        self.app_password = os.getenv("WORDPRESS_APP_PASSWORD")

        if not all([self.site_url, self.username, self.app_password]):
            logger.warning("WordPress credentials incomplete - publishing disabled")

    def publish_article(self, title: str, content: str, tags: list = None) -> str:
        if not all([self.site_url, self.username, self.app_password]):
            return "SKIPPED: WordPress not configured"

        if not AVAILABLE_TOOLS.get('requests'):
            return "ERROR: requests library not installed"

        logger.info(f"📝 WORDPRESS: Publishing '{title}'...")

        url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/posts"

        payload = {
            "title": title,
            "content": content,
            "status": "publish"
        }

        try:
            r = requests.post(
                url,
                json=payload,
                auth=(self.username, self.app_password),
                timeout=20
            )
            r.raise_for_status()
            post_data = r.json()
            return f"SUCCESS: Published at {post_data.get('link', 'WordPress')}"
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            logger.error(f"WordPress request failed: {error_text}")
            return f"ERROR: {error_text}"


# === Content Parsing ===
def parse_html_content(filepath: str) -> (Optional[str], Optional[str], Optional[str]):
    try:
        with open(filepath, encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No Title Found"
        article_div = soup.find('div', class_='article-content')

        if article_div:
            text_content = article_div.get_text(separator='\n\n', strip=True)
            article_html = str(article_div)
        else:
            logger.warning("Could not find a div with class 'article-content'")
            text_content = "No article content found."
            article_html = "<p>No article content found.</p>"

        return title, text_content, article_html

    except FileNotFoundError:
        logger.error(f"HTML file not found at: {filepath}")
        return None, None, None
    except Exception as e:
        logger.error(f"Failed to parse HTML file: {e}")
        return None, None, None


def run_pipeline(html_filepath: str):
    logger.info("="*60)
    logger.info("🚀 STARTING CONTENT PUBLISHING PIPELINE")
    logger.info("="*60)

    if not AVAILABLE_TOOLS.get('content_factory'):
        logger.critical("ContentFactory is not available. Aborting pipeline.")
        return

    # === STEP 1: SOURCE - HTML FILE ===
    logger.info(f"\n📥 STEP 1: Parsing HTML Content from {html_filepath}...")
    title, raw_text, article_html = parse_html_content(html_filepath)

    if not title or not raw_text:
        logger.error("Failed to get content from HTML. Aborting.")
        return

    logger.info("   Successfully parsed content.")
    logger.info(f"   Title: {title}")

    # === STEP 2: BRAIN - CONTENT GENERATION ===
    logger.info("\n🧠 STEP 2: Generating Content with Cohere...")
    content_factory = ContentFactory()

    social_prompt = f"Create a short, engaging social media post (under 280 characters) for Twitter/X and LinkedIn to promote a new article titled '{title}'. The article is about the rise of an autonomous AI in South Africa's Vaal Triangle. Include relevant hashtags like #AI, #SouthAfrica, #Tech, #Innovation, #VaalAI."
    try:
        social_result = content_factory.generate_content(social_prompt, max_tokens=150)
        social_text = social_result['text']
        logger.info(f"   Generated Social Post: {social_text}")
    except Exception as e:
        logger.error(f"   Failed to generate social post: {e}")
        social_text = f"Read our latest article: {title} #AI #SouthAfrica"

    email_prompt = f"Write an exciting email newsletter to announce a new article titled '{title}'. The tone should be bold and inspiring. Briefly summarize the article's core message: a new autonomous AI is transforming South African SMEs, starting in the Vaal. Encourage readers to click a link to read the full manifesto. Keep it under 200 words."
    try:
        email_result = content_factory.generate_content(email_prompt, max_tokens=300)
        email_text = email_result['text']
        logger.info("   Generated Email Body.")
    except Exception as e:
        logger.error(f"   Failed to generate email body: {e}")
        email_text = f"Hello,\n\nWe've just published a groundbreaking new article: '{title}'.\n\n{raw_text[:300]}...\n\nRead more on our blog!"

    # === STEP 3: DISTRIBUTION BLITZ ===
    logger.info("\n📤 STEP 3: Multi-Channel Distribution...")
    report_log = []

    wp = WordPressTool()
    wp_result = wp.publish_article(title, article_html)
    logger.info(f"   WordPress: {wp_result}")
    report_log.append(f"WordPress: {wp_result}")

    ayr = AyrshareTool()
    social_result = ayr.post_to_socials(social_text)
    logger.info(f"   Ayrshare: {social_result}")
    report_log.append(f"Ayrshare: {social_result}")

    mc = MailChimpTool()
    email_html = f"<html><body style='font-family: Arial, sans-serif;'><h1>{title}</h1><p>{email_text.replace(os.linesep, '<br>')}</p><p>Read the full story on our blog!</p></body></html>"
    email_result = mc.send_campaign(f"Vaal AI Newsletter: {title}", email_html, email_text)
    logger.info(f"   MailChimp: {email_result}")
    report_log.append(f"MailChimp: {email_result}")

    # === SUMMARY ===
    logger.info("\n" + "="*60)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info("="*60)
    logger.info("\nDistribution Summary:")
    for log_entry in report_log:
        logger.info(f"   {log_entry}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish content from an HTML file to multiple channels.")
    parser.add_argument("html_filepath", type=str, help="The path to the HTML file to be published.")
    args = parser.parse_args()

    try:
        run_pipeline(args.html_filepath)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

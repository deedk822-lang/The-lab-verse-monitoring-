import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class MailChimpClient:
    def __init__(self):
        try:
            from mailchimp_marketing import Client
            self.client = Client()
 feat/production-hardening-and-keyword-research
        except ImportError:
            raise ImportError("MailChimp SDK not installed. Please install it with 'pip install mailchimp-marketing'")

        api_key = os.getenv("MAILCHIMP_API_KEY")
        server = os.getenv("MAILCHIMP_SERVER_PREFIX", "us10")

        if not api_key:
            raise ValueError("MAILCHIMP_API_KEY environment variable not set.")

        self.client.set_config({
            "api_key": api_key,
            "server": server
        })

    def create_audience(self, name: str) -> Dict:
        """Create new MailChimp audience"""

            api_key = os.getenv("MAILCHIMP_API_KEY")
            server = os.getenv("MAILCHIMP_SERVER_PREFIX", "us10")

            if api_key:
                self.client.set_config({
                    "api_key": api_key,
                    "server": server
                })
                self.available = True
            else:
                logger.warning("MAILCHIMP_API_KEY not set - using mock mode")
                self.available = False
        except ImportError:
            logger.warning("MailChimp SDK not installed - using mock mode")
            self.available = False

    def create_audience(self, name: str) -> Dict:
        """Create new MailChimp audience"""
        if not self.available:
            return {
                "id": f"mock_list_{name.replace(' ', '_')}",
                "name": name,
                "status": "mock"
            }

 main
        try:
            return self.client.lists.create_list({
                "name": name,
                "contact": {
                    "company": "Vaal AI Empire",
                    "address1": "123 Main St",
                    "city": "Vereeniging",
                    "state": "GP",
                    "zip": "1939",
                    "country": "ZA"
                },
                "permission_reminder": "You opted in to our list",
                "campaign_defaults": {
                    "from_name": "Vaal AI Empire",
                    "from_email": "hello@vaalaicorp.co.za",
                    "subject": "Weekly Update",
                    "language": "af"
                },
                "email_type_option": True
            })
        except Exception as e:
            logger.error(f"MailChimp error: {e}")
 feat/production-hardening-and-keyword-research
            raise e

            return {"error": str(e), "id": "error"}
 main

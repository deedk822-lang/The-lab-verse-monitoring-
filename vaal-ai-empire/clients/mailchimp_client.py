import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class MailChimpClient:
    def __init__(self):
        try:
            from mailchimp_marketing import Client
            self.client = Client()
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

        # Load contact details from environment variables
        self.contact_company = os.getenv("MAILCHIMP_CONTACT_COMPANY", "Vaal AI Empire")
        self.contact_address1 = os.getenv("MAILCHIMP_CONTACT_ADDR1", "123 Main St")
        self.contact_city = os.getenv("MAILCHIMP_CONTACT_CITY", "Vereeniging")
        self.contact_state = os.getenv("MAILCHIMP_CONTACT_STATE", "GP")
        self.contact_zip = os.getenv("MAILCHIMP_CONTACT_ZIP", "1939")
        self.contact_country = os.getenv("MAILCHIMP_CONTACT_COUNTRY", "ZA")
        self.from_name = os.getenv("MAILCHIMP_FROM_NAME", "Vaal AI Empire")
        self.from_email = os.getenv("MAILCHIMP_FROM_EMAIL", "hello@vaalaicorp.co.za")


    def create_audience(self, name: str) -> Dict:
        """Create new MailChimp audience"""
        try:
            return self.client.lists.create_list({
                "name": name,
                "contact": {
                    "company": self.contact_company,
                    "address1": self.contact_address1,
                    "city": self.contact_city,
                    "state": self.contact_state,
                    "zip": self.contact_zip,
                    "country": self.contact_country
                },
                "permission_reminder": "You opted in to our list",
                "campaign_defaults": {
                    "from_name": self.from_name,
                    "from_email": self.from_email,
                    "subject": "Weekly Update",
                    "language": "af"
                },
                "email_type_option": True
            })
        except Exception as e:
            logger.error(f"MailChimp error: {e}")
            raise e

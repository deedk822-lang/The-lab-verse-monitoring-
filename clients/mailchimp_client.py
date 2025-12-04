import os
from mailchimp3 import MailChimp

class MailChimpClient:
    def __init__(self):
        self.api_key = os.getenv("MAILCHIMP_API_KEY")
        self.server_prefix = os.getenv("MAILCHIMP_SERVER_PREFIX")
        self.available = bool(self.api_key and self.server_prefix)
        self.client = MailChimp(mc_api=self.api_key, mc_user=self.server_prefix) if self.available else None

    def create_audience(self, name):
        if not self.available:
            return {"id": "mock_list_123"}
        return self.client.lists.create({"name": name, "contact": {"company": "Vaal AI Empire", "address1": "123 Street", "city": "Vereeniging", "state": "Gauteng", "zip": "1930", "country": "ZA"}, "permission_reminder": "You're receiving this email because you opted in for updates.", "campaign_defaults": {"from_name": "Vaal AI Empire", "from_email": "noreply@vaal-ai.co.za", "subject": "", "language": "en"}, "email_type_option": False})

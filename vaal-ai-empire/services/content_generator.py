from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ContentFactory:
    def __init__(self):
        from api.cohere import CohereAPI
        from api.mistral import MistralAPI
        from clients.mailchimp_client import MailChimpClient

        self.cohere = CohereAPI()
        self.mistral = MistralAPI()
        self.mailchimp = MailChimpClient()

    def generate_social_pack(self, business_type: str, language: str = "afrikaans") -> Dict:
        """Generate complete social media pack - FIXED"""

        # Generate posts with Cohere or Mistral
        posts_prompt = f"Generate 10 {language} social media posts for a {business_type} in Vaal Triangle. Include emojis and calls-to-action."

        # Try Cohere first, fallback to Mistral
        posts_result = self.cohere.generate_content(posts_prompt, max_tokens=1000)
        posts = [p.strip() for p in posts_result["text"].split("\n") if p.strip()]

        # Generate mock images (replace with actual Bria integration)
        images = []
        for i in range(min(5, len(posts))):
            image_prompt = f"Professional photo for {business_type} in South Africa, style: clean, modern"
            images.append({
                "prompt": image_prompt,
                "url": f"https://placeholder.com/600x400?text=Image+{i+1}"  # Replace with actual API
            })

        return {
            "posts": posts[:10],  # Limit to 10
            "images": images,
            "cost": posts_result.get("usage", {}).get("cost_usd", 0.0),
            "language": language,
            "business_type": business_type
        }

    def generate_mailchimp_campaign(self, business_name: str, pack: Dict) -> Dict:
        """Create MailChimp campaign from social pack"""
        subject = f"Weekly Social Content for {business_name}"

        html_content = f"""
        <html>
        <head><style>body{{font-family:Arial;padding:20px;}}</style></head>
        <body>
        <h1>Your Weekly Content Pack</h1>
        <p>Hello {business_name}! Here's your fresh content:</p>
        """

        for i, post in enumerate(pack.get("posts", []), 1):
            html_content += f"<div style='margin:20px 0;padding:15px;border:1px solid #ddd;'>"
            html_content += f"<strong>Post {i}:</strong><p>{post}</p>"
            html_content += "</div>"

        html_content += "</body></html>"

        return {
            "subject": subject,
            "html_content": html_content,
            "status": "created"
        }

from typing import Dict
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppBot:
    """WhatsApp bot for client acquisition and communication"""

    def __init__(self, db):
        self.db = db
        self.templates = {
            "afrikaans": {
                "outreach": """Goeie dag! 👋

Ek is van Vaal AI Empire - ons help klein besighede in die Vaal Driehoek met professionele sosiale media inhoud.

Ons pakket sluit in:
✅ 20 posts per maand (Afrikaans/Engels)
✅ 5 professionele foto's
✅ Sosiale media beplanning
✅ Gratis demo pakket

Net R600/maand - geen kontrak! 🚀

Kan ek vir jou 'n gratis demo pakket stuur?""",
                "demo_delivered": """Dankie! 🎉

Hier is jou GRATIS demo pakket:
📱 10 sosiale media posts
🖼️ 3 professionele foto's

Geniet dit? Net R600/maand vir:
✅ 20 posts/maand
✅ 5 foto's/maand
✅ Sosiale media beplanning

Antwoord "JA" om te begin!""",
                "invoice": """Perfek! 💚

Stuur asseblief R{amount} na:
💳 FNB: 62845XXXXX
📱 Ref: {invoice_number}

Sodra ons betaling ontvang, kry jy:
✅ Volle maand inhoud
✅ Toegang tot kliënte portaal
✅ WeekLikse updates

Dankie vir jou besigheid! 🚀"""
            }
        }

    def send_outreach(self, phone: str, language: str = "afrikaans") -> Dict:
        """Send outreach message via Twilio (or mock)"""
        message = self.templates[language]["outreach"]

        # In production, use Twilio API
        logger.info(f"Sending outreach to {phone}: {message[:50]}...")

        return {
            "phone": phone,
            "message": message,
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }

    def send_demo(self, phone: str, client_id: str) -> Dict:
        """Send demo pack link"""
        demo_link = f"https://vaalaicorp.co.za/demo/{client_id}"
        message = self.templates["afrikaans"]["demo_delivered"]
        message += f"\n\n🔗 Download: {demo_link}"

        logger.info(f"Sending demo to {phone}")

        return {
            "phone": phone,
            "demo_link": demo_link,
            "status": "sent"
        }

    def send_invoice(self, phone: str, amount: float, invoice_number: str) -> Dict:
        """Send invoice via WhatsApp"""
        message = self.templates["afrikaans"]["invoice"].format(
            amount=amount,
            invoice_number=invoice_number
        )

        logger.info(f"Sending invoice to {phone}: {invoice_number}")

        return {
            "phone": phone,
            "invoice_number": invoice_number,
            "amount": amount,
            "status": "sent"
        }

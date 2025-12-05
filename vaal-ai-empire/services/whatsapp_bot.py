from datetime import datetime
from typing import Dict, Optional
import requests
import logging
import os

logger = logging.getLogger(__name__)

class WhatsAppBot:
    """Real WhatsApp bot using Twilio API"""

    def __init__(self, db=None):
        self.db = db
        self.use_twilio = self._init_twilio()

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
✅ Weeklikse updates

Dankie vir jou besigheid! 🚀""",

                "payment_received": """Dankie vir jou betaling! 🎉

Ons het R{amount} ontvang (Ref: {invoice_number}).

Jou inhoud word nou gegenereer en sal binne 24 uur gereed wees.

Verwag:
✅ 20 posts
✅ 5 foto's
✅ Toegang tot portaal

Welkom by Vaal AI Empire! 🚀""",

                "content_ready": """Goeie nuus! 📱

Jou inhoud is gereed:
✅ {posts_count} posts
✅ {images_count} foto's

Alles is geskeduleer en sal outomaties geplaas word.

Kyk portaal: {portal_url}

Vrae? Antwoord hierdie boodskap! 😊"""
            },

            "english": {
                "outreach": """Good day! 👋

I'm from Vaal AI Empire - we help small businesses in Vaal Triangle with professional social media content.

Our package includes:
✅ 20 posts per month (Afrikaans/English)
✅ 5 professional photos
✅ Social media scheduling
✅ Free demo pack

Only R600/month - no contract! 🚀

Can I send you a free demo pack?""",

                "demo_delivered": """Thank you! 🎉

Here's your FREE demo pack:
📱 10 social media posts
🖼️ 3 professional photos

Like it? Only R600/month for:
✅ 20 posts/month
✅ 5 photos/month
✅ Social media scheduling

Reply "YES" to get started!""",

                "invoice": """Perfect! 💚

Please send R{amount} to:
💳 FNB: 62845XXXXX
📱 Ref: {invoice_number}

Once we receive payment, you'll get:
✅ Full month's content
✅ Client portal access
✅ Weekly updates

Thank you for your business! 🚀""",

                "payment_received": """Thank you for your payment! 🎉

We've received R{amount} (Ref: {invoice_number}).

Your content is being generated and will be ready within 24 hours.

Expect:
✅ 20 posts
✅ 5 photos
✅ Portal access

Welcome to Vaal AI Empire! 🚀""",

                "content_ready": """Good news! 📱

Your content is ready:
✅ {posts_count} posts
✅ {images_count} photos

Everything is scheduled and will post automatically.

Check portal: {portal_url}

Questions? Reply to this message! 😊"""
            }
        }

    def _init_twilio(self) -> bool:
        """Initialize Twilio client"""
        try:
            from twilio.rest import Client

            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.from_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

            if not account_sid or not auth_token:
                logger.warning("Twilio credentials not set - using simulation mode")
                return False

            self.twilio_client = Client(account_sid, auth_token)
            logger.info("✅ Twilio WhatsApp initialized")
            return True

        except ImportError:
            logger.warning("Twilio SDK not installed - using simulation mode")
            return False
        except Exception as e:
            logger.error(f"Twilio initialization failed: {e}")
            return False

    def send_message(self, to_phone: str, message: str, media_url: Optional[str] = None) -> Dict:
        """
        Send WhatsApp message via Twilio

        Args:
            to_phone: Recipient phone (format: +27XXXXXXXXX)
            message: Message text
            media_url: Optional media URL

        Returns:
            Dict with status and message_sid
        """
        # Ensure phone has whatsapp: prefix
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        if self.use_twilio:
            try:
                # Send via Twilio
                kwargs = {
                    "from_": self.from_whatsapp,
                    "body": message,
                    "to": to_phone
                }

                if media_url:
                    kwargs["media_url"] = [media_url]

                message_obj = self.twilio_client.messages.create(**kwargs)

                logger.info(f"✅ WhatsApp sent to {to_phone}: {message_obj.sid}")

                # Log in database
                if self.db:
                    self.db.log_api_usage(
                        "twilio_whatsapp",
                        "send_message",
                        tokens_used=len(message),
                        cost_usd=0.005,  # Approximate Twilio cost per WhatsApp message
                        success=True
                    )

                return {
                    "status": "sent",
                    "message_sid": message_obj.sid,
                    "to": to_phone,
                    "sent_at": datetime.now().isoformat(),
                    "simulated": False
                }

            except Exception as e:
                logger.error(f"Twilio send failed: {e}")

                if self.db:
                    self.db.log_api_usage(
                        "twilio_whatsapp",
                        "send_message",
                        success=False,
                        error_message=str(e)
                    )

                return {
                    "status": "error",
                    "error": str(e),
                    "to": to_phone
                }
        else:
            # Simulation mode
            logger.info(f"📱 [SIMULATED] WhatsApp to {to_phone}:")
            logger.info(f"   Message: {message[:100]}...")
            if media_url:
                logger.info(f"   Media: {media_url}")

            return {
                "status": "simulated",
                "to": to_phone,
                "message": message[:100],
                "sent_at": datetime.now().isoformat(),
                "simulated": True
            }

    def send_outreach(self, phone: str, language: str = "afrikaans") -> Dict:
        """Send outreach message"""
        message = self.templates[language]["outreach"]
        return self.send_message(phone, message)

    def send_demo(self, phone: str, client_id: str, language: str = "afrikaans") -> Dict:
        """Send demo pack notification with link"""
        demo_link = f"https://vaalaicorp.co.za/demo/{client_id}"
        message = self.templates[language]["demo_delivered"]
        message += f"\n\n🔗 Download: {demo_link}"

        return self.send_message(phone, message)

    def send_invoice(self, phone: str, amount: float, invoice_number: str,
                    language: str = "afrikaans") -> Dict:
        """Send invoice via WhatsApp"""
        message = self.templates[language]["invoice"].format(
            amount=amount,
            invoice_number=invoice_number
        )

        return self.send_message(phone, message)

    def send_payment_confirmation(self, phone: str, amount: float,
                                 invoice_number: str, language: str = "afrikaans") -> Dict:
        """Send payment confirmation"""
        message = self.templates[language]["payment_received"].format(
            amount=amount,
            invoice_number=invoice_number
        )

        return self.send_message(phone, message)

    def send_content_ready_notification(self, phone: str, posts_count: int,
                                       images_count: int, portal_url: str,
                                       language: str = "afrikaans") -> Dict:
        """Notify client that content is ready"""
        message = self.templates[language]["content_ready"].format(
            posts_count=posts_count,
            images_count=images_count,
            portal_url=portal_url
        )

        return self.send_message(phone, message)

    def send_with_media(self, phone: str, message: str, media_path: str) -> Dict:
        """Send message with attached media"""
        # Upload media to accessible URL (would need proper hosting)
        # For now, use local path or placeholder

        media_url = f"https://vaalaicorp.co.za/media/{os.path.basename(media_path)}"

        return self.send_message(phone, message, media_url=media_url)

    def handle_incoming_message(self, from_phone: str, message_body: str) -> Dict:
        """
        Handle incoming WhatsApp message

        This would be called by your webhook endpoint
        """
        logger.info(f"Incoming WhatsApp from {from_phone}: {message_body}")

        # Simple keyword detection
        message_lower = message_body.lower().strip()

        response = None

        if message_lower in ["ja", "yes", "y"]:
            response = {
                "action": "sign_up_intent",
                "reply": "Great! Let me get you set up. What's your business name?"
            }

        elif message_lower in ["info", "more", "meer"]:
            response = {
                "action": "send_info",
                "reply": self.templates["afrikaans"]["outreach"]
            }

        elif message_lower in ["demo"]:
            response = {
                "action": "send_demo",
                "reply": "I'll prepare a demo pack for you!"
            }

        elif message_lower in ["help", "hulp"]:
            response = {
                "action": "help",
                "reply": "I can help you with:\n- Demo pack\n- Pricing info\n- Sign up\n\nJust ask!"
            }

        else:
            response = {
                "action": "forward_to_human",
                "reply": "Thank you for your message! Someone will respond shortly. 😊"
            }

        # Send auto-reply if configured
        if response and self.use_twilio:
            self.send_message(from_phone, response["reply"])

        return response

    def get_message_status(self, message_sid: str) -> Dict:
        """Get status of sent message"""
        if not self.use_twilio:
            return {"status": "simulated"}

        try:
            message = self.twilio_client.messages(message_sid).fetch()
            return {
                "sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return {"error": str(e)}

    def send_bulk_messages(self, recipients: list, message: str) -> Dict:
        """Send same message to multiple recipients"""
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "details": []
        }

        for phone in recipients:
            try:
                result = self.send_message(phone, message)
                if result["status"] in ["sent", "simulated"]:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                results["details"].append(result)
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "phone": phone,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def create_whatsapp_webhook(self) -> Dict:
        """
        Create webhook configuration for receiving messages

        Returns instructions for setting up webhook in Twilio console
        """
        return {
            "webhook_url": "https://your-domain.com/api/whatsapp/webhook",
            "method": "POST",
            "instructions": [
                "1. Go to Twilio Console > Messaging > Settings > WhatsApp sandbox",
                "2. Set 'WHEN A MESSAGE COMES IN' to your webhook URL",
                "3. Set HTTP method to POST",
                "4. Save configuration",
                "5. Test by sending a message to your WhatsApp number"
            ],
            "example_payload": {
                "From": "whatsapp:+27XXXXXXXXX",
                "Body": "Hello",
                "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        }
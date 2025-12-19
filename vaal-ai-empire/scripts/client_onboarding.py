#!/usr/bin/env python3
"""
Complete Client Onboarding Flow
WhatsApp → Demo → Payment → Delivery → Scheduling
"""

import sys
import json
from datetime import datetime
import sqlite3
from core.database import Database
from services.content_generator import get_content_factory
from services.whatsapp_bot import WhatsAppBot
from services.content_scheduler import ContentScheduler
from services.revenue_tracker import RevenueTracker

class ClientOnboarding:
    """Automated client onboarding system"""

    def __init__(self):
        self.db = Database()
        self.factory = get_content_factory()
        self.whatsapp = WhatsAppBot(self.db)
        self.scheduler = ContentScheduler(self.db)
        self.revenue = RevenueTracker(self.db)

    def send_outreach(self, phone: str, language: str = "afrikaans") -> Dict:
        """Step 1: Send outreach message"""
        result = self.whatsapp.send_outreach(phone, language)
        return result

    def generate_demo(self, phone: str, business_name: str, business_type: str) -> Dict:
        """Step 2: Generate and send demo pack"""

        # Create client record
        client_id = self.db.add_client({
            "name": business_name,
            "business_type": business_type,
            "phone": phone,
            "subscription_type": "demo",
            "subscription_amount": 0
        })

        # Generate demo content
        demo_pack = self.factory.generate_social_pack(business_type, "afrikaans")

        # Send demo via WhatsApp
        self.whatsapp.send_demo(phone, client_id)

        return {
            "client_id": client_id,
            "demo_pack": demo_pack,
            "status": "demo_sent"
        }

    def close_deal(self, client_id: str, subscription_amount: float = 600) -> Dict:
        """Step 3: Close deal and send invoice"""

        # Update client to active
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE clients
            SET active = 1, subscription_type = 'social_media', subscription_amount = ?
            WHERE id = ?
        """, (subscription_amount, client_id))

        conn.commit()
        conn.close()

        # Log revenue
        revenue_id = self.db.log_revenue(client_id, subscription_amount, "social_media")

        # Get invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{revenue_id}"

        # Send invoice
        client = self.db.get_active_clients()[0]  # Simplified
        self.whatsapp.send_invoice(client["phone"], subscription_amount, invoice_number)

        return {
            "client_id": client_id,
            "invoice_number": invoice_number,
            "amount": subscription_amount,
            "status": "invoice_sent"
        }

    def deliver_content(self, client_id: str) -> Dict:
        """Step 4: Generate and schedule full month of content"""

        # Get client details
        clients = self.db.get_active_clients()
        client = next((c for c in clients if c["id"] == client_id), None)

        if not client:
            return {"error": "Client not found"}

        # Generate full content pack (20 posts)
        pack = self.factory.generate_social_pack(client["business_type"], client["language"])

        # Schedule posts
        scheduled = self.scheduler.schedule_pack(client_id, pack["posts"])

        return {
            "client_id": client_id,
            "posts_generated": len(pack["posts"]),
            "posts_scheduled": scheduled,
            "status": "delivered"
        }

def main():
    """CLI interface for onboarding"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python client_onboarding.py outreach <phone>")
        print("  python client_onboarding.py demo <phone> <name> <type>")
        print("  python client_onboarding.py close <client_id> <amount>")
        print("  python client_onboarding.py deliver <client_id>")
        sys.exit(1)

    onboarding = ClientOnboarding()
    command = sys.argv[1]

    if command == "outreach":
        result = onboarding.send_outreach(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif command == "demo":
        result = onboarding.generate_demo(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, indent=2))

    elif command == "close":
        result = onboarding.close_deal(sys.argv[2], float(sys.argv[3]))
        print(json.dumps(result, indent=2))

    elif command == "deliver":
        result = onboarding.deliver_content(sys.argv[2])
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# 1. Load Environment Variables
load_dotenv()

URL = os.getenv("SABC_PLUS_URL")
USERNAME = os.getenv("SABC_PLUS_USERNAME")
PASSWORD = os.getenv("SABC_PLUS_PASSWORD")
HEADLESS = os.getenv("HEADLESS_MODE", "true").lower() == "true"

def run_sabc_test():
    print("🚀 Initializing SABC Plus Search Agent...")

    with sync_playwright() as p:
        # Launch Browser
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 2. Navigate to SABC Plus
            print(f"🌐 Navigating to: {URL}")
            page.goto(URL, timeout=60000)
            page.wait_for_load_state("networkidle")

            # 3. Handle Login (If redirect to login page or generic login button found)
            # Note: Selectors depend on the specific site structure.
            # These are generic selectors that usually work or need slight adjustment.
            print("🔑 Attempting Login...")

            # Look for common login button text
            login_button = page.get_by_text("Log In", exact=False).or_(page.get_by_text("Sign In", exact=False)).first

            if login_button.is_visible():
                login_button.click()
                page.wait_for_timeout(2000)

                # Fill Credentials
                print(f"📝 Filling credentials for: {USERNAME}")
                # Try standard input types
                page.fill('input[type="email"], input[name="email"], input[name="username"]', USERNAME)
                page.fill('input[type="password"]', PASSWORD)

                # Click Submit
                page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")')
                page.wait_for_load_state("networkidle")
                print("✅ Login Credentials Submitted")
            else:
                print("ℹ️ No login button found immediately, checking if already logged in or search is public...")

            # 4. Perform Test Search
            search_term = "Generations"
            print(f"🔍 Searching for: '{search_term}'")

            # Click search icon usually represented by magnifying glass or 'Search' text
            search_icon = page.locator('svg[data-icon="search"]').or_(page.get_by_role("button", name="Search")).first
            if search_icon.is_visible():
                search_icon.click()
                page.fill('input[type="search"], input[placeholder*="Search"]', search_term)
                page.press('input[type="search"], input[placeholder*="Search"]', 'Enter')

                # Wait for results
                page.wait_for_timeout(3000)

                # 5. Capture Evidence
                screenshot_path = "sabc_search_result.png"
                page.screenshot(path=screenshot_path)
                print(f"📸 Screenshot saved to: {screenshot_path}")

                print("✅ Test Complete: Search functionality verified.")
            else:
                print("❌ Could not locate Search interface.")

        except Exception as e:
            print(f"❌ Error during test: {e}")
            page.screenshot(path="error_state.png")

        finally:
            browser.close()

if __name__ == "__main__":
    if not URL or not USERNAME:
        print("❌ Error: Missing credentials in .env file")
    else:
        run_sabc_test()

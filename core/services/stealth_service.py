import os
import random
import time

from django.conf import settings
from playwright.sync_api import sync_playwright


STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter(parameter);
    };
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ? Promise.resolve({ state: 'denied' }) : originalQuery(parameters)
    );
"""


class StealthBrowserService:
    def _human_type(self, page, selector, text):
        """
        Simulates human typing behavior with random delays between keystrokes.
        """

        page.click(selector)
        for char in text:
            page.keyboard.type(char)
            time.sleep(random.uniform(0.05, 0.15))

    def run_ecommerce_test(self, search_item="iphone 15 case"):
        """
        Executes the full e-commerce flow: Search -> Select -> Screenshot.
        """

        # Load proxy configuration from environment variables
        PROXY_SERVER = os.getenv("PROXY_SERVER")
        PROXY_USER = os.getenv("PROXY_USER")
        PROXY_PASS = os.getenv("PROXY_PASS")

        proxy_config = None
        if PROXY_SERVER:
            print(f"Proxy configuration detected: {PROXY_SERVER}")
            proxy_config = {"server": PROXY_SERVER}
            if PROXY_USER and PROXY_PASS:
                proxy_config["username"] = PROXY_USER
                proxy_config["password"] = PROXY_PASS
        else:
            print("WARNING: Running without proxy. High risk of blocking.")

        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--start-maximized",
            "--disable-infobars",
        ]

        media_root = getattr(settings, "MEDIA_ROOT", "media")
        if not os.path.isabs(media_root):
            media_root = os.path.abspath(media_root)
        os.makedirs(media_root, exist_ok=True)
        screenshot_path = os.path.join(media_root, "amazon_test.png")

        try:
            with sync_playwright() as p:
                print("Initializing browser session...")

                browser = p.chromium.launch(
                    headless=False, args=args, proxy=proxy_config, slow_mo=50
                )

                context = browser.new_context(
                    viewport={"width": 1366, "height": 768},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    locale="pt-BR",
                    timezone_id="America/Sao_Paulo",
                )

                context.add_init_script(STEALTH_JS)

                page = context.new_page()

                print("Navigating to Amazon...")
                page.goto("https://www.amazon.com.br/", timeout=60000)

                page.wait_for_selector('input[name="field-keywords"]', timeout=30000)

                if "Robot Check" in page.title():
                    print("BLOCKED: Amazon Captcha detected on entry.")
                    return {"status": "blocked", "message": "Captcha detected"}

                print(f"Searching for: {search_item}")
                self._human_type(page, 'input[name="field-keywords"]', search_item)

                time.sleep(random.uniform(0.5, 1.2))
                page.keyboard.press("Enter")

                print("Selecting product from results...")
                selector_product = 'div[data-component-type="s-search-result"] h2 a'
                page.wait_for_selector(selector_product, timeout=30000)

                first_product = page.locator(selector_product).first

                first_product.hover()
                time.sleep(random.uniform(0.3, 0.7))
                first_product.click()

                print("Capturing product screenshot...")

                page.wait_for_selector("#productTitle", timeout=30000)
                page.screenshot(path=screenshot_path)

                print("Test completed successfully.")
                time.sleep(2)
                browser.close()

                return {"status": "success", "file": screenshot_path}

        except Exception as e:
            print(f"Error executing browser task: {e}")
            return {"status": "error", "message": str(e)}

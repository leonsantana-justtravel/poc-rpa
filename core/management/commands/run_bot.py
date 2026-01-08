import os
import time

from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright


# --- STEALTH JAVASCRIPT PAYLOAD ---
# This script manually overrides browser properties to hide automation indicators
STEALTH_JS = """
    // 1. Remove the 'webdriver' flag that identifies robots
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    
    // 2. Mock the Chrome runtime object (missing in standard Playwright)
    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
    
    // 3. Mock the Plugins list (bots usually have empty lists)
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    
    // 4. Mock WebGL Vendor/Renderer to simulate an Intel GPU instead of a server GPU
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter(parameter);
    };
    
    // 5. Override Notification Permissions to simulate human behavior ('denied' or 'prompt')
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ? Promise.resolve({ state: 'denied' }) : originalQuery(parameters)
    );
"""


class Command(BaseCommand):
    help = "Executes the Amazon RPA Bot using Playwright with advanced stealth techniques and proxy support."

    def handle(self, *args, **options):
        # Load proxy credentials from environment variables (.env file)
        PROXY_SERVER = os.getenv("PROXY_SERVER")
        PROXY_USER = os.getenv("PROXY_USER")
        PROXY_PASS = os.getenv("PROXY_PASS")

        proxy_config = None

        # Configure proxy dictionary if server is defined
        if PROXY_SERVER:
            self.stdout.write(f"Usando Proxy: {PROXY_SERVER}")
            proxy_config = {"server": PROXY_SERVER}
            if PROXY_USER and PROXY_PASS:
                proxy_config["username"] = PROXY_USER
                proxy_config["password"] = PROXY_PASS
        else:
            self.stdout.write(
                self.style.WARNING(
                    "ATENCAO: Rodando SEM PROXY. Risco alto de bloqueio."
                )
            )

        with sync_playwright() as p:
            self.stdout.write("Iniciando sessao do Bot...")

            # Launch Browser
            # headless=False is required for Xvfb compatibility on Linux servers
            browser = p.chromium.launch(
                headless=False,
                slow_mo=300,
                proxy=proxy_config,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

            # Create Browser Context
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )

            # Inject the stealth script before page load
            context.add_init_script(STEALTH_JS)

            page = context.new_page()

            try:
                self.stdout.write("Acessando Amazon...")
                page.goto("https://www.amazon.com.br", timeout=60000)

                # Security Check: Detect if Amazon blocked the IP or presented a CAPTCHA
                if (
                    "Robot Check" in page.title()
                    or page.locator("input#captchacharacters").count() > 0
                ):
                    self.stdout.write(
                        self.style.ERROR(
                            "BLOQUEADO: Amazon detectou o IP ou o Proxy e de baixa qualidade."
                        )
                    )
                    page.screenshot(path="debug_block.png")
                    return

                self.stdout.write("Buscando produto...")
                page.fill("#twotabsearchtextbox", "playstation 5")
                time.sleep(1)
                page.keyboard.press("Enter")

                self.stdout.write("Selecionando produto...")
                page.wait_for_selector(
                    "div[data-component-type='s-search-result']", timeout=30000
                )
                # Click on the image of the first result
                page.locator(
                    "div[data-component-type='s-search-result'] .s-image"
                ).first.click()

                self.stdout.write("Adicionando ao carrinho...")
                page.wait_for_selector("#add-to-cart-button", timeout=15000)
                page.click("#add-to-cart-button", force=True)

                self.stdout.write("Indo para o Checkout...")
                time.sleep(3)

                # Handle potential upsell modals
                if page.is_visible("#attachSiNoCoverage"):
                    page.click("#attachSiNoCoverage")
                elif page.is_visible("button[id*='siNoCoverage']"):
                    page.click("button[id*='siNoCoverage']")

                # Direct navigation to Cart URL to avoid popup traps
                page.goto("https://www.amazon.com.br/gp/cart/view.html?ref_=nav_cart")

                # Click on 'Proceed to Checkout'
                if page.is_visible("input[name='proceedToRetailCheckout']"):
                    page.click("input[name='proceedToRetailCheckout']")
                    self.stdout.write(
                        self.style.SUCCESS("SUCESSO: Tela de login alcancada!")
                    )
                    page.screenshot(path="sucesso_login.png")
                else:
                    self.stdout.write(
                        self.style.ERROR("Botao de checkout nao encontrado.")
                    )
                    page.screenshot(path="erro_layout.png")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro fatal: {str(e)}"))
                try:
                    page.screenshot(path="erro_fatal.png")
                except:  # noqa: E722, S110
                    pass
            finally:
                self.stdout.write("Encerrando sessao...")
                time.sleep(2)
                browser.close()

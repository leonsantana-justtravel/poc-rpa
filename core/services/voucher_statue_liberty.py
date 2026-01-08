import logging
import os
import random
import re
import time
from datetime import datetime

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.mail import send_mail
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    expect,
    sync_playwright,
)

# Configuração de Logger
logger = logging.getLogger(__name__)

# --- STEALTH PAYLOAD LEVE ---
STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    if (window.navigator.permissions) {
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ? Promise.resolve({ state: 'denied' }) : originalQuery(parameters)
        );
    }
"""

class VoucherStatueLibertyService:
    def __init__(self):
        self.proxy_config = settings.PROXY_CONFIG
        if self.proxy_config:
            logger.info(f"🌐 Proxy configurado: {self.proxy_config['server']}")
        else:
            logger.warning("⚠️ Rodando SEM PROXY. Risco alto de bloqueio.")

    # --- MÉTODOS AUXILIARES ---

    def _get_iso_alpha2_code(self, country_name: str) -> str:
        """Retorna código ISO para o país (ex: Brazil -> BR)."""
        country_map = {
            "brazil": "BR",
            "brasil": "BR",
            "portugal": "PT",
            "united states": "US",
            "usa": "US",
            "uruguay": "UY",
            "argentina": "AR",
        }
        return country_map.get(country_name.lower().strip(), "US")

    def _format_brazilian_phone(self, phone_number: str) -> str:
        """Formata telefone BR: (XX) XXXXX-XXXX."""
        cleaned_phone = re.sub(r"\D", "", phone_number)
        if len(cleaned_phone) == 11:
            return f"({cleaned_phone[0:2]}) {cleaned_phone[2:7]}-{cleaned_phone[7:]}"
        elif len(cleaned_phone) == 10:
            return f"({cleaned_phone[0:2]}) {cleaned_phone[2:6]}-{cleaned_phone[6:]}"
        return phone_number

    def _calculate_age(self, birth_date_str, travel_date):
        born = datetime.strptime(birth_date_str, "%Y-%m-%d")
        return (
            travel_date.year
            - born.year
            - ((travel_date.month, travel_date.day) < (born.month, born.day))
        )

    def _calculate_ticket_counts(self, visitors, travel_date):
        counts = {"adults": 0, "seniors": 0, "children": 0}
        for visitor in visitors:
            age = self._calculate_age(visitor["birthDate"], travel_date)
            if age >= 62:
                counts["seniors"] += 1
            elif age >= 13:
                counts["adults"] += 1
            elif age >= 4:
                counts["children"] += 1
        return counts

    def _decrypt_payment_data(self):
        try:
            key = settings.DECRYPT_KEY
            if not key:
                return settings.PAYMENT_DETAILS
            cipher = Fernet(key)
            details = settings.PAYMENT_DETAILS
            return {
                "number": cipher.decrypt(details["CARD_NUMBER"].encode()).decode(),
                "cvc": cipher.decrypt(details["CARD_CVC"].encode()).decode(),
                "exp_month": details["CARD_EXP_MONTH"],
                "exp_year": details["CARD_EXP_YEAR"],
                "type": details["CARD_TYPE"],
            }
        except Exception:
            return settings.PAYMENT_DETAILS

    def _human_delay(self, min_s=0.5, max_s=1.5):
        time.sleep(random.uniform(min_s, max_s))

    def _send_availability_alert(self, contact_email, requested_date, requested_time, available_slots):
        logger.info(f"📧 Preparando e-mail de indisponibilidade para {contact_email}...")
        
        slots_str = "\n".join([f"- {slot}" for slot in available_slots]) if available_slots else "Nenhum horário identificado."
        
        subject = f"⚠️ Indisponibilidade: Estátua da Liberdade - {requested_date}"
        message = (
            f"Olá,\n\n"
            f"O horário solicitado ({requested_time}) não está disponível para o dia {requested_date}.\n\n"
            f"Horários identificados na tela:\n"
            f"{slots_str}\n\n"
            f"Atenciosamente,\n"
            f"Robô de Emissões"
        )
        
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@justtravel.com')
            send_mail(subject, message, from_email, [contact_email], fail_silently=False)
            logger.info("✅ E-mail de alerta enviado.")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar e-mail: {e}")

    # --- LÓGICA DE PREENCHIMENTO REORDENADA ---
    def _fill_buyer_data(self, page, target_container, buyer):
        logger.info("📝 Preenchendo dados do comprador...")
        
        # 1. Anti-Modal Guest
        guest_selector = 'button:has-text("Guest"), button:has-text("Convidado"), [data-testid="guest-checkout-button"]'
        try:
            if page.locator(guest_selector).first.is_visible(timeout=3000):
                page.locator(guest_selector).first.click()
            elif target_container.locator(guest_selector).first.is_visible(timeout=3000):
                target_container.locator(guest_selector).first.click()
            self._human_delay(1, 2)
        except:
            pass

        try:
            # --- EMAIL (Etapa 1) ---
            email_input = target_container.locator('input[name="email"]')
            email_input.wait_for(state="visible", timeout=30000)
            email_input.fill(buyer["email"])
            self._human_delay(0.5, 1.0)
            
            continue_btn = target_container.get_by_role("button", name="Continue")
            if continue_btn.is_visible():
                continue_btn.click()
                self._human_delay(2.0, 3.0)

            # --- DADOS PESSOAIS ---
            target_container.locator('input[name="firstName"]').fill(buyer["firstName"])
            target_container.locator('input[name="lastName"]').fill(buyer["lastName"])
            
            # --- MUDANÇA CRUCIAL: PAÍS PRIMEIRO! ---
            # Selecionar o país costuma corrigir a bandeira do telefone automaticamente
            logger.info(f"Selecionando país: {buyer['country']}")
            try:
                country_select = target_container.locator('select[name="country"]')
                country_select.select_option(label=buyer["country"])
                # Espera o site "pensar" e mudar os campos
                self._human_delay(3.0, 4.0) 
            except Exception as e:
                logger.warning(f"Erro ao selecionar país: {e}")

            # --- TELEFONE ---
            # Agora tentamos ajustar o telefone. Se a bandeira falhar, seguimos em frente.
            iso_code = self._get_iso_alpha2_code(buyer["country"])
            
            if iso_code == "BR":
                logger.info("Tentando ajustar bandeira para BR (se necessário)...")
                try:
                    # Verifica se já não está BR (pela seleção do país)
                    flag_container = target_container.locator(".iti__selected-flag")
                    if flag_container.is_visible():
                        # Clica com timeout curto, se falhar não trava o robô
                        flag_container.click(timeout=3000)
                        self._human_delay(0.5, 1.0)
                        
                        br_opt = target_container.locator('li[data-country-code="br"]').first
                        if br_opt.is_visible():
                            br_opt.click()
                        else:
                            # Tenta texto
                            target_container.locator('li span:has-text("Brazil")').first.click()
                        self._human_delay(0.5, 1.0)
                except Exception as e:
                    # Apenas loga o aviso, mas NÃO PARA o robô. 
                    # Talvez a seleção do país já tenha resolvido.
                    logger.warning(f"⚠️ Aviso: Não foi possível clicar na bandeira ({e}). Tentando digitar direto.")

            # Preenche o telefone formatado
            raw_phone = buyer["phone"]
            if iso_code == "BR":
                formatted_phone = self._format_brazilian_phone(raw_phone)
                target_container.locator('input[name="phone"]').fill(formatted_phone)
            else:
                target_container.locator('input[name="phone"]').fill(raw_phone)

            self._human_delay(0.5, 1.0)

            # --- ENDEREÇO & ESTADO ---
            target_container.locator('input[name="address"]').fill(buyer["address"])
            target_container.locator('input[name="city"]').fill(buyer["city"])
            
            if buyer.get("state"):
                logger.info(f"Preenchendo estado: {buyer['state']}")
                state_filled = False
                
                # Lista de seletores possíveis
                state_locators = [
                    'select[name="state"]', 'select[name="province"]',
                    'input[name="state"]', 'input[name="province"]'
                ]
                
                for selector in state_locators:
                    try:
                        el = target_container.locator(selector).first
                        if el.is_visible(timeout=1000): # Check rápido
                            tag_name = el.evaluate("el => el.tagName")
                            if tag_name == "SELECT":
                                try:
                                    el.select_option(label=buyer["state"])
                                except:
                                    el.select_option(value=buyer["state"])
                            else:
                                el.fill(buyer["state"])
                            state_filled = True
                            break
                    except:
                        continue
                
                if not state_filled:
                    # Fallback TAB (força o cursor a ir para o próximo campo)
                    target_container.locator('input[name="city"]').press("Tab")
                    page.keyboard.type(buyer["state"])

            target_container.locator('input[name="postalCode"]').fill(buyer["zipCode"])

            # Termos
            target_container.locator("#checkoutTermsAndConditions").check()
            self._human_delay(1.0, 2.0)
            
            # CLIQUE FINAL
            final_btn = target_container.get_by_role("button", name="Continue to Payment")
            
            # Se desabilitado, clica fora para validar
            if not final_btn.is_enabled():
                target_container.locator("body").click()
                self._human_delay(1, 2)

            # Clica!
            final_btn.click()
            return target_container

        except Exception as e:
            logger.error(f"Erro no preenchimento: {e}")
            page.screenshot(path="debug_fill_error.png")
            raise

    def _process_payment(self, page, target_container):
        card_data = self._decrypt_payment_data()
        
        # Localiza o iframe do Chase
        if hasattr(target_container, "frame_locator"):
             payment_frame = target_container.frame_locator("iframe#chaseHostedPayment")
        else:
             payment_frame = target_container.frame_locator("iframe#chaseHostedPayment")

        logger.info("💳 Preenchendo Cartão de Crédito...")
        try:
            payment_frame.locator("#ccNumber").wait_for(state="visible", timeout=45000)
            payment_frame.locator("#ccNumber").fill(card_data["number"] or "")
            self._human_delay(0.3, 0.6)
            payment_frame.locator("#CVV2").fill(card_data["cvc"] or "")
            payment_frame.locator("#expMonth").select_option(card_data["exp_month"] or "01")
            payment_frame.locator("#expYear").select_option(card_data["exp_year"] or "2028")
            
            self._human_delay(1.0, 2.0)
            logger.info("🛑 PAGAMENTO PREENCHIDO (Clique final desativado para segurança em teste)")
            # btn = payment_frame.get_by_role("button", name="Complete")
            # btn.click()
        except Exception as e:
            logger.error(f"Erro no pagamento: {e}")
            page.screenshot(path="debug_payment_error.png")
            raise

    def execute(self, order_data):
        travel_date = datetime.strptime(order_data["travelDate"], "%Y-%m-%d")
        ticket_counts = self._calculate_ticket_counts(order_data["visitors"], travel_date)

        with sync_playwright() as p:
            logger.info("🚀 Iniciando Navegador (Stealth Nativo)...")

            args = [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--start-maximized',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
            ]

            browser = p.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                proxy=self.proxy_config,
                slow_mo=50,
                args=args,
            )

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="America/New_York",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            context.add_init_script(STEALTH_JS)
            page = context.new_page()

            try:
                logger.info("Acessando site...")
                y, m, d = order_data["travelDate"].split("-")
                direct_url = f"https://www.cityexperiences.com/new-york/city-cruises/statue/new-york-reserve/?date={m}/{d}/{y}&openSdk=1"
                
                logger.info(f"Navegando direto para a data: {direct_url}")
                page.goto(direct_url, timeout=90000, wait_until="domcontentloaded")
                
                try:
                    page.get_by_role("button", name="Cookies Settings").click(timeout=8000)
                    self._human_delay(0.5, 1)
                    page.get_by_role("button", name="Confirm My Choices").click()
                except:
                    pass

                self._human_delay(3, 5)

                # --- SELEÇÃO DE HORÁRIO ---
                frame_loc = page.frame_locator('iframe[title="hb_commerce"]').first
                time_slot = order_data["timeSlot"]
                
                logger.info(f"⏳ Aguardando carregamento dos horários no iframe...")
                try:
                    frame_loc.locator("button", has_text=re.compile(r"AM|PM")).first.wait_for(timeout=25000)
                except:
                    logger.warning("Timeout esperando lista de horários. Tentando seguir...")

                logger.info(f"Procurando horário: '{time_slot}'")
                slot_btn = frame_loc.locator("button", has_text=time_slot).first
                
                if slot_btn.is_visible():
                    logger.info(f"✅ Horário encontrado! Clicando...")
                    slot_btn.scroll_into_view_if_needed()
                    self._human_delay(0.5, 1)
                    slot_btn.click(force=True)
                else:
                    logger.warning(f"⚠️ Horário '{time_slot}' não visível. Analisando opções...")
                    try:
                        all_btns = frame_loc.locator("button").all()
                        visible_texts = sorted(list(set([b.text_content().strip() for b in all_btns if b.text_content() and ("AM" in b.text_content() or "PM" in b.text_content()) and "Buy" not in b.text_content()])))
                        self._send_availability_alert(order_data["buyer"]["email"], order_data["travelDate"], time_slot, visible_texts)
                        return {"status": "error", "message": f"Horário {time_slot} indisponível. Alternativas enviadas."}
                    except Exception as scrape_error:
                        return {"status": "error", "message": "Falha crítica na detecção de horários."}

                self._human_delay(2, 3)

                # Quantidades
                for type_key, count in ticket_counts.items():
                    if count > 0:
                        labels = {
                            "adults": "Adult General Admission",
                            "seniors": "Senior General Admission",
                            "children": "Child General Admission",
                        }
                        logger.info(f"Adicionando {count} ingressos para {type_key}")
                        row = frame_loc.locator(f"li:has-text('{labels[type_key]}')")
                        inc_button = row.locator("button").last 
                        inc_button.click(click_count=count)
                        self._human_delay(0.5, 1.0)

                # --- TRANSIÇÃO ---
                logger.info("🔄 Clicando em Comprar...")
                try:
                    buy_btn = frame_loc.get_by_role("button", name="Buy Now")
                    buy_btn.scroll_into_view_if_needed()
                    buy_btn.click() 
                except:
                    pass

                checkout_reached = False
                target_container = None
                
                for i in range(15):
                    logger.info(f"⏳ Aguardando checkout... ({i+1}/15)")
                    page.wait_for_timeout(2000)
                    
                    if "checkout" in page.url:
                        checkout_reached = True
                        break
                    
                    try:
                        if frame_loc.locator('input[name="email"]').is_visible(timeout=500) or \
                           page.locator('input[name="email"]').is_visible(timeout=500):
                            checkout_reached = True
                            break
                    except: pass

                if not checkout_reached:
                    logger.warning("⚠️ Forçando URL de checkout...")
                    page.goto("https://www.cityexperiences.com/new-york/city-cruises/statue/checkout/", wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)

                logger.info("✅ Iniciando preenchimento inteligente...")
                active_container = self._fill_buyer_data(page, page if page.locator('input[name="email"]').is_visible() else frame_loc, order_data["buyer"])

                logger.info("💳 Processando Pagamento...")
                self._process_payment(page, active_container)

                logger.info("✅ SUCESSO TOTAL!")
                screenshot_path = os.path.join(settings.MEDIA_ROOT, f"voucher_success_{int(time.time())}.png")
                page.screenshot(path=screenshot_path)

                return {"status": "success", "file": screenshot_path}

            except Exception as e:
                logger.error(f"❌ Erro: {str(e)}")
                try: page.screenshot(path="error_final.png")
                except: pass
                return {"status": "error", "message": str(e)}
            finally:
                try: browser.close()
                except: pass
import logging

from django.core.management.base import BaseCommand

from core.services.voucher_statue_liberty import VoucherStatueLibertyService


# Configuração básica de log para ver no terminal
logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = "Testa o fluxo RPA da Estátua da Liberdade com dados fictícios"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("🗽 Iniciando Teste da Estátua da Liberdade...")
        )

        # 1. Dados Fictícios (Mock) - Simulando o JSON que viria da API
        # IMPORTANTE: Coloque uma data futura válida!
        mock_order_data = {
            "orderId": "TEST-CMD-001",
            "ticketType": "General Admission",
            "travelDate": "2026-05-20",  # YYYY-MM-DD (Data futura)
            "departureLocation": "New York",  # ou "New Jersey"
            "timeSlot": "11:00 AM",  # Horário que costuma ter vaga
            "visitors": [
                {"name": "Leon Tester", "birthDate": "1990-01-01"},  # Adulto
                {"name": "Kid Tester", "birthDate": "2018-01-01"},  # Criança
            ],
            "buyer": {
                "firstName": "Leon",
                "lastName": "Developer",
                "email": "teste.rpa@example.com",
                "phone": "11999999999",
                "country": "Brazil",
                "address": "Av Paulista, 1000",
                "city": "Sao Paulo",
                "state": "SP",
                "zipCode": "01310-100",
            },
        }

        try:
            # 2. Instancia o Serviço (Já carrega Proxy e Stealth)
            service = VoucherStatueLibertyService()

            # 3. Executa
            result = service.execute(mock_order_data)

            # 4. Resultado
            if result["status"] == "success":
                self.stdout.write(
                    self.style.SUCCESS(f"✅ SUCESSO! Print salvo em: {result['file']}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ ERRO NO FLUXO: {result.get('message')}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"💥 Erro Fatal no Teste: {str(e)}"))

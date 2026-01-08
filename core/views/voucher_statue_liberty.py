import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import AvailabilityError, DecryptionError
from core.middleware.permissions import IsAuthorized

# Imports da nova estrutura do POC-RPA
from core.serializers.voucher_statue_liberty import VoucherStatueLibertySerializer
from core.services.voucher_statue_liberty import VoucherStatueLibertyService


# Configuração de Logs (Importante para produção)
logger = logging.getLogger(__name__)


class VoucherStatueLibertyView(APIView):
    """
    Endpoint para emissão de Vouchers da Estátua da Liberdade.
    Integração completa com:
    - Stealth Mode (Anti-bot)
    - Proxy Rotativo
    - Validação de Dados
    """

    # Define que só quem tem a X-Api-Key pode acessar
    permission_classes = [IsAuthorized]

    def post(self, request):
        logger.info("Recebendo requisição POST para Statue Liberty...")

        # 1. Validação dos dados de entrada (JSON)
        serializer = VoucherStatueLibertySerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Dados inválidos recebidos: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Pegamos os dados validados
        order_data = serializer.validated_data

        # ------------------------------------------------------------------
        # AJUSTE TÉCNICO: Conversão de Data
        # O Service espera string "YYYY-MM-DD" para preencher no site,
        # mas o Serializer entrega objeto python date(). Convertemos aqui:
        # ------------------------------------------------------------------
        order_data["travelDate"] = order_data["travelDate"].strftime("%Y-%m-%d")
        for visitor in order_data["visitors"]:
            visitor["birthDate"] = visitor["birthDate"].strftime("%Y-%m-%d")

        try:
            # 2. Instancia o Serviço (Aqui o Stealth e Proxy são ativados no __init__)
            service = VoucherStatueLibertyService()

            # 3. Executa o Robô
            logger.info(f"Iniciando robô para pedido: {order_data.get('orderId')}")
            result = service.execute(order_data)

            # 4. Retorna o Resultado
            if result["status"] == "success":
                return Response(
                    {"status": "success", "details": result}, status=status.HTTP_200_OK
                )
            # Se o robô retornou erro controlado
            return Response(
                {"status": "error", "details": result},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except AvailabilityError as e:
            # Erro específico de negócio (Ingressos esgotados)
            logger.error(f"Indisponibilidade: {str(e)}")
            return Response(
                {"error": str(e), "code": "tickets_unavailable"},
                status=status.HTTP_409_CONFLICT,
            )

        except DecryptionError as e:
            # Erro de configuração de chaves/segurança
            logger.critical(f"Erro de Descriptografia: {str(e)}")
            return Response(
                {"error": "Erro interno de configuração de segurança."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            # Erro genérico (Crash do robô, Timeout, etc)
            logger.exception("Erro fatal não tratado na View.")
            return Response(
                {"error": f"Internal Server Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

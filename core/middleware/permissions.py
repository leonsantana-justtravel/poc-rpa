from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAuthorized(BasePermission):
    """
    Permissão personalizada para verificar a X-Api-Key no cabeçalho.
    """

    def has_permission(self, request, view):  # noqa: ARG002
        # Obtém a chave enviada no Header da requisição
        api_key_sent = request.headers.get("X-Api-Key")

        # Compara com a chave definida no settings.py (que vem do .env)
        if not api_key_sent or api_key_sent != settings.API_KEY:
            return False
        return True

from rest_framework.exceptions import APIException


class ServiceUnavailableError(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = "service_unavailable"


class AvailabilityError(APIException):
    """Erro quando não há ingressos disponíveis para a data."""

    status_code = 400
    default_detail = "Tickets are not available for the selected date/time."
    default_code = "availability_error"


class DecryptionError(APIException):
    """Erro ao tentar descriptografar dados sensíveis."""

    status_code = 500
    default_detail = "Failed to decrypt sensitive data."
    default_code = "decryption_error"

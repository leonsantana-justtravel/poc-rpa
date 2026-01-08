from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.stealth_service import StealthBrowserService


class TriggerRPAView(APIView):
    def post(self, request):  # noqa: ARG002
        service = StealthBrowserService()

        result = service.run_bot_check()

        if result["status"] == "success":
            return Response(result, status=200)
        else:  # noqa: RET505
            return Response(result, status=500)

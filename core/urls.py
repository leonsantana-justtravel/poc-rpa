from django.urls import path

from core.views.rpa_views import TriggerRPAView  # noqa: F401
from core.views.voucher_statue_liberty import VoucherStatueLibertyView


urlpatterns = [
    path("voucher/statue-liberty/", VoucherStatueLibertyView.as_view()),
]

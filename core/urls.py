from django.urls import path

from core.views.rpa_views import TriggerRPAView


urlpatterns = [
    path("rpa/test/", TriggerRPAView.as_view(), name="rpa-test"),
]

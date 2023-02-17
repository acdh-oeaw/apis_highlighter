from django.conf import settings
from django.urls import path

app_name = "apis_highlighter"

urlpatterns = []

if 'annotator agreement' in getattr(settings, "APIS_COMPONENTS", []):
    from apis_highlighter.views import ComputeAgreement
    urlpatterns.append(path(r'^agreement/$', ComputeAgreement.as_view(), name='agreement'))

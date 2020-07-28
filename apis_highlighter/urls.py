from django.conf import settings
from django.conf.urls import url

app_name = "apis_highlighter"

urlpatterns = []

if 'annotator agreement' in getattr(settings, "APIS_COMPONENTS", []):
    from apis_highlighter.views import ComputeAgreement
    urlpatterns.append(url(r'^agreement/$', ComputeAgreement.as_view(), name='agreement'))

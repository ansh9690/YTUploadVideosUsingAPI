from django.urls import path
from .views import AuthorizeView, Oauth2CallbackView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('authorize/', AuthorizeView.as_view(), name="authorize"),
    path('oauth2callback/', Oauth2CallbackView.as_view(), name='oauth2callback'),
    path('', views.home, name='home')
]
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

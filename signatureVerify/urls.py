
from django.urls import path
from.import views
urlpatterns = [
    path('api/signatureVerify', views.signatureVerify, name='signatureVerify'),
]
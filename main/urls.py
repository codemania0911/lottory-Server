
from django.urls import path
from.import views
urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('', views.home, name='home'),

    path('lotteryocr', views.lotteryocr, name='lotteryocr'),
    path('api/lotteryocrApi', views.lotteryocrApi, name='lotteryocrApi'),
    path('api/lotteryocrnumberApi', views.lotteryocrnumberApi, name='lotteryocrnumberApi'),
    
]

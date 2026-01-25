from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/chat/', views.chat, name='chat'),
    path('api/save/', views.save_code, name='save_code'),
    path('api/execute/', views.execute_code, name='execute_code'),
]

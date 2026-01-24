"""
URL configuration for selfbuilding_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from editor import views as editor_views

# API endpoints without language prefix (fixes 302 redirect issue)
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/chat/', editor_views.chat, name='chat'),
    path('api/save/', editor_views.save_code, name='save_code'),
    path('api/execute/', editor_views.execute_code, name='execute_code'),
]

# Language-prefixed URLs
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', editor_views.index, name='index'),
)

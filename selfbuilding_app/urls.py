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
    # Phase 5: Authentication endpoints (without language prefix)
    path('accounts/login/', editor_views.login_view, name='login'),
    path('accounts/logout/', editor_views.logout_view, name='logout'),
    path('accounts/register/', editor_views.register_view, name='register'),
    # API endpoints
    path('api/chat/', editor_views.chat, name='chat'),
    path('api/save/', editor_views.save_code, name='save_code'),
    path('api/execute/', editor_views.execute_code, name='execute_code'),
    # Phase 4: Self-modification endpoints
    path('api/features/', editor_views.list_features, name='list_features'),
    path('api/features/analyze/', editor_views.analyze_feature, name='analyze_feature'),
    path('api/features/implement/', editor_views.implement_feature, name='implement_feature'),
    # Phase 4 Part 3: User approval workflow endpoints
    path('api/features/preview/', editor_views.preview_feature_changes, name='preview_feature_changes'),
    path('api/features/apply/', editor_views.apply_feature_changes, name='apply_feature_changes'),
    path('api/features/reject/', editor_views.reject_feature_changes, name='reject_feature_changes'),
    # Phase 5: Version control endpoints
    path('api/versions/', editor_views.get_version_history, name='get_version_history'),
    path('api/versions/switch/', editor_views.switch_version, name='switch_version'),
]

# Language-prefixed URLs
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', editor_views.index, name='index'),
)

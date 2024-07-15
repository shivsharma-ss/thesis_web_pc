"""
URL configuration for modbus_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path
from django.contrib.auth import views as auth_views
from modbus_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),  # Redirect to login by default
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change_server_settings/', views.change_server_settings, name='change_server_settings'),
    path('api/data/', views.api_data, name='api_data'),
    path('force_stop/', views.force_stop, name='force_stop'),
    path('continuous_tests/', views.continuous_tests, name='continuous_tests'),
    path('sse/', views.sse, name='sse'),
    path('tool_status_sse/', views.tool_status_sse, name='tool_status_sse'),
    path('update/<int:signal_id>/', views.update_signal, name='update_signal'),
    path('check_tool_connection/', views.check_tool_connection, name='check_tool_connection'),
]

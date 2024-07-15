# modbus_project/urls.py

from django.contrib import admin
from django.urls import path, include
from modbus_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('api/data', views.api_data, name='api_data'),
    path('sse/', views.sse, name='sse'),
    path('change_server_settings/', views.change_server_settings, name='change_server_settings'),
    path('force_stop/', views.force_stop, name='force_stop'),
    path('continuous_tests/', views.continuous_tests, name='continuous_tests'),
    path('check_tool_connection/', views.check_tool_connection, name='check_tool_connection'),
]
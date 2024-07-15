# modbus_app/backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
import modbus_project.config as config

class ConfigBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        config_username = config.DEFAULT_USERNAME
        config_password = config.DEFAULT_PASSWORD
        if username == config_username and password == config_password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user if not exists
                user = User(username=username)
                user.set_unusable_password()
                user.is_staff = True
                user.is_superuser = True
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

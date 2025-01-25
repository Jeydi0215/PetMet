# backends.py
from django.contrib.auth.backends import ModelBackend  # Import ModelBackend
from .models import Admin  # Import your Admin model

class AdminBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Admin.objects.get(username=username)
            if user.check_password(password):
                return user
        except Admin.DoesNotExist:
            return None
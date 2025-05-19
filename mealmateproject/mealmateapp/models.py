from django.db import models

# Create your models here.

class UserRegistration(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # For demo only! See note below.
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from datetime import date


class UserData(AbstractUser):
    username = None
    first_name = None
    last_name = None
    name = models.CharField(max_length=100, unique=False)
    email = models.EmailField(max_length=100, unique=True)
    otp=models.CharField(max_length=6,null=True,blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    is_active= models.BooleanField(default=False)

    def __str__(self):
        return str(self.email)


class Todo(models.Model):
    user = models.ForeignKey("UserData", on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    entry_date = models.DateField(default=date.today)
    due_date = models.DateField(default=date.today)
    status = models.BooleanField(default=False)

    def __str__(self):
        return str(self.title)

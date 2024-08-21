from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

class UserData(AbstractUser):
    username = None
    first_name = None
    last_name = None
    name = models.CharField(max_length=100, unique=False)
    email = models.EmailField(max_length=100, unique=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField()
    is_approved = models.BooleanField(default=True)
    def __str__(self):
        return str(self.email)

class Todo(models.Model):
    assigned_to = models.ForeignKey("UserData", related_name='assigned_tasks', on_delete=models.CASCADE)
    assigned_by = models.ForeignKey("UserData", related_name='created_tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    entry_date = models.DateField(default=date.today)
    due_date = models.DateField(default=date.today)
    status = models.BooleanField(default=False)
    image = models.ImageField(upload_to='todo_images/', null=True, blank=True)  # Add this line

    def __str__(self):
        return str(self.title)
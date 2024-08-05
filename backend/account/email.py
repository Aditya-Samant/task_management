# from datetime import datetime
from django.utils import timezone
from django.core.mail import send_mail
import random
from django.conf import settings
from .models import UserData

def send_otp_via_mail(Email):
    subject="Your email verification otp"
    otp=random.randint(100000,999999)
    message=f"Your opt is {otp} \n (otp will expire in 10 minutes)"
    email_from=settings.EMAIL_HOST
    send_mail(subject,message,email_from,[Email])
    user=UserData.objects.get(email=Email)
    user.otp=otp
    user.otp_created_at = timezone.now()
    user.save()



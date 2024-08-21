from django.urls import path,include
from account.views import *
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [
    path('account/register/', RegisterView.as_view(), name="sign_up"),
    path('account/register/verifyotp/', VerifyOTPView.as_view(), name="otp_verification"),
    path('account/register/resendotp/', ResendOtp.as_view(), name="resend_otp"),
    path('account/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('account/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('account/login/', MyTokenObtainPairViews.as_view(), name='token_obtain_pair'),
    path('account/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('todos/assign/', AssignTaskView.as_view(), name='assign_task'),
    path('todos/', EmployeeTaskView.as_view(), name='employee_tasks'),
    path('todos/<int:pk>/', EmployeeTaskView.as_view(), name='update_task'),
    path('employee/', ManagerEmployeeListView.as_view(), name='update_task'),
]


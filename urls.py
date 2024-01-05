from django.urls import path

from . import views

urlpatterns = [
    path('get-fee/', views.GetFeesAPIView.as_view()),
    path('create-bill-transaction/', views.CreateBillPaymentAPIView.as_view()),
    path('get-bill-categories/', views.GetBillCategoriesAPIView.as_view()),
    path('validate-bill-service/', views.ValidateBillServiceAPIView.as_view()),
    path('create-giftcard/', views.GiftCardCreateAPIView.as_view()),
    path('redeem-giftcard/', views.RedeemCreateAPIView.as_view()),
    path('transactions/', views.TransactionAPIView.as_view()),
]

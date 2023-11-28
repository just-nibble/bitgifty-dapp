from django.urls import path

from . import views

urlpatterns = [
    path('get-fee/', views.GetFeesAPIView.as_view()),
    path('create-bill-transaction/', views.CreateBillPaymentAPIView.as_view()),

    path('create-giftcard/', views.GiftCardCreateAPIView.as_view()),
    path('redeem-giftcard/', views.RedeemCreateAPIView.as_view()),
]

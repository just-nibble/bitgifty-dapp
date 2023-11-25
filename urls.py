from django.urls import path

from . import views

urlpatterns = [
    path('get-fee/', views.GetFeesAPIView.as_view()),
]

import os
import re
import secrets
import requests


from rest_framework import generics, exceptions, response

from core.utils import get_naira_price, get_rate, get_flw_headers, Blockchain, get_rate_buffer

from transactions.models import Transaction
from wallets.models import VirtualAccount

from rest_framework  import generics, permissions

from giftCards.models import GiftCardFee

from . import serializers, models
# Create your views here.


class GetFeesAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny,]
    queryset = GiftCardFee.objects.all()
    serializer_class = serializers.FeeSerializer
    filterset_fields = ['network',]


class CreateBillPaymentAPIView(generics.GenericAPIView):
    serializer_class = serializers.CreateBillPaymentSerializer

    def initiate_payment(
            self, bill_type: str, amount: int,
            customer: str, country: str
        ):
        url = "https://api.flutterwave.com/v3/bills"
        
        body = {
            "country": country,
            "customer": customer,
            "amount": amount,
            "type": bill_type,
            "reference": secrets.token_hex(7)
        }

        req = requests.post(
            url=url,
            json=body,
            headers=get_flw_headers()
        )

        resp = req.json()
        if resp.get('status') == 'error':
            raise ValueError(resp.get('message'))

        return resp

    def post(self, request, *args, **kwargs):
        serializer = serializers.CreateBillPaymentSerializer(data=self.request.data)
        
        if serializer.is_valid():
            country = serializer.validated_data['country']
            customer = serializer.validated_data['customer']
            bill_type = serializer.validated_data['bill_type']
            amount = serializer.validated_data['amount']
            chain = serializer.validated_data['chain']
            email = serializer.validated_data['email']
            wallet_address = serializer.validated_data['wallet_address']
            
            payment = self.initiate_payment(
                bill_type=bill_type,
                country=country,
                customer=customer,
                amount=amount,
            )

            transaction = Transaction(
                amount=amount,
                currency=chain,
                currency_type="crypto",
                status='pending',
                transaction_type=f"{bill_type} dapp",
                email=email,
                wallet_address=wallet_address
            )
            transaction.save()
            return response.Response(payment)
        else:
            raise ValueError("something went wrong")


class GiftCardCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny,]
    queryset = models.GiftCard.objects.all()
    serializer_class = serializers.GiftCardSerializer


class RedeemCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny,]
    queryset = models.Redeem.objects.all()
    serializer_class = serializers.RedeemSerializer

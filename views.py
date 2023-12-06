import os
import re
import secrets
import requests

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, exceptions, response, views

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

class GetBillCategoriesAPIView(views.APIView):
    permission_classes = [permissions.AllowAny,]
    bill_type = openapi.Parameter('bill-type', openapi.IN_QUERY, description="example: airtime, data_bundle", type=openapi.TYPE_STRING)
    provider = openapi.Parameter('provider', openapi.IN_QUERY, description="example: MTN, GLO, Airtel, 9Mobile", type=openapi.TYPE_STRING)
    
    response_schema_dict = {
        "201": openapi.Response(
            description="Htpp 201 description",
            examples={
            "status": "success",
            "message": "bill categories retrieval successful",
            "data": [
                {
                "id": 1,
                "biller_code": "BIL099",
                "name": "MTN NIgeria",
                "default_commission": 0.02,
                "date_added": "2018-07-03T00:00:00Z",
                "country": "NG",
                "is_airtime": True,
                "biller_name": "AIRTIME",
                "item_code": "AT099",
                "short_name": "MTN",
                "fee": 0,
                "commission_on_fee": False,
                "label_name": "Mobile Number",
                "amount": 0
            },
            {
                "id": 2,
                "biller_code": "BIL099",
                "name": "GLO Nigeria",
                "default_commission": 0.025,
                "date_added": "2018-07-03T00:00:00Z",
                "country": "NG",
                "is_airtime": True,
                "biller_name": "AIRTIME",
                "item_code": "AT099",
                "short_name": "GLO",
                "fee": 0,
                "commission_on_fee": False,
                "label_name": "Mobile Number",
                "amount": 0
            },
            {
                "id": 9,
                "biller_code": "BIL119",
                "name": "DSTV BoxOffice",
                "default_commission": 0.3,
                "date_added": "2018-08-17T00:00:00Z",
                "country": "NG",
                "is_airtime": False,
                "biller_name": "DSTV BOX OFFICE",
                "item_code": "CB140",
                "short_name": "Box Office",
                "fee": 100,
                "commission_on_fee": True,
                "label_name": "Smart Card Number",
                "amount": 0
            },
        ]
            }
        ),

        "500": openapi.Response(
            description="Htpp 500 description",
            examples={
                "application/json": {
                    "key_1": "error message 1",
                    "key_2": "error message 2",
                }
            }
        ),
    }

    def make_request(self, bill_type: str, provider: str):
        biller_code = {
            "MTN": "BIL099",
            "GLO": "BIL102",
            "Airtel": "BIL100",
            "9Mobile": "BIL103",
        }

        params = {
            bill_type: 1
        }

        if provider:
            params["biller_code"] = biller_code[provider]

        
        r = requests.get(
            url="https://api.flutterwave.com/v3/bill-categories",
            params=params,
            headers=get_flw_headers()
        )

        response = r.json()
        
        if response.get("status") != "success":
            raise ValueError("error getting bill category")
        return response

    @swagger_auto_schema(manual_parameters=[bill_type, provider], )
    def get(self, *args, **kwargs):     
        bill_type = self.request.query_params.get('bill-type')
        provider = self.request.query_params.get('provider')
        
        res = self.make_request(bill_type, provider)
        return response.Response(res)


class ValidateBillServiceAPIView(views.APIView):
    permission_classes = [permissions.AllowAny,]
    item_code = openapi.Parameter('item-code', openapi.IN_QUERY, description="get item code from get bill category", type=openapi.TYPE_STRING)
    
    def validate_bill(self, item_code: str):
        url = f"https://api.flutterwave.com/v3/bill-items/{item_code}/validate"
        req = requests.get(url=url, headers=get_flw_headers())
        resp = req.json()
        return resp

    @swagger_auto_schema(manual_parameters=[item_code], )
    def get(self, *args, **kwargs):
        item_code = self.request.query_params.get('item-code')
        validate = self.validate_bill(item_code)
        return response.Response(validate)
 

class CreateBillPaymentAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny,]
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
            
            try:
                payment = self.initiate_payment(
                    bill_type=bill_type,
                    country=country,
                    customer=customer,
                    amount=amount,
                )
            except Exception as exception:
                raise ValueError(exception)
            
            try:
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
            except Exception as exception:
                raise ValueError("Transaction failed to save")
            return response.Response(payment)
        else:
            raise exceptions.ValidationError("You aren't passing in a value correctly")


class GiftCardCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny,]
    queryset = models.GiftCard.objects.all()
    serializer_class = serializers.GiftCardSerializer


class RedeemCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny,]
    queryset = models.Redeem.objects.all()
    serializer_class = serializers.RedeemSerializer

from rest_framework import serializers


from giftCards.models import GiftCardFee
from .models import GiftCard, Redeem, Transaction



class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCardFee
        fields = "__all__"


class CreateBillPaymentSerializer(serializers.Serializer):
    bill_type = serializers.CharField()
    amount = serializers.IntegerField()
    customer = serializers.CharField()
    country = serializers.CharField()
    chain = serializers.CharField()
    email = serializers.EmailField(required=False)
    wallet_address = serializers.CharField()
    crypto_amount = serializers.FloatField()
    transaction_hash = serializers.CharField()

    class Meta:
        ref_name = 'create_bill_dap'



class GiftCardSerializer(serializers.ModelSerializer):
    class Meta:
        ref_name = 'giftcard_dap'
        model = GiftCard
        fields = "__all__"


class RedeemSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=False)
    class Meta:
        ref_name = 'redeem_dap'
        model = Redeem
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        ref_name = "dapp_transaction"

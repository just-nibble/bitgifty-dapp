from rest_framework import serializers


from giftCards.models import GiftCardFee



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
    email = serializers.EmailField()
    wallet_address = serializers.CharField()

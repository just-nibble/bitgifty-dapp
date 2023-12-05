import os

from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core import mail, exceptions

from core.utils import Blockchain

from giftCards.models import GiftCardImage, GiftCardFee
from wallets.models import AdminWallet

# Create your models here.

# Create Get Fee endpoint


class GiftCard(models.Model):
    address = models.CharField(max_length=255)
    currency = models.CharField(max_length=255)
    amount = models.FloatField(default=0.0)
    image = models.ForeignKey(GiftCardImage, on_delete=models.SET_NULL, null=True, related_name="dapp_image")
    sender_email = models.EmailField(null=True, blank=True)
    receipent_email = models.EmailField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, default="generated")
    creation_date = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.currency
    

    def save(self, *args, **kwargs):
        try:
            if self._state.adding:
                client = Blockchain(key=os.getenv('TATUM_API_KEY'))
                self.code = client.generate_code()
                if self.receipent_email:
                    subject = "Gift Card from BitGifty"
                    note = "You received a gift card from a friend"
                    if self.note:
                        note = self.note
                    html_message = render_to_string(
                        'giftcardtemplate_v2.html',
                        {   
                            'image': self.image.link,
                            'receipent_email': self.receipent_email,
                            'sender_email': self.sender_email,
                            'code': self.code,
                            'note': note,
                            'amount': self.amount,
                            'currency': self.currency,
                        }
                    )
                    
                    plain_message = strip_tags(html_message)
                    mail.send_mail(
                        subject, plain_message, "BitGifty <dev@bitgifty.com>",
                        [self.receipent_email], html_message=html_message
                    )
        except Exception as exception:
            raise exceptions.ValidationError(exception)
        return super(GiftCard, self).save(*args, **kwargs)
    

class Redeem(models.Model):
    address = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    redemption_date = models.DateTimeField(auto_now_add=True, null=True)

    def redeem_giftcard(self, code):
        try:
            giftcard = GiftCard.objects.get(code=code)
        except GiftCard.DoesNotExist:
            raise ValueError("gift card not found")
        
        if giftcard.status == "used":
            raise ValueError("Giftcard has already been used")

        try:
            fee = GiftCardFee.objects.get(network=giftcard.currency.title(), operation="redeem").amount
        except GiftCardFee.DoesNotExist:
            fee = 0.0

        TATUM_API_KEY = os.getenv("TATUM_API_KEY")
        client = Blockchain(TATUM_API_KEY, os.getenv("BIN_KEY"), os.getenv("BIN_SECRET"))
        admin_wallet = AdminWallet.objects.get(owner__username=f"{os.getenv('ADMIN_USERNAME')}", network=giftcard.currency.title())
        amount = str(float(giftcard.amount) - fee)
    
        return client.redeem_gift_card(
            code, admin_wallet.private_key, amount,
            self.address, giftcard.currency.lower(), admin_wallet.address
        )
    
    def save(self, *args, **kwargs):
        try:
            if self._state.adding:
                giftcard = GiftCard.objects.get(code=self.code)
                note = giftcard.note
                giftcard.status = "used"
                self.redeem_giftcard(self.code)
                giftcard.save()

                subject = "Gift Card Redeemed"
                html_message = render_to_string(
                    'giftcard_redeem_v2.html',
                    {
                        'receipent_email': giftcard.receipent_email,
                        'code': self.code,
                        'note': note,
                    }
                )
                    
                plain_message = strip_tags(html_message)
                mail.send_mail(
                    subject, plain_message, f"BitGifty <{os.getenv('ADMIN_EMAIL')}>",
                    [giftcard.receipent_email], html_message=html_message
                )
        except Exception as exception:
            raise exceptions.ValidationError(exception)
        return super(Redeem, self).save(*args, **kwargs)

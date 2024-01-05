import os

from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core import mail, exceptions

from core.utils import Blockchain

from giftCards.models import GiftCardImage, GiftCardFee
from wallets.models import AdminWallet, Wallet

from core.utils import Blockchain, get_flw_status


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
        network_mapping = {
            'celo': {
                "virt": "celo",
                "wallet": "celo",
            },
            "ceur": {
                "virt": "CEUR",
                "wallet": "celo",
            },
            "cusd": {
                "virt": "CUSD",
                "wallet": "celo",
            },
            "usdt_tron": {
                "virt": "USDT_TRON",
                "wallet": "tron"
            },
            "tron": {
                "virt": "TRON",
                "wallet": "tron"
            },
            "eth": {
                "virt": "ETH",
                "wallet": "ethereum"
            },
        }
        try:
            giftcard = GiftCard.objects.get(code=code)
        except GiftCard.DoesNotExist:
            raise ValueError("Giftcard not found")
        
        if giftcard.status == "used":
            raise ValueError("Giftcard has already been used")

        try:
            fee = GiftCardFee.objects.get(network=giftcard.currency.title(), operation="redeem").amount
        except GiftCardFee.DoesNotExist:
            fee = 0.0

        TATUM_API_KEY = os.getenv("TATUM_API_KEY")
        
        client = Blockchain(TATUM_API_KEY, os.getenv("BIN_KEY"), os.getenv("BIN_SECRET"))
        
        try:
            admin_wallet = AdminWallet.objects.get(
                owner__username=f"{os.getenv('ADMIN_USERNAME')}",
                network__icontains=network_mapping[giftcard.currency.lower()]["wallet"]
            )
        except AdminWallet.DoesNotExist:
            raise ValueError("Admin Wallet not found")
        
        amount = str(float(giftcard.amount) - fee)

        try:
            return client.redeem_gift_card(
                code, admin_wallet.private_key, amount,
                self.address, giftcard.currency.lower(),
                admin_wallet.address
            )
        except Exception as exception:
            raise exceptions.ValidationError(exception, 400)

    
    def save(self, *args, **kwargs):
        if self._state.adding:
            try:
                giftcard = GiftCard.objects.get(code=self.code)
            except GiftCard.DoesNotExist:
                raise exceptions.ValidationError("Giftcard does not exist", 404)
            
            note = giftcard.note
            
            try:
                self.redeem_giftcard(self.code)
            except Exception as exception:
                raise exceptions.ValidationError(exception, 400)
            
            giftcard.status = "used"
            
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
        return super(Redeem, self).save(*args, **kwargs)


class Transaction(models.Model):
    amount = models.FloatField(default=0.0)
    currency = models.CharField(max_length=255, default="naira")
    currency_type = models.CharField(max_length=255, default="fiat")
    crypto_amount = models.FloatField(default=0.0)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, default='pending')
    time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    transaction_type = models.CharField(max_length=255, null=True)
    transaction_hash = models.CharField(max_length=255, null=True)
    wallet_address = models.CharField(max_length=255, null=True)
    email = models.EmailField(blank=True, null=True)
    ref = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f"{self.wallet_address}: {self.email}"
    
    def check_flw_tran(self):
        email = self.email
        platform = "minipay"
    
        status = get_flw_status(self.transaction_hash)
        self.status = status.get('status')
        token_data = status.get('data')
        
        if token_data:
            token = token_data.get('extra')

        if self.status == "success" and token_data.get('extra'):
            # todo: customize email
            subject = "Transaction Success"
            html_message = render_to_string(
            'transaction_success.html',
                {
                    'token': token,
                }
            )
            plain_message = strip_tags(html_message)
            mail.send_mail(
                subject, plain_message, "BitGifty <info@bitgifty.com>",
                [email], html_message=html_message
            )

        if self.status != "success":
            if self.status != "pending":
                subject = "Withdrawal request failed"
                html_message = render_to_string(
                'transaction_failed.html',
                    {
                        'receipent_email': email,
                        'amount': self.amount,
                        'currency': self.currency,
                    }
                )
                plain_message = strip_tags(html_message)
                mail.send_mail(
                    subject, plain_message, "BitGifty <info@bitgifty.com>",
                    [email], html_message=html_message
                )

                client = Blockchain(key=os.getenv("TATUM_API_KEY"))
                
                network_mapping = {

                    "bitcoin": {
                        "virt": "BTC",
                        "wallet": "Bitcoin",
                    },
                    "celo": {
                        "virt": "CELO",
                        "wallet": "Celo",
                    },
                    "naira": {
                        "virt": "VC__BITGIFTY_NAIRA",
                        "wallet": "VC__BITGIFTY_NAIRA",
                    },
                    "ceur": {
                        "virt": "CEUR",
                        "wallet": "celo",
                    },
                    "cusd": {
                        "virt": "CUSD",
                        "wallet": "celo",
                    },
                    "usdt_tron": {
                        "virt": "USDT_TRON",
                        "wallet": "tron"
                    },
                    "tron": {
                        "virt": "TRON",
                        "wallet": "tron"
                    },
                    "eth": {
                        "virt": "ETH",
                        "wallet": "ethereum"
                    },
                }

                network = network_mapping[self.currency]["wallet"]
                admin_wallet = AdminWallet.objects.get(
                    owner__username="superman-houseboy",
                    network=network
                )

                receipent = Wallet.objects.get(
                    owner__email=email,
                    network=network
                )

                client.send_token(
                    receiver_address=self.wallet_address,
                    network=network,
                    amount=self.amount,
                    private_key=client.decrypt_crendentails(admin_wallet.private_key),
                    address=admin_wallet.address,
                )
                
        self.save()
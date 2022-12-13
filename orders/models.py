from django.db import models
from django.contrib.auth.models import User


class Bank(models.Model):
    bank = models.CharField(max_length=500, blank=False, null=False)

    def __str__(self):
        return self.bank


class DocumentType(models.Model):
    document = models.CharField(max_length=500, blank=False, null=False)

    def __str__(self):
        return self.document


class AccountType(models.Model):
    account_type = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.account_type


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    binance_id = models.CharField(primary_key=True, blank=False, null=False, max_length=1000)
    pay_id = models.CharField(max_length=500, blank=False, null=False)
    amount = models.CharField(max_length=500, blank=False, null=False)
    usdt_price = models.CharField(max_length=500, blank=False, null=False)
    is_contact = models.BooleanField(blank=True, null=True)
    account = models.CharField(max_length=500, null=False, blank=False)
    name = models.CharField(max_length=500, blank=True, null=True)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, null=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, null=True)
    document_number = models.CharField(max_length=500, null=True, blank=True)
    date = models.DateTimeField("When Created", auto_now_add=True)
    status = models.CharField(max_length=500, blank=False, null=False, default="created")
    fail_retry = models.IntegerField(null=False, blank=False, default=0)
    subscribe = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return " {} -- {}".format(self.binance_id, self.status)


class Abs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField()


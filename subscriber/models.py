from django.db import models

class Admin(models.Model):
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)

class Subscriber(models.Model):
    username = models.CharField(max_length=255)
    role = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    tariff = models.CharField(max_length=255)
    balance = models.CharField(max_length=20)
    status = models.CharField(max_length=100)
    iptv_login = models.CharField(max_length=100, blank=True, null=True)
    iptv_password = models.CharField(max_length=100, blank=True, null=True)
    equipment = models.TextField()

class Request(models.Model):
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    response = models.TextField()
    resolved = models.BooleanField(default=False)

class Problem(models.Model):
    description = models.TextField()
    reason = models.TextField()
    solution = models.TextField()
    is_correct = models.BooleanField(default=True)
    
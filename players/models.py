from django.db import models
from datetime import datetime


class Player(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    contact_number = models.CharField(max_length=30)
    ranking = models.IntegerField(default=0)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Active(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True)
    eff_from_date = models.DateField(default=datetime.now)
    eff_to_date = models.DateField(blank=True, null=True)
    transaction_date = models.DateTimeField(default=datetime.now)

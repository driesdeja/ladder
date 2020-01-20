from django.db import models


class Player(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    contact_number = models.CharField(max_length=30)
    ranking = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

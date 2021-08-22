from django.db import models
from django.contrib.auth.models import User
from players.models import Player


# Create your models here.
class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    player = models.OneToOneField(Player, on_delete=models.PROTECT)

    def __str___(self):
        return f'{self.player.first_name} Profile'

from django.db import models
from players.signals import player_status_changed


class Player(models.Model):
    ACTIVE = 0
    INACTIVE = 1
    DISABLED = 2

    Status = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (DISABLED, 'Disabled')
    ]
    
    
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    contact_number = models.CharField(max_length=30)
    ranking = models.IntegerField(default=0)
    email = models.EmailField(blank=True)
    status = models.IntegerField(choices=Status, default=ACTIVE)

    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)
        self.__original_status = self.status

    

    def save(self, *args, **kwargs):
        if self.status != self.__original_status:
            player_status_changed.send(sender=self, player=self, original_status=self.__original_status)
        super().save(*args, **kwargs)
    
    
    class Meta:
        ordering = ['last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class PlayerStatus(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    status = models.IntegerField()
    from_date = models.DateTimeField()
    to_date = models.DateTimeField(null=True)
    updated_date = models.DateTimeField(auto_now=True)


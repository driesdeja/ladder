from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from .models import Player, Active


"""
Used to create an active record when the player is created.
"""
@receiver(post_save, sender=Player)
def create_active_user(sender, instance, created, **kwargs):
    if created:
        Active.objects.create(player=instance)


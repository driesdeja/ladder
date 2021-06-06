from django.dispatch import Signal
from django.dispatch import receiver

player_status_changed = Signal()

@receiver(player_status_changed)
def player_status_change(sender, player, original_status, **kwargs):
    
    # This is a simple implementation of bi-temporality for player status.
    # Invalidate previous status. 
  #  player_status = PlayerStatus.objects.filter(player=player).filter(to_date__is_null=True)
    print(f'****** Status changed for {player.first_name} original status {original_status} new status {player.status}')
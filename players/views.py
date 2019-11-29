from django.shortcuts import render
from .models import Player


def list_players(request):
    context = {
        'title': 'Player List',
        'players': Player.objects.all()
    }
    return render(request, 'players/player_list.html', context)

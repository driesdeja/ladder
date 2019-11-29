from django.shortcuts import render
from .models import PlayersInLadderRound
from .models import LadderRound
from .models import Draw
from datetime import date


def list_rounds(request):
    # round_date = datetime.strptime('28 NOV 2019', '%d %b %Y')

    ladder_rounds = LadderRound.objects.all()

    ladder_rounds_with_players = []
    for entry in ladder_rounds:
        ladder_round_with_players = {'ladder_round': entry, 'players': PlayersInLadderRound.objects.filter(
            ladder_round__date=entry.date)}
        ladder_rounds_with_players.append(ladder_round_with_players)
    context = {
        'ladder_rounds': ladder_rounds_with_players
    }
    return render(request, 'round/round.html', context)


def ladder_draw(request):
    draw = Draw.objects.all()
    context = {
        'ladder_round_date': draw
    }
    return render(request, 'round/draw.html', context)

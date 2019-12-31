from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from .models import PlayersInLadderRound
from .models import LadderRound
from .models import Match
from .models import Ladder
from .models import Match
from .models import MatchResult
from datetime import date
from .forms import LadderForm, LadderRoundForm
from players.models import Player
from . import utils


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
    draw = Match.objects.all()
    context = {
        'ladder_round_date': draw
    }
    return render(request, 'round/draw.html', context)


def ladder_admin(request):
    form = LadderForm(request.POST or None)
    if form.is_valid():
        form.save()
        form = LadderForm()
    ladders = Ladder.objects.all()
    context = {
        'form': form,
        'ladders': ladders
    }
    return render(request, 'round/ladder-admin.html', context)


def ladder_detail(request, ladder_id):
    form = LadderRoundForm(request.POST or None)

    ladder = Ladder.objects.get(id=ladder_id)
    rounds = LadderRound.objects.filter(ladder=ladder).order_by('-start_date')
    if request.POST:
        print("Form posted")
    if form.is_valid():
        form.save()
        form = LadderRoundForm()
    context = {
        'form': form,
        'ladder': ladder,
        'rounds': rounds
    }
    return render(request, 'round/ladder-detail.html', context)


def round_detail(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    players = utils.get_players_in_round(ladder_round)
    context = {
        'ladder_round': ladder_round,
        'players': players
    }
    return render(request, 'round/round-detail.html', context)


def manage_players_in_round(request):
    ladder_round = LadderRound.objects.get(id=request.GET.get('round'))
    players = Player.objects.all()
    players_in_round = utils.get_players_in_round(ladder_round)
    players_not_in_round = []
    for player in players:
        if player not in players_in_round:
            players_not_in_round.append(player)
    players_not_in_round.sort(key=lambda x: x.ranking)
    players_in_round.sort(key=lambda x: x.ranking)
    context = {
        'ladder_round': ladder_round,
        'players_not_in_round': players_not_in_round,
        'players_in_round': players_in_round

    }
    return render(request, 'round/manage-players-in-round.html', context)


def add_players_to_round(request):
    ladder_round = LadderRound.objects.get(id=request.POST.get('ladder_round'))

    if request.POST.get('add_to_round'):
        add_player_to_round = PlayersInLadderRound()
        add_player_to_round.player = Player.objects.get(id=request.POST.get('add_to_round'))
        add_player_to_round.ladder_round = LadderRound.objects.get(id=request.POST.get('ladder_round'))
        add_player_to_round.save()

    if request.POST.get('remove_from_round'):
        player_to_remove = PlayersInLadderRound.objects.get(player=request.POST.get('remove_from_round'))
        player_to_remove.delete()

    players_in_round = utils.get_players_in_round(ladder_round)
    players_not_in_round = utils.get_players_not_in_round(players_in_round)

    context = {
        'ladder_round': ladder_round,
        'players_not_in_round': players_not_in_round,
        'players_in_round': players_in_round

    }
    return render(request, 'round/manage-players-in-round.html', context)


def round_draw(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    players = utils.get_players_in_round(ladder_round)
    matches = utils.setup_matches_for_draw(ladder_round, players)
    # Setting up the match ups/matches
    if len(players) % 2 == 0:
        print('EVEN' + str(len(players)))
    else:
        messages.warning(request, 'The number of players in the draw is uneven, please add or remove someone')
        print('odd' + str(len(players)))
    context = {
        'ladder_round': ladder_round,
        'players': players,
        'matches': matches
    }
    return render(request, 'round/draw.html', context)


def close_draw(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)

    if request.POST:
        if request.POST.get('close'):
            if ladder_round.status < 2:
                ladder_round.status = 2  # Closed
                ladder_round.save()
                number_of_matches = int(request.POST.get('number-of-matches'))
                for i in range(number_of_matches):
                    print(request.POST.get(str(i + 1) + '-player1'))
                    player1_id = int(request.POST.get(str(i + 1) + '-player1'))
                    player2_id = int(request.POST.get(str(i + 1) + '-player2'))
                    player1 = Player.objects.get(id=player1_id)
                    player2 = Player.objects.get(id=player2_id)
                    match = Match()
                    match.player1 = player1
                    match.player2 = player2
                    match.ladder_round = ladder_round
                    match.match_result = 0  # not played
                    match.save()
                    print(match)
            else:
                messages.warning(request, 'The round is not open for changes')
    players = utils.get_players_in_round(ladder_round)
    matches = []
    context = {
        'ladder_round': ladder_round,
        'players': players,
        'matches': matches,
    }
    return render(request, 'round/draw.html', context)


def capture_results(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    context = {
        'ladder_round': ladder_round,
        'matches': matches
    }
    return render(request, 'round/capture-results.html', context)

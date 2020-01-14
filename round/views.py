from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.forms.models import model_to_dict
from django.http import HttpResponse
from .models import PlayersInLadderRound
from .models import LadderRound
from .models import Match
from .models import Ladder
from .models import Match
from .models import MatchResult
from datetime import date
from .forms import LadderForm, LadderRoundForm, MatchForm
from players.models import Player
from .utils import validate_match_results, get_players_in_round, get_players_not_in_round, setup_matches_for_draw
from players.utils import calculate_change_in_ranking, update_ladder_ranking
from players.views import list_players


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
    players = get_players_in_round(ladder_round)
    context = {
        'ladder_round': ladder_round,
        'players': players
    }
    return render(request, 'round/round-detail.html', context)


def manage_players_in_round(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    players = Player.objects.all()
    players_in_round = get_players_in_round(ladder_round)
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


def add_players_to_round(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)

    if request.POST.get('add_to_round'):
        add_player_to_round = PlayersInLadderRound()
        add_player_to_round.player = Player.objects.get(id=request.POST.get('add_to_round'))
        add_player_to_round.ladder_round = LadderRound.objects.get(id=request.POST.get('ladder_round'))
        add_player_to_round.save()

    if request.POST.get('remove_from_round'):
        player_to_remove = PlayersInLadderRound.objects.get(player=request.POST.get('remove_from_round'))
        player_to_remove.delete()

    players_in_round = get_players_in_round(ladder_round)
    players_not_in_round = get_players_not_in_round(players_in_round)

    context = {
        'ladder_round': ladder_round,
        'players_not_in_round': players_not_in_round,
        'players_in_round': players_in_round

    }
    return render(request, 'round/manage-players-in-round.html', context)


def round_draw(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    players = get_players_in_round(ladder_round)
    matches = setup_matches_for_draw(ladder_round, players)
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
    players = get_players_in_round(ladder_round)
    matches = []
    context = {
        'ladder_round': ladder_round,
        'players': players,
        'matches': matches,
    }
    return render(request, 'round/draw.html', context)


def capture_results(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    if request.POST:
        if request.POST.get('save_results'):
            form_matches = request.POST.getlist("match")
            for form_match in form_matches:
                match = Match.objects.get(id=form_match)
                if request.POST.get('match[' + form_match + '][player1-games]'):
                    match.games_for_player1 = int(request.POST.get('match[' + form_match + '][player1-games]'))
                if request.POST.get('match[' + form_match + '][player2-games]'):
                    match.games_for_player2 = int(request.POST.get('match[' + form_match + '][player2-games]'))
                if request.POST.get('match[' + form_match + '][player1-defaulted]'):
                    match.result = match.PLAYER_1_DEFAULTED
                if request.POST.get('match[' + form_match + '][player2-defaulted]'):
                    match.result = match.PLAYER_2_DEFAULTED
                if request.POST.get('match[' + form_match + '][match-cancelled]'):
                    match.result = match.CANCELLED
                errors = validate_match_results(match)
                if len(errors) < 1:
                    if match.games_for_player1 == 3:
                        match.result = match.PLAYER_1_WON
                    elif match.games_for_player2 == 3:
                        match.result = match.PLAYER_2_WON
                    if match.result == match.PLAYER_1_DEFAULTED:
                        match.games_for_player2 = 3
                    if match.result == match.PLAYER_2_DEFAULTED:
                        match.games_for_player1 = 3
                    print(match)
                    match.save()
                else:
                    for error in errors:
                        messages.error(request, error)
        if request.POST.get('update_ranking'):
            return redirect(update_players_ranking, round_id=ladder_round.id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    unplayed_matches = Match.objects.filter(ladder_round=ladder_round).filter(result__exact=0)
    if len(unplayed_matches) == 0:
        all_matches_captured = True
    else:
        all_matches_captured = False
    context = {
        'ladder_round': ladder_round,
        'matches': matches,
        'all_matches_captured': all_matches_captured
    }
    return render(request, 'round/capture-results.html', context)


def view_round_results(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)

    context = {
        'ladder_round': ladder_round,
        'matches': matches
    }
    return render(request, 'round/view-results.html', context)


def edit_match(request, round_id, match_id):
    match = Match.objects.get(id=match_id)
    ladder_round = LadderRound.objects.get(id=round_id)
    if request.POST:
        if request.POST.get("save"):
            form = MatchForm(request.POST, instance=match)
            if form.is_valid():  # The form validation is not happening, I have no idea why not.

                error_messages = validate_match_results(match)
                if len(error_messages) > 0:
                    for message in error_messages:
                        messages.error(request, message)
                else:
                    match.save()
                    messages.info(request, 'Match Saved Successfully')
        else:
            return redirect(capture_results, round_id=ladder_round.id)
    else:
        form = MatchForm(initial=model_to_dict(match))
    context = {
        'ladder_round': ladder_round,
        'match': match,
        'form': form
    }
    return render(request, 'round/edit-match.html', context)


def update_players_ranking(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    new_ranking_list = calculate_change_in_ranking(matches)
    if request.POST:
        for each_player in new_ranking_list:
            player = Player.objects.get(id=each_player['player_id'])
            new_ranking = player.ranking + int(each_player['player_ranking_change'])
            update_ladder_ranking(player, 'change', new_ranking)
        ladder_round.end_date = date.today()
        ladder_round.status = ladder_round.COMPLETED
        ladder_round.save()
        return redirect(list_players)

    context = {
        'new_ranking_list': new_ranking_list,
        'matches': matches,
        'ladder_round': ladder_round
    }
    return render(request, 'round/update_players_ranking.html', context)


def ladder_overview(request):
    ladders = Ladder.objects.filter(status=Ladder.OPEN)
    for ladder in ladders:
        ladder_rounds = LadderRound.objects.filter(ladder=ladder)
        for ladder_round in ladder_rounds:
            if ladder_round.status == ladder_round.COMPLETED:
                matches_in_round = Match.objects.filter(ladder_round=ladder_round)
                print(str(ladder_round.start_date))
                for match in matches_in_round:
                    print(match.games_for_player1)
                    print(match.games_for_player2)

    players = Player.objects.all().order_by('ranking') 
    context = {
        'ladders': ladders,
        'players': players
    }
    return render(request, 'round/ladder-overview.html', context)

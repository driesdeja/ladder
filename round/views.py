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
from .models import PlayerRanking
from datetime import date, datetime
from .forms import LadderForm, LadderRoundForm, MatchForm, LadderStatusForm
from players.models import Player
from .utils import validate_match_results, get_players_in_round, get_players_not_in_round, setup_matches_for_draw, \
    add_player_to_round, compare_and_update_player_with_playerranking, get_full_ladder_details, remove_player_from_round
from round.utils import calculate_change_in_ranking, update_ladder_ranking, matches_player_played_in
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
    rounds = list(LadderRound.objects.filter(ladder=ladder).order_by('start_date'))
    if request.POST:
        if request.POST.get("add_round"):
            if form.is_valid():
                form.save()
                form = LadderRoundForm()
                if ladder.status == ladder.CREATED:
                    ladder.status = ladder.OPEN
                    ladder.save()
                return redirect(ladder_detail, ladder_id)
        elif request.POST.get('close_ladder'):
            if rounds:
                ladder.status = ladder.COMPLETED
            else:
                ladder.status = ladder.CANCELLED
            if request.POST.get('end_date'):
                ladder.end_date = request.POST.get('end_date')
            else:
                if not ladder.end_date:
                    ladder.end_date = datetime.now()
            ladder.save()
            return redirect(ladder_admin)
        elif request.POST.get('delete_ladder'):
            ladder.delete()
            return redirect(ladder_admin)
        elif request.POST.get('re_open'):
            ladder.status = ladder.OPEN

            if ladder.end_date <= date.today():
                ladder.end_date = None
            ladder.save()
            return redirect(ladder_detail, ladder_id)

    ladder_close_form = LadderStatusForm(initial={'end_date': datetime.now()})
    closeable = True
    for ladder_round in rounds:
        if ladder_round.status < ladder_round.COMPLETED:
            closeable = False
    context = {
        'form': form,
        'closeable': closeable,
        'ladder_close_form': ladder_close_form,
        'ladder': ladder,
        'rounds': rounds
    }
    return render(request, 'round/ladder-detail.html', context)


def round_detail(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    players = get_players_in_round(ladder_round)
    if ladder_round.status == ladder_round.CLOSED:
        matches = Match.objects.filter(ladder_round=ladder_round)
    else:
        matches = None
    if request.POST.get('copy_players'):
        previous_round_id = request.POST.get('previous_round')
        previous_round = LadderRound.objects.get(id=previous_round_id)
        new_players = get_players_in_round(previous_round)
        for player in new_players:
            add_player_to_round(round_id, player)
        ladder_round.status = ladder_round.OPEN
        ladder_round.save()
        return redirect(manage_players_in_round, round_id)
    if request.POST.get('leave_round'):
        player_id = request.POST.get('player_id')
        player = Player.objects.get(id=player_id)
        remove_player_from_round(round_id, player)
        return redirect(round_detail, round_id)
    if request.POST.get('enter_round'):
        player_id = request.POST.get('player_id')
        player = Player.objects.get(id=player_id)
        add_player_to_round(round_id, player_id)
        return redirect(round_detail, round_id)
    if request.POST.get('capture-match-results'):
        match = Match.objects.get(id=request.POST.get('match-id'))
        if request.POST.get('player1-defaulted'):
            match.result = match.PLAYER_1_DEFAULTED
        if request.POST.get('player2-defaulted'):
            match.result = match.PLAYER_2_DEFAULTED
        if request.POST.get('games-for-player1'):
            match.games_for_player1 = int(request.POST.get('games-for-player1'))
        if request.POST.get('games-for-player2'):
            match.games_for_player2 = int(request.POST.get('games-for-player2'))
        if request.POST.get('date-played'):
            date_str = request.POST.get('date-played')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            match.date_played = date_obj
            match.date_played = datetime.strptime(
                request.POST.get('date-played'), '%Y-%m-%d')
        else:
            match.date_played = date.today()
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

            match.save()
            messages.info(request, 'Match result successfully captured!')
            return redirect(round_detail, round_id)
        else:
            for error in errors:
                messages.warning(request, error)
    if request.POST.get('reset-match-results'):
        match = Match.objects.get(id=request.POST.get('match-id'))
        match.games_for_player2 = 0
        match.games_for_player1 = 0
        match.date_played = None
        match.result = Match.NOT_PLAYED
        match.save()
        messages.info(request, 'Match result has been reset, please re-capture!')
        return redirect(round_detail, round_id)
    previous_rounds = LadderRound.objects.filter(ladder=ladder_round.ladder,
                                                 status__exact=LadderRound.COMPLETED).order_by('-start_date')
    ladder_rounds = LadderRound.objects.filter(ladder=ladder_round.ladder,
                                               status__in=[LadderRound.OPEN, LadderRound.CLOSED,
                                                           LadderRound.COMPLETED]).order_by('start_date')
    ladder = ladder_round.ladder
    context = {
        'ladder': ladder,
        'ladder_round': ladder_round,
        'ladder_rounds': ladder_rounds,
        'players': players,
        'previous_rounds': previous_rounds,
        'matches': matches
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

    if request.POST.get('add_to_round[]'):
        if ladder_round.status > ladder_round.OPEN:
            messages.error(request, 'The round is not open anymore, re-open the round if needed.')
        if not ladder_round.status == ladder_round.OPEN:
            ladder_round.status = ladder_round.OPEN
            ladder_round.save()
        players_to_add = request.POST.getlist('add_to_round[]')
        for player in players_to_add:
            add_player_to_round(round_id, player)

    if request.POST.get('remove_from_round[]'):
        players_to_remove = request.POST.getlist('remove_from_round[]')
        for player in players_to_remove:
            player_to_remove = PlayersInLadderRound.objects.filter(player=player, ladder_round=ladder_round)
            if player_to_remove:
                player_to_remove.delete()
        return redirect(add_players_to_round, round_id)

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
    if len(players) % 2 != 0:
        messages.warning(request, 'The number of players in the draw is uneven, please add or remove someone')
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
                return redirect(capture_results, ladder_round.id)
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
    if ladder_round.status < 2:
        messages.warning(request, 'Draw is not yet finalised.  Please finalise the draw before capturing the results.')
    else:
        if request.POST:
            if request.POST.get('update_ranking'):
                return redirect(update_players_ranking, ladder_round.id)
            if request.POST.get('re-open-round'):
                matches = Match.objects.filter(ladder_round=ladder_round)
                for match in matches:
                    match.delete()
                ladder_round.status = ladder_round.OPEN
                ladder_round.save()

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
                    if request.POST.get('match[' + form_match + '][date-played]'):
                        date_str = request.POST.get('match[' + form_match + '][date-played]')
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        match.date_played = date_obj
                        match.date_played = datetime.strptime(
                            request.POST.get('match[' + form_match + '][date-played]'), '%Y-%m-%d')
                    else:
                        match.date_played = date.today()
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

                        match.save()
                    else:
                        for error in errors:
                            messages.warning(request, error)

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
    ladder = ladder_round.ladder
    matches = Match.objects.filter(ladder_round=ladder_round)
    ladder_rounds = list(
        LadderRound.objects.filter(ladder__exact=ladder).filter(
            status__in=[LadderRound.COMPLETED, LadderRound.CLOSED, LadderRound.OPEN]).order_by('start_date'))
    context = {
        'ladder_round': ladder_round,
        'ladder_rounds': ladder_rounds,
        'ladder': ladder,
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
                        messages.warning(request, message)
                else:
                    match.save()
                    messages.success(request, 'Match Saved Successfully')
                    return redirect(capture_results, round_id=ladder_round.id)
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
        today = date.today()
        ladder_round.end_date = today
        ladder_round.status = ladder_round.COMPLETED
        ladder_round.save()
        """ Need to update the ranking change log once all the movements for the rounds has been completed.
            The way to do this is to loop through the rankings in the player list and compare that with the active
            PlayerRanking for the player
        """
        compare_and_update_player_with_playerranking(f'Ladder round {ladder_round.start_date} updated on {today}')
        return redirect(list_players)

    context = {
        'new_ranking_list': new_ranking_list,
        'matches': matches,
        'ladder_round': ladder_round
    }
    return render(request, 'round/update_players_ranking.html', context)


def ladder_overview(request):
    open_ladder = Ladder.objects.filter(status=Ladder.OPEN).first()
    ladder_rounds = list(LadderRound.objects.filter(ladder__exact=open_ladder).filter(
        status__in=(LadderRound.OPEN, LadderRound.COMPLETED, LadderRound.CLOSED)))
    players = Player.objects.all().order_by('ranking')
    full_ladder_details = get_full_ladder_details(open_ladder)
    context = {
        'ladder': open_ladder,
        'ladder_rounds': ladder_rounds,
        'players': players,
        'full_ladder_details': full_ladder_details
    }
    return render(request, 'round/ladder-overview.html', context)


def player_profile(request, player_id):
    player = Player.objects.get(id=player_id)
    player_rankings = PlayerRanking.objects.filter(player=player).order_by('-last_updated')
    competed_in_rounds = PlayersInLadderRound.objects.filter(player=player)

    ladder_rounds_competed_in = []
    for competed_in_round in competed_in_rounds:
        ladder_rounds_competed_in.append(competed_in_round.ladder_round)
    ladders_competed_in = []
    for ladder_round in ladder_rounds_competed_in:
        ladders_competed_in.append(Ladder.objects.get(id=ladder_round.ladder.id))
    set_ladders = set(ladders_competed_in)
    ladders_competed_in = list(set_ladders)
    matches_played_in = []
    for each_ladder in ladders_competed_in:
        matches_played_in.extend(matches_player_played_in(player, each_ladder))
    context = {
        'player': player,
        'player_rankings': player_rankings,
        'ladders_competed_in': ladders_competed_in,
        'ladder_rounds_competed_in': ladder_rounds_competed_in,
        'matches': matches_played_in
    }

    return render(request, 'round/player_profile.html', context)

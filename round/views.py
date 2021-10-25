"""
Views
"""

import json
from datetime import date, datetime
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from players.models import Player
from players.views import list_players
from round.utils import calculate_change_in_ranking, \
    update_ladder_ranking, matches_player_played_in, date_range
from .models import PlayersInLadderRound
from .models import LadderRound
from .models import Match
from .models import Ladder
from .models import PlayerRanking
from .models import MatchSchedule
from .forms import LadderForm, LadderRoundForm, MatchForm, LadderStatusForm

from .utils import validate_match_results, \
    get_players_in_round, \
    get_players_not_in_round, \
    setup_matches_for_draw, \
    add_player_to_round, \
    compare_and_update_player_with_playerranking, \
    get_full_ladder_details, \
    remove_player_from_round, \
    create_match_schedule_with_round_match_schedule, \
    validate_and_create_ladder_round, \
    re_open_round, \
    save_scheduled_matches, \
    save_scheduled_match, \
    validate_and_create_ladder_rounds, \
    generate_round_match_schedule, \
    validate_and_create_ladder, \
    setup_match_days, \
    close_ladder_round_draw
from .reports import get_pdf_match_schedule


def list_rounds(request, ladder_id):
    """
    List all the rounds in a Ladder
    """
    # round_date = datetime.strptime('28 NOV 2019', '%d %b %Y')
    ladder = Ladder.objects.get(id=ladder_id)

    ladder_rounds = LadderRound.objects.filter(ladder=ladder)

    ladder_rounds_with_players = []
    for entry in ladder_rounds:
        ladder_round_with_players = {'ladder_round': entry,
                                     'players': PlayersInLadderRound.objects.filter(
                                         ladder_round__date=entry.date)}
        ladder_rounds_with_players.append(ladder_round_with_players)
    context = {
        'ladder_rounds': ladder_rounds_with_players
    }
    return render(request, 'round/round.html', context)


def ladder_draw(request, round_id):
    """
    view to display the draw (Matches) in a LadderRound
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    draw = Match.objects.filter(ladder_round=ladder_round)
    context = {
        'ladder_round_date': draw
    }
    return render(request, 'round/draw.html', context)


def ladder_admin(request):
    """
    Not sure what this does...Looks like it serves the form to create a Ladder?
    """
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
    """
    View to service the basic maintanance of the ladder.
    This would be to add a round or close the ladder.
    """
    form = LadderRoundForm(request.POST or None)
    ladder = Ladder.objects.get(id=ladder_id)
    rounds = list(LadderRound.objects.filter(
        ladder=ladder).order_by('start_date'))
    if request.POST:
        if request.POST.get("add_round"):
            if form.is_valid():
                new_ladder_round = form.save()
                if ladder.status == ladder.CREATED:
                    ladder.status = ladder.OPEN
                    ladder.save()
                return redirect(manage_players_in_round, new_ladder_round.id)
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
    """
    Supports the following POST requests:
    copy_players,
    leave_round,
    enter_round,
    capture-match-results
    reset-match-results
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    players = get_players_in_round(ladder_round)
    scheduled_matches = MatchSchedule.objects.filter(
        ladder_round=ladder_round).order_by('time_grid_location')
    round_match_schedule = ladder_round.match_schedule
    matches = Match.objects.filter(ladder_round=ladder_round)

    if request.POST.get('copy_players'):
        # todo: Move this to the business layer
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
        add_player_to_round(round_id, player_id)
        return redirect(round_detail, round_id)
    if request.POST.get('capture-match-results'):
        match = Match.objects.get(id=request.POST.get('match-id'))
        if request.POST.get('player1-defaulted'):
            match.result = match.PLAYER_1_DEFAULTED
        if request.POST.get('player2-defaulted'):
            match.result = match.PLAYER_2_DEFAULTED
        if request.POST.get('games-for-player1'):
            match.games_for_player1 = int(
                request.POST.get('games-for-player1'))
        if request.POST.get('games-for-player2'):
            match.games_for_player2 = int(
                request.POST.get('games-for-player2'))
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
        messages.info(
            request, 'Match result has been reset, please re-capture!')
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
        'matches': matches,
        'round_match_schedule': round_match_schedule,
        'scheduled_matches': scheduled_matches
    }
    return render(request, 'round/round-detail.html', context)


def manage_players_in_round(request, round_id):
    """
    Create list of players in the round and not in the round.
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    players = Player.objects.filter(status=Player.ACTIVE)
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
    """
    Manages adding players to the round.
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    ladder = ladder_round.ladder
    ladder_rounds = LadderRound.objects.filter(
        ladder=ladder_round.ladder).order_by("start_date")
    previous_round = LadderRound.objects.filter(ladder=ladder).exclude(id=ladder_round.id).order_by(
        '-start_date').first()
    players_in_previous_round = get_players_in_round(previous_round)
    number_of_players_in_previous_round = len(players_in_previous_round)

    if request.POST.get('copy_players'):
        for player_in_previous_round in players_in_previous_round:
            add_player_to_round(ladder_round.id, player_in_previous_round)
        if not ladder_round.status == ladder_round.OPEN:
            ladder_round.status = ladder_round.OPEN
            ladder_round.save()
        return redirect(add_players_to_round, ladder_round.id)
    if request.POST.get("view_draw"):
        return redirect(round_draw, ladder_round.id)
    if request.POST.get('add_to_round[]'):
        if ladder_round.status > ladder_round.OPEN:
            messages.error(
                request, 'The round is not open anymore, re-open the round if needed.')
        if not ladder_round.status == ladder_round.OPEN:
            ladder_round.status = ladder_round.OPEN
            ladder_round.save()
        players_to_add = request.POST.getlist('add_to_round[]')
        for player in players_to_add:
            add_player_to_round(round_id, player)

    if request.POST.get('remove_from_round[]'):
        players_to_remove = request.POST.getlist('remove_from_round[]')
        for player in players_to_remove:
            player_to_remove = PlayersInLadderRound.objects.filter(
                player=player, ladder_round=ladder_round)
            if player_to_remove:
                player_to_remove.delete()
        return redirect(add_players_to_round, round_id)

    players_in_round = get_players_in_round(ladder_round)
    players_not_in_round = get_players_not_in_round(players_in_round)

    round_has_players = len(players_in_round) > 0

    context = {
        'ladder': ladder,
        'ladder_round': ladder_round,
        'ladder_rounds': ladder_rounds,
        'players_not_in_round': players_not_in_round,
        'players_in_round': players_in_round,
        'round_has_players': round_has_players,
        'previous_round': previous_round,
        'number_of_players_in_previous_round': number_of_players_in_previous_round
    }
    return render(request, 'round/manage-players-in-round.html', context)


def round_draw(request, round_id):
    """
    Creates the draw for the round and ensure that there are an even number of players
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    ladder_rounds = LadderRound.objects.filter(ladder=ladder_round.ladder)
    players = get_players_in_round(ladder_round)
    matches = Match.objects.filter(ladder_round=ladder_round)
    if not matches:
        matches = setup_matches_for_draw(ladder_round, players)

    if len(players) % 2 != 0:
        messages.warning(
            request, 'The number of players in the draw is uneven, please add or remove someone')
    context = {
        'ladder_round': ladder_round,
        'ladder_rounds': ladder_rounds,
        'players': players,
        'matches': matches
    }
    return render(request, 'round/draw.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def close_draw(request, round_id):
    """
    Closes the draw for the round.
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    if ladder_round.status < ladder_round.CLOSED:
        if LadderRound.objects.filter(status=ladder_round.CLOSED):
            messages.error(
                request, 'Two rounds cannot be closed (in progress) at the same time')
        else:
            players = get_players_in_round(ladder_round)
            matches = Match.objects.filter(ladder_round=ladder_round)
            if not matches:
                matches = setup_matches_for_draw(ladder_round, players)
            close_ladder_round_draw(ladder_round, matches)
        return redirect(round_draw, ladder_round.id)
    else:
        messages.warning(request, 'The round is not open for changes')
    return redirect(round_draw, ladder_round.id)


@permission_required('round.ladder.can_administrate_the_ladder')
def edit_draw(request, round_id):
    """
    Edit the ladder draw
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    players = get_players_in_round(ladder_round)
    if request.POST:
        data = json.loads(request.POST.get("payload"))
        new_players = []
        for item in data:
            new_players.append(Player.objects.get(id=item['player1']))
            new_players.append(Player.objects.get(id=item['player2']))
        matches = setup_matches_for_draw(ladder_round, new_players)
        close_ladder_round_draw(ladder_round, matches)

        return redirect(round_draw, ladder_round.id)
    else:
        matches = setup_matches_for_draw(ladder_round, players)
    context = {
        'players': players,
        'ladder_round': ladder_round,
        'matches': matches
    }
    return render(request, 'round/edit-draw.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def capture_results(request, round_id):
    """
    Capture results of the matches
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    if ladder_round.status < 2:
        messages.warning(
            request,
            'Draw is not yet finalised.  Please finalise the draw before capturing the results.')
    else:
        if request.POST:
            if request.POST.get('update_ranking'):
                return redirect(update_players_ranking, ladder_round.id)
            if request.POST.get('re-open-round'):
                if re_open_round(ladder_round):
                    return redirect(round_draw, ladder_round.id)
                else:
                    messages.error(request, 'Unable to re-open the round!')
            if request.POST.get('save_results'):
                form_matches = request.POST.getlist("match")
                for form_match in form_matches:
                    match = Match.objects.get(id=form_match)
                    if request.POST.get('match[' + form_match + '][player1-games]'):
                        match.games_for_player1 = int(request.POST.get(
                            'match[' + form_match + '][player1-games]'))
                    if request.POST.get('match[' + form_match + '][player2-games]'):
                        match.games_for_player2 = int(request.POST.get(
                            'match[' + form_match + '][player2-games]'))
                    if request.POST.get('match[' + form_match + '][player1-defaulted]'):
                        match.result = match.PLAYER_1_DEFAULTED
                    if request.POST.get('match[' + form_match + '][player2-defaulted]'):
                        match.result = match.PLAYER_2_DEFAULTED
                    if request.POST.get('match[' + form_match + '][match-cancelled]'):
                        match.result = match.CANCELLED
                    if request.POST.get('match[' + form_match + '][date-played]'):
                        date_str = request.POST.get(
                            'match[' + form_match + '][date-played]')
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
    unplayed_matches = Match.objects.filter(
        ladder_round=ladder_round).filter(result__exact=0)
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
    """
    Retrieve and display the results of the the round
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    ladder = ladder_round.ladder
    matches = Match.objects.filter(ladder_round=ladder_round)
    ladder_rounds = list(
        LadderRound.objects.filter(ladder__exact=ladder).filter(
            status__in=[LadderRound.COMPLETED, LadderRound.CLOSED, LadderRound.OPEN])\
                        .order_by('start_date'))
    context = {
        'ladder_round': ladder_round,
        'ladder_rounds': ladder_rounds,
        'ladder': ladder,
        'matches': matches
    }
    return render(request, 'round/view-results.html', context)


def edit_match(request, round_id, match_id):
    """
    Edit a specific match
    """
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


@permission_required('round.ladder.can_administrate_the_ladder')
def update_players_ranking(request, round_id):
    """
    Manually update a players ranking
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    new_ranking_list = calculate_change_in_ranking(matches)
    if request.POST:
        eff_date = request.POST.get("eff_date")
        for each_player in new_ranking_list:
            player = Player.objects.get(id=each_player['player_id'])
            new_ranking = player.ranking + \
                int(each_player['player_ranking_change'])
            update_ladder_ranking(player, 'change', new_ranking, eff_date)
        ladder_round.status = ladder_round.COMPLETED
        ladder_round.save()
        # Need to update the ranking change log once all the movements for the rounds has been
        # completed.
        # The way to do this is to loop through the rankings in the player list and compare
        # that with the active
        # SPlayerRanking for the player
        #
        compare_and_update_player_with_playerranking(
            f'Ladder round {ladder_round.start_date} updated on {eff_date}', ladder_round.end_date)

        return redirect(list_players)

    context = {
        'new_ranking_list': new_ranking_list,
        'matches': matches,
        'ladder_round': ladder_round
    }
    return render(request, 'round/update_players_ranking.html', context)


def ladder_overview(request):
    """
    Setup the details of the open ladder
    """
    open_ladder = None
    ladder_rounds = None
    full_ladder_details = None

    if Ladder.objects.filter(status=Ladder.OPEN).exists():
        open_ladder = Ladder.objects.filter(status=Ladder.OPEN).first()
        ladder_rounds = LadderRound.objects.filter(ladder=open_ladder, status__in=[
                LadderRound.OPEN, LadderRound.COMPLETED, LadderRound.CLOSED]).order_by('start_date')

        full_ladder_details = get_full_ladder_details(open_ladder)
    players = Player.objects.filter(status=Player.ACTIVE).order_by('-ranking')
    context = {
        'ladder': open_ladder,
        'ladder_rounds': ladder_rounds,
        'players': players,
        'full_ladder_details': full_ladder_details
    }
    return render(request, 'round/ladder-overview.html', context)


def player_profile(request, player_id):
    """
    Retreive all of the details of a player,
    as it relates to the matches played.
    """
    player = Player.objects.get(id=player_id)
    player_rankings = PlayerRanking.objects.filter(
        player=player).order_by('-last_updated')
    competed_in_rounds = PlayersInLadderRound.objects.filter(player=player)

    ladder_rounds_competed_in = []
    for competed_in_round in competed_in_rounds:
        ladder_rounds_competed_in.append(competed_in_round.ladder_round)
    ladders_competed_in = []
    for ladder_round in ladder_rounds_competed_in:
        ladders_competed_in.append(
            Ladder.objects.get(id=ladder_round.ladder.id))
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


@permission_required('round.ladder.can_administrate_the_ladder')
def schedule_matches(request, round_id):
    """
    Scheduling of matches.
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    non_scheduled_matches = []
    for each_match in matches:
        if not MatchSchedule.objects.filter(match=each_match):
            non_scheduled_matches.append(each_match)
    saved_matches_schedule = MatchSchedule.objects.filter(
        ladder_round=ladder_round)
    schedule = ladder_round.match_schedule
    if not schedule:
        messages.error(
            request, 'Please setup a schedule before schedulding matches')
        return redirect(setup_scheduling_for_round, ladder_round.id)
    if request.POST:
        scheduled_matches = json.loads(request.POST.get('scheduled-matches'))
        # todo Validate that match_day is between the start and end dates of the ladder_round
        save_scheduled_matches(ladder_round, scheduled_matches)

        print(scheduled_matches)
    # setup the year for the round
    ladder_round_year = ladder_round.start_date.year
    context = {
        'ladder_round': ladder_round,
        'matches': non_scheduled_matches,
        'schedule': schedule,
        'saved_matches_schedule': saved_matches_schedule,
        'ladder_round_year': ladder_round_year
    }
    return render(request, 'round/schedule_matches.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def setup_scheduling_for_round(request, round_id):
    """
    Setup the scheduling for the round.  This can be complicated.
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    ladder = ladder_round.ladder
    ladder_rounds = LadderRound.objects.filter(ladder=ladder)
    start_date = ladder_round.start_date
    end_date = ladder_round.end_date
    days = date_range(start_date, end_date)
    if request.POST:
        if request.POST.get('generate-match-schedule'):
            match_days = request.POST.getlist('match-day[]')
            number_of_courts = int(request.POST.get('number-of-courts'))
            start_time = datetime.strptime(
                request.POST.get('start-time'), '%H:%M').time()
            time_interval = request.POST.get('time-interval')
            number_of_games = request.POST.get('number-of-games')
            end_time = datetime.strptime(
                request.POST.get('end-time'), '%H:%M').time()

            round_match_schedule = generate_round_match_schedule(match_days,
                                                                 number_of_courts,
                                                                 start_time,
                                                                 end_time,
                                                                 time_interval,
                                                                 number_of_games)

            ladder_round.match_schedule = round_match_schedule
            ladder_round.save()
            create_match_schedule_with_round_match_schedule(
                ladder_round, round_match_schedule)
            print(f'schedule: {round_match_schedule}')
        elif request.POST.get('reset-schedule'):
            matches_schedule = MatchSchedule.objects.filter(
                ladder_round=ladder_round)
            for each in matches_schedule:
                each.delete()
            ladder_round.match_schedule = None
            ladder_round.save()
        elif request.POST.get('commit-schedule'):
            return redirect(add_players_to_round, ladder_round.id)
        return redirect(setup_scheduling_for_round, ladder_round.id)

    matches_schedule = MatchSchedule.objects.filter(
        ladder_round=ladder_round).order_by('day').order_by('time_slot')

    context = {
        'ladder_rounds': ladder_rounds,
        'ladder': ladder,
        'ladder_round': ladder_round,
        'days': days,
        'matches_schedule': matches_schedule
    }
    return render(request, 'round/setup-scheduling.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def admin_round_detail(request, round_id):
    """
    Sets up most of the details of a ladder round.
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    match_schedule = ladder_round.match_schedule
    scheduled_matches = MatchSchedule.objects.filter(
        ladder_round=ladder_round).exclude(match__isnull=True)
    ladder_rounds = list(LadderRound.objects.filter(
        ladder=ladder_round.ladder).order_by('start_date'))
    round_number = ladder_rounds.index(ladder_round) + 1
    context = {
        'ladder_round': ladder_round,
        'round_number': round_number,
        'match_schedule': match_schedule,
        'scheduled_matches': scheduled_matches,
        'ladder_rounds': ladder_rounds,
        'matches': matches,

    }
    return render(request, 'round/admin-round-detail.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def create_ladder_round(request, ladder_id):
    """
    Create a ladder round
    """
    ladder = Ladder.objects.get(id=ladder_id)
    ladder_rounds = LadderRound.objects.filter(ladder=ladder)
    last_round = LadderRound.objects.filter(
        ladder=ladder).order_by('-end_date').first()
    if request.POST:
        # todo validate the dates
        start_date = datetime.strptime(
            request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(
            request.POST.get('end_date'), '%Y-%m-%d').date()
        try:
            ladder_round = validate_and_create_ladder_round(
                ladder, start_date, end_date)
        except ValueError as error:
            messages.error(request, f'{error}')
        else:
            ladder_round.save()
            if request.POST.get('setup_schedule'):
                return redirect(setup_scheduling_for_round, ladder_round.id)
    context = {
        'ladder': ladder,
        'ladder_rounds': ladder_rounds,
        'last_round': last_round

    }
    return render(request, 'round/create-ladder-round.html', context)


def save_scheduled_match_view(request, round_id):
    """
    Save scheduled match
    """
    response_data = {}
    ladder_round = LadderRound.objects.get(id=round_id)
    if request.POST:
        if request.POST.get('save'):
            match_id = request.POST.get("match_id")
            match_time = request.POST.get("match_time")
            match_day = request.POST.get("match_day")
            court = request.POST.get("court")
            # todo:  I hate this and need to find another way to do this
            try:
                scheduled_match = MatchSchedule.objects.get(match_id=match_id)
                scheduled_match.delete()
            except ObjectDoesNotExist:
                pass
            finally:
                scheduled_match = save_scheduled_match(
                    ladder_round, match_id, match_day, court, match_time)
            response_data['match_schedule_id'] = scheduled_match.id
            response_data['match_id'] = match_id
            return JsonResponse(response_data)
        elif request.POST.get('remove'):
            match_id = request.POST.get("match_id")
            match = Match.objects.get(id=match_id)
            match_schedule = MatchSchedule.objects.get(match=match)
            print(match_schedule)
            if match_schedule:
                match_schedule.delete()
            response_data['match_removed'] = match_schedule.id
            response_data['match_id'] = match_id
            return JsonResponse(response_data)
    return render(request, 'round/create-ladder-round.html')


def ladder_setup_wizard(request):
    """
    View to support the ladder setup wizzard
    """
    if request.POST:
        # Ladder details
        ladder_name = request.POST.get('ladder_name')
        ladder_start_date = request.POST.get('ladder_start_date')
        ladder_end_date = request.POST.get('ladder_end_date')
        number_of_rounds = request.POST.get('number_of_rounds')

        try:
            ladder = validate_and_create_ladder(
                ladder_name, ladder_start_date, ladder_end_date)
        except ValueError as error:
            messages.error(request, f'The ladder is invalid: {error}')
            return redirect(ladder_setup_wizard)

        # Calculation Engine
        # todo: Implement the calculation selection.  Only one is currently implemented.

        # Rounds details

        if request.POST.get('round_start_date'):
            first_round_start_date = datetime.strptime(
                request.POST.get('round_start_date'), '%Y-%m-%d').date()
        else:
            first_round_start_date = ladder.start_date
        duration_of_round = request.POST.get('duration_of_round')

        if number_of_rounds:
            number_of_rounds = int(number_of_rounds)
        # create the rounds setting up the start and end dates

        try:
            ladder_rounds = validate_and_create_ladder_rounds(
                ladder, number_of_rounds, first_round_start_date, duration_of_round)
        except ValueError as error:
            messages.error(request, f'Ladder rounds are invalid: {error}')
            return redirect(ladder_setup_wizard)
        # Round schedule setup
        set_up_schedule = request.POST.get('schedule_select')

        if set_up_schedule == 'setup_schedule':
            match_days = request.POST.getlist('match_day[]')
            number_of_courts = request.POST.get('number_of_courts')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            time_interval = request.POST.get('time_interval')
            number_of_games = request.POST.get('number_of_games')

            for each_round in ladder_rounds:
                match_days_of_the_year = setup_match_days(
                    each_round.start_date, match_days)
                round_match_schedule = generate_round_match_schedule(match_days_of_the_year,
                                                                     number_of_courts,
                                                                     start_time,
                                                                     end_time,
                                                                     time_interval,
                                                                     number_of_games)
                each_round.match_schedule = round_match_schedule
                each_round.save()

        select_players = request.POST.get('select_players')
        if select_players == 'now':
            players_for_round = request.POST.getlist('add_to_round[]')
            for each_round in ladder_rounds:
                for player in players_for_round:
                    add_player_to_round(each_round.id, player)
                # Round status is set to open when players are added.
                # This allows for players to manage themselves
                each_round.status = each_round.OPEN
                each_round.save()

        return redirect(ladder_admin)

    players = Player.objects.all().filter(status=Player.ACTIVE).order_by('ranking')
    context = {
        'players': players
    }
    return render(request, 'round/ladder_setup_wizard.html', context)


def download_match_schedule(request, round_id):
    """
    Download the match schedule
    """
    ladder_round = LadderRound.objects.get(id=round_id)
    filename = 'round_match_schedule.pdf'
    pdf_file = get_pdf_match_schedule(ladder_round)
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
import json
from django import forms
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from .models import PlayersInLadderRound
from .models import LadderRound
from .models import Match
from .models import Ladder
from .models import Match
from .models import MatchResult
from .models import PlayerRanking
from .models import MatchSchedule
from .models import RoundMatchSchedule
from datetime import date, datetime
from .forms import LadderForm, LadderRoundForm, MatchForm, LadderStatusForm
from players.models import Player
from .utils import validate_match_results, get_players_in_round, get_players_not_in_round, setup_matches_for_draw, \
    add_player_to_round, compare_and_update_player_with_playerranking, get_full_ladder_details, \
    remove_player_from_round, is_int, add_intervals_to_start_time, get_number_of_timeslots, \
    create_match_schedule_with_round_match_schedule, validate_and_create_ladder_round, re_open_round, \
    save_scheduled_matches, save_scheduled_match
from round.utils import calculate_change_in_ranking, update_ladder_ranking, matches_player_played_in, date_range
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
    ladder_round = LadderRound.objects.get(id=round_id)
    players = get_players_in_round(ladder_round)
    if ladder_round.status == ladder_round.CLOSED:
        matches = Match.objects.filter(ladder_round=ladder_round)
    else:
        matches = None
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
    ladder = ladder_round.ladder
    ladder_rounds = LadderRound.objects.filter(ladder=ladder_round.ladder)
    previous_round = LadderRound.objects.filter(ladder=ladder).exclude(id=ladder_round.id).order_by(
        '-start_date').first()
    players_in_previous_round = get_players_in_round(previous_round)
    number_of_players_in_previous_round = len(players_in_previous_round)

    if request.POST.get('copy_players'):
        for player_in_previous_round in players_in_previous_round:
            add_player_to_round(ladder_round.id, player_in_previous_round)
        return redirect(add_players_to_round, ladder_round.id)
    if request.POST.get("view_draw"):
        return redirect(round_draw, ladder_round.id)
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
    ladder_round = LadderRound.objects.get(id=round_id)
    ladder_rounds = LadderRound.objects.filter(ladder=ladder_round.ladder)
    players = get_players_in_round(ladder_round)
    matches = Match.objects.filter(ladder_round=ladder_round)
    if not matches:
        matches = setup_matches_for_draw(ladder_round, players)

    if len(players) % 2 != 0:
        messages.warning(request, 'The number of players in the draw is uneven, please add or remove someone')
    context = {
        'ladder_round': ladder_round,
        'ladder_rounds': ladder_rounds,
        'players': players,
        'matches': matches
    }
    return render(request, 'round/draw.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def close_draw(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    if ladder_round.status < ladder_round.CLOSED:
        if LadderRound.objects.filter(status=ladder_round.CLOSED):
            messages.error(request, 'Two rounds cannot be closed (in progress) at the same time')
        else:
            ladder_round.status = ladder_round.CLOSED  # Closed
            ladder_round.save()
            players = get_players_in_round(ladder_round)
            matches = setup_matches_for_draw(ladder_round, players)
            for each in matches:
                each.save()
        return redirect(round_draw, ladder_round.id)
    else:
        messages.warning(request, 'The round is not open for changes')
    return redirect(round_draw, ladder_round.id)


@permission_required('round.ladder.can_administrate_the_ladder')
def capture_results(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    if ladder_round.status < 2:
        messages.warning(request, 'Draw is not yet finalised.  Please finalise the draw before capturing the results.')
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


@permission_required('round.ladder.can_administrate_the_ladder')
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


@permission_required('round.ladder.can_administrate_the_ladder')
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


@permission_required('round.ladder.can_administrate_the_ladder')
def schedule_matches(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    non_scheduled_matches = []
    for each_match in matches:
        if not MatchSchedule.objects.filter(match=each_match):
            non_scheduled_matches.append(each_match)
    saved_matches_schedule = MatchSchedule.objects.filter(ladder_round=ladder_round)
    schedule = ladder_round.match_schedule
    if schedule:
        pass
    else:
        messages.error(request, 'Please setup a schedule before schedulding matches')
        return redirect(setup_scheduling_for_round, ladder_round.id)
    if request.POST:
        scheduled_matches = json.loads(request.POST.get('scheduled-matches'))
        # todo Validate that match_day is between the start and end dates of the ladder_round
        save_scheduled_matches(ladder_round, scheduled_matches)

        print(scheduled_matches)

    context = {
        'ladder_round': ladder_round,
        'matches': non_scheduled_matches,
        'schedule': schedule,
        'saved_matches_schedule': saved_matches_schedule
    }
    return render(request, 'round/schedule_matches.html', context)


@permission_required('round.ladder.can_administrate_the_ladder')
def setup_scheduling_for_round(request, round_id):
    ladder_round = LadderRound.objects.get(id=round_id)
    ladder = ladder_round.ladder
    ladder_rounds = LadderRound.objects.filter(ladder=ladder)
    start_date = ladder_round.start_date
    end_date = ladder_round.end_date
    delta = end_date - start_date
    days = date_range(start_date, end_date)
    if request.POST:
        if request.POST.get('generate-match-schedule'):
            match_days = ','.join(request.POST.getlist('match-day[]'))
            number_of_courts = int(request.POST.get('number-of-courts'))
            start_time = datetime.strptime(request.POST.get('start-time'), '%H:%M').time()
            time_interval = request.POST.get('time-interval')
            number_of_games = request.POST.get('number-of-games')

            if is_int(number_of_games):
                number_of_games = int(number_of_games)
            else:
                number_of_games = 0

            if number_of_games > 0:
                number_of_time_slots = int(float(number_of_games) / float(number_of_courts) + 1)

                end_time = add_intervals_to_start_time(start_time, time_interval, int(number_of_time_slots))

                print(f'end time: {end_time.strftime("%H:%M")}')
            else:
                end_time = datetime.strptime(request.POST.get('end-time'), '%H:%M').time()
            number_of_timeslots = get_number_of_timeslots(start_time, end_time, time_interval)
            round_match_schedule = RoundMatchSchedule.objects.create(match_days=match_days,
                                                                     number_of_courts=number_of_courts,
                                                                     start_time=start_time,
                                                                     end_time=end_time,
                                                                     number_of_timeslots=number_of_timeslots,
                                                                     time_interval=int(time_interval))
            round_match_schedule.save()
            ladder_round.match_schedule = round_match_schedule
            ladder_round.save()
            create_match_schedule_with_round_match_schedule(ladder_round, round_match_schedule)
            print(f'schedule: {round_match_schedule}')
        elif request.POST.get('reset-schedule'):
            matches_schedule = MatchSchedule.objects.filter(ladder_round=ladder_round)
            for each in matches_schedule:
                each.delete()
            ladder_round.match_schedule = None
            ladder_round.save()
        elif request.POST.get('commit-schedule'):
            return redirect(add_players_to_round, ladder_round.id)
        return redirect(setup_scheduling_for_round, ladder_round.id)

    matches_schedule = MatchSchedule.objects.filter(ladder_round=ladder_round).order_by('day').order_by('time_slot')

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
    ladder_round = LadderRound.objects.get(id=round_id)
    matches = Match.objects.filter(ladder_round=ladder_round)
    match_schedule = ladder_round.match_schedule
    scheduled_matches = MatchSchedule.objects.filter(ladder_round=ladder_round).exclude(match__isnull=True)
    ladder_rounds = list(LadderRound.objects.filter(ladder=ladder_round.ladder).order_by('start_date'))
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
    ladder = Ladder.objects.get(id=ladder_id)
    ladder_rounds = LadderRound.objects.filter(ladder=ladder)
    last_round = LadderRound.objects.filter(ladder=ladder).order_by('-end_date').first()
    if request.POST:
        # todo validate the dates
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
        try:
            ladder_round = validate_and_create_ladder_round(ladder, start_date, end_date)
        except ValueError as e:
            messages.error(request, f'{e}')
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
    response_data = {}
    ladder_round = LadderRound.objects.get(id=round_id)
    if request.POST:
        if request.POST.get('save'):
            match_id = request.POST.get("match_id")
            match_time = request.POST.get("match_time")
            match_day = request.POST.get("match_day")
            court = request.POST.get("court")
            try:
                scheduled_match = MatchSchedule.objects.get(match_id=match_id)
                scheduled_match.delete()
            except ObjectDoesNotExist:
                pass
            finally:
                scheduled_match = save_scheduled_match(ladder_round, match_id, match_day, court, match_time)
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

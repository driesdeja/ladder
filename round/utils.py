import json
from collections import namedtuple
from django.db import IntegrityError
from .models import PlayersInLadderRound, \
    PlayerRanking, \
    Ladder, \
    LadderRound, \
    Match, \
    MatchSchedule, \
    RoundMatchSchedule

from players.models import Player
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


def get_players_in_round(ladder_round):
    players_in_round = PlayersInLadderRound.objects.filter(ladder_round=ladder_round)
    players = []
    for player in players_in_round:
        players.append(player.player)
    players.sort(key=lambda x: x.ranking)
    return players


def get_players_not_in_round(players_in_round):
    players = Player.objects.all()
    players_not_in_round = []
    for player in players:
        if player not in players_in_round:
            players_not_in_round.append(player)
    players_not_in_round.sort(key=lambda x: x.ranking)
    return players_not_in_round


def setup_matches_for_draw(ladder_round, players):
    matches = []
    for x in range(0, len(players), 2):
        match = Match()
        match.ladder_round = ladder_round
        match.player1 = players[x]
        if x + 1 >= len(players):
            print(str(players[x]) + 'player 2: None')
        else:
            print(str(players[x]) + 'player 2: ' + str(players[x + 1]))
            match.player2 = players[x + 1]
        matches.append(match)
    return matches


def validate_match_results(match):
    messages = []
    if match.result == match.CANCELLED:
        match.games_for_player1 = 0
        match.games_for_player2 = 0
    else:
        if match.result == match.PLAYER_1_DEFAULTED:
            match.games_for_player2 = 3
        if match.result == match.PLAYER_2_DEFAULTED:
            match.games_for_player1 = 3
        if match.games_for_player1 == 3 and match.games_for_player2 == 3:
            messages.append(
                match.player1.first_name + ' and ' + match.player2.first_name + ' cannot both have won 3 games.')
        if match.games_for_player1 == 3 and match.result == match.PLAYER_1_DEFAULTED:
            messages.append('Player 1 cannot win 3 games and default the game.')
        if match.games_for_player2 == 3 and match.result == match.PLAYER_2_DEFAULTED:
            messages.append('Player 2 cannot win 3 games and default the game.')
        if match.games_for_player1 < 3 and match.games_for_player2 < 3:
            if not (match.games_for_player1 == 3 or match.games_for_player2 == 3):
                messages.append('At least 1 player must have the winning number of sets (3)')
    return messages


'''The purpose of this function is to ensure that no duplicate player exist in the LadderRound
It will all'''


def ensure_player_not_already_in_round(ladder_round, player):
    same_players_in_round = PlayersInLadderRound.objects.filter(player=player, ladder_round=ladder_round)
    if len(same_players_in_round) > 0:
        for same_player_in_round in same_players_in_round:
            same_player_in_round.delete()


def add_player_to_round(round_id, player):
    player_to_add = PlayersInLadderRound()
    ladder_round = LadderRound.objects.get(id=round_id)
    if isinstance(player, Player):
        player_to_add.player = player
    else:
        player_to_add.player = Player.objects.get(id=player)
    ensure_player_not_already_in_round(ladder_round, player_to_add.player)
    player_to_add.ladder_round = ladder_round
    player_to_add.save()


def remove_player_from_round(round_id, player):
    ladder_round = LadderRound.objects.get(id=round_id)
    if isinstance(player, Player):
        player_to_remove = PlayersInLadderRound.objects.get(player=player, ladder_round=ladder_round)
    else:
        player_to_remove = PlayersInLadderRound.objects.get(player=Player.objects.get(id=player),
                                                            ladder_round=ladder_round)
    player_to_remove.delete()


def update_ladder_ranking(player, action, new_ranking):
    """This action only occurs when a player is added for the first time."""
    if action == 'add':
        today = datetime.now()
        '''If the new player's ranking in 0 then we add him to the end of the ranking list)'''
        if new_ranking == 0:
            players = Player.objects.all()
            player.ranking = len(players)
        else:
            players = Player.objects.filter(ranking__gte=new_ranking).order_by('ranking')
            player.ranking = new_ranking
            for each_player in players:
                each_player.ranking = each_player.ranking + 1
                each_player_ranking = PlayerRanking()
                each_player_ranking.player = each_player
                each_player_ranking.ranking = each_player.ranking
                each_player_ranking.reason_for_change = \
                    f'{player.first_name} {player.last_name} added to the ladder {today}.'
                if activate_and_invalidate_ranking(each_player_ranking):
                    each_player_ranking.save()
                    each_player.save()
                else:
                    raise

        """Insert log entry for the update of the ranking"""
        ranking = PlayerRanking()
        ranking.player = player
        ranking.ranking = player.ranking
        ranking.reason_for_change = 'Initial creation of the the player'
        if activate_and_invalidate_ranking(ranking):
            player.save()
            ranking.save()
        else:
            raise
    if action == 'delete':
        players = Player.objects.filter(ranking__gt=player.ranking).order_by('ranking')
        for each_player in players:
            each_player.ranking = each_player.ranking - 1
            each_player.save()
    if action == 'change':
        if new_ranking <= 0:
            new_ranking = 1
        if player.ranking > new_ranking:
            players = Player.objects.filter(ranking__gte=new_ranking).filter(ranking__lt=player.ranking)
            for each_player in players:
                each_player.ranking = each_player.ranking + 1
                each_player.save()
            player.ranking = new_ranking
            player.save()
        else:
            if player.ranking < new_ranking:
                if player.ranking != 0:
                    players = Player.objects.filter(ranking__gt=player.ranking).filter(ranking__lte=new_ranking)
                    for each_player in players:
                        each_player.ranking = each_player.ranking - 1
                        each_player.save()
                    if new_ranking > players[len(players) - 1].ranking:
                        new_ranking = players[len(players) - 1].ranking + 1
                    player.ranking = new_ranking
                    player.save()
                else:
                    players = Player.objects.filter(ranking__gte=new_ranking).order_by('ranking')
                    for each_player in players:
                        each_player.ranking = each_player.ranking + 1
                        each_player.save()
                    player.ranking = new_ranking
                    player.save()


def ranking_change(games_won):
    if games_won == 0:
        player_ranking_change = 1
    elif games_won == 1:
        player_ranking_change = 0
    elif games_won == 2:
        player_ranking_change = -2
    elif games_won == 3:
        player_ranking_change = -4
    else:
        raise ValueError(f'Games won must be between 0 and 3 and not {games_won}!')
    return player_ranking_change


def setup_player_for_ranking_change(player, games_won):
    player_ranking_change = ranking_change(games_won)

    player_ranking = {
        'player_id': player.id,
        'player_name': player.first_name + ' ' + player.last_name,
        'player_current_ranking': player.ranking,
        'player_ranking_change': player_ranking_change
    }
    return player_ranking


def calculate_change_in_ranking(matches):
    new_ranking_list = []
    for match in matches:
        player_ranking = setup_player_for_ranking_change(match.player1, match.games_for_player1)
        new_ranking_list.append(player_ranking)
        player_ranking = setup_player_for_ranking_change(match.player2, match.games_for_player2)
        new_ranking_list.append(player_ranking)
    return new_ranking_list


def activate_and_invalidate_ranking(ranking):
    now = datetime.now()
    # Find the currently active ranking
    current_ranking = PlayerRanking.objects.filter(player=ranking.player, eff_to__isnull=True).first()
    # If there is no previous PlayerRanking, only happens if it is a new player -
    # ranking will then be the first PlayerRanking
    if current_ranking:
        current_ranking.eff_to = now
    ranking.eff_from = now
    return True


"""
    This function assumes that the player.ranking is the most accurate.
    The reason_why should be descriptive enough to explain the potential update in ranking
"""


def compare_and_update_player_with_playerranking(reason_for_change):
    players = Player.objects.all()
    for player in players:
        player_ranking = PlayerRanking.objects.filter(player=player, eff_to__isnull=True).first()
        now = datetime.now()
        # if there is a record in PlayerRanking
        if player_ranking:
            if player.ranking != player_ranking.ranking:
                new_player_ranking = PlayerRanking()
                new_player_ranking.eff_from = now
                new_player_ranking.ranking = player.ranking
                player_ranking.eff_to = now
                new_player_ranking.player = player_ranking.player
                if len(reason_for_change) > 0:
                    new_player_ranking.reason_for_change = reason_for_change
                player_ranking.save()
                new_player_ranking.save()
        # if there is no record for the player in PlayerRanking, this should rarely happen, but due to the decoupling
        # it is possible to create a new Player and not have a ranking in the PlayerRanking log
        else:
            player_ranking = PlayerRanking()
            player_ranking.eff_from = now
            player_ranking.player = player
            player_ranking.reason_for_change = reason_for_change
            player_ranking.ranking = player.ranking
            player_ranking.save()
    return True


def matches_player_played_in(player, ladder):
    # todo: This is not the best way but it kinda works for now.
    # need to be smarter on how to do this, polymorphism is dead!
    if ladder is None:
        matches_played_in_as_player1 = Match.objects.filter(player1=player, result__gt=Match.NOT_PLAYED).order_by(
            '-last_updated')
        matches_played_in_as_player2 = Match.objects.filter(player2=player, result__gt=Match.NOT_PLAYED).order_by(
            '-last_updated')
    else:
        ladder_id = ladder.id

        ladder_rounds = list(LadderRound.objects.filter(ladder=ladder))

        matches_played_in_as_player1 = Match.objects.filter(player1=player, result__gt=Match.NOT_PLAYED,
                                                            ladder_round__in=ladder_rounds).order_by(
            '-last_updated')
        matches_played_in_as_player2 = Match.objects.filter(player2=player, result__gt=Match.NOT_PLAYED,
                                                            ladder_round__in=ladder_rounds).order_by(
            '-last_updated')

    all_matches = []

    for match in matches_played_in_as_player1:
        result = get_match_result(match, 1)

        all_matches.append({
            'ladder_id': ladder.id,
            'ladder_round_id': match.ladder_round.id,
            'ladder_round': match.ladder_round.start_date,
            'date_played': match.date_played,
            'opponent': f'{match.player2.first_name} {match.player2.last_name}',
            'opponent_id': match.player2.id,
            'games_for': match.games_for_player1,
            'games_against': match.games_for_player2,
            'result': result
        })
    for match in matches_played_in_as_player2:
        result = get_match_result(match, 2)
        all_matches.append({
            'ladder_id': ladder.id,
            'ladder_round_id': match.ladder_round.id,
            'ladder_round': match.ladder_round.start_date,
            'date_played': match.date_played,
            'opponent': f'{match.player1.first_name} {match.player1.last_name}',
            'opponent_id': match.player1.id,
            'games_for': match.games_for_player2,
            'games_against': match.games_for_player1,
            'result': result
        })
    all_matches = sorted(all_matches, key=lambda x: x['date_played'], reverse=True)
    return all_matches


def get_match_result(match, player_number):
    result = ''
    if player_number == 1:
        if match.result == match.PLAYER_1_WON:
            result = 'Won'
        elif match.result == match.PLAYER_2_WON:
            result = 'Loss'
        elif match.result == match.PLAYER_1_DEFAULTED:
            result = 'Loss by default'
        elif match.result == match.PLAYER_2_DEFAULTED:
            result = 'Won by default'
        elif result == match.CANCELLED:
            result = 'Cancelled'
        elif result == match.NOT_PLAYED:
            result == 'Not played'
    if player_number == 2:
        if match.result == match.PLAYER_1_WON:
            result = 'Loss'
        elif match.result == match.PLAYER_2_WON:
            result = 'Won'
        elif match.result == match.PLAYER_1_DEFAULTED:
            result = 'Won by default'
        elif match.result == match.PLAYER_2_DEFAULTED:
            result = 'Loss by default'
        elif result == match.CANCELLED:
            result = 'Cancelled'
        elif result == match.NOT_PLAYED:
            result == 'Not played'

    return result


def get_full_ladder_details(ladder):
    full_details = {}
    # Get all the players who have entered the ladder
    all_player_matches = []
    #if LadderRound.objects.filter(ladder=ladder, status__in=[LadderRound.CREATED, LadderRound.OPEN, LadderRound.CLOSED, LadderRound.COMPLETED]).exists():
    all_rounds = LadderRound.objects.filter(ladder=ladder, status__in=[LadderRound.CREATED, LadderRound.OPEN, LadderRound.CLOSED, LadderRound.COMPLETED]) \
        .order_by('start_date')
    all_players = list(Player.objects.all().order_by('ranking'))
    for each_player in all_players:
        player_matches = matches_player_played_in(each_player, ladder)
        rounds_player_had_matches = []
        for each_round in all_rounds:
            for each_match in player_matches:
                if each_round.id == each_match['ladder_round_id']:
                    rounds_player_had_matches.append({'round_id': each_round.id,
                                                      'games_for': each_match['games_for'],
                                                      'result': each_match['result']})

        all_player_matches.append({'player_id': each_player.id,
                                   'player_ranking': each_player.ranking,
                                   'player_name': f'{each_player.first_name} {each_player.last_name}',
                                   'games': rounds_player_had_matches})
        # get all the rounds for the ladder
        # get all the results for the rounds that are complete
        # for player in all_players:
    return all_player_matches


def fix_date_played(matches):
    for match in matches:
        if match.date_played is None:
            match.date_played = datetime.today()
            match.save()
    return True


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + timedelta(n)


def validate_round_match_schedule(round_match_schedule):
    return True


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def add_intervals_to_start_time(start_time, interval, number_of_intervals):
    if isinstance(start_time, datetime):
        start_time_time_obj = start_time
    else:
        start_time_time_obj = datetime.strptime(start_time, '%H:%M')
    total_minutes = int(interval) * int(number_of_intervals)
    end_time = start_time_time_obj + timedelta(minutes=total_minutes)
    return end_time.time()


def create_match_schedule_with_round_match_schedule(ladder_round, round_match_schedule):
    match_days = round_match_schedule.match_days.split(',')
    for each_day in match_days:
        year = ladder_round.start_date.year
        day_of_year = datetime(year, 1, 1) + timedelta(int(each_day) - 1)
        start_time = round_match_schedule.start_time
        for each_time in range(round_match_schedule.number_of_timeslots):
            for each_court in range(round_match_schedule.number_of_courts):
                match_schedule = MatchSchedule.objects.create(day=day_of_year,
                                                              court=each_court + 1,
                                                              time_slot=start_time,
                                                              ladder_round=ladder_round)
                print(f'match_Schedule: {match_schedule}')
                match_schedule.save()
            start_time = add_minutes(start_time, round_match_schedule.time_interval)


def get_number_of_timeslots(start_time, end_time, time_interval):
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M')
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M')
    if isinstance(time_interval, str):
        time_interval = int(time_interval)
    start_time_delta = start_time.hour
    end_time_delta = end_time.hour
    diff = end_time_delta - start_time_delta
    minutes = diff * 60
    number_of_timeslots = int(minutes / time_interval)
    return number_of_timeslots


def add_minutes(tm, minutes):
    full_date = datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    full_date = full_date + timedelta(minutes=minutes)
    return full_date.time()


def validate_and_create_ladder_round(ladder, start_date, end_date):
    ladder_rounds = LadderRound.objects.filter(ladder=ladder)
    ladder_round = LadderRound(start_date=start_date, end_date=end_date, ladder=ladder)

    if not start_date >= ladder.start_date:
        raise ValueError(
            f'The round can only start after the ladder started. Check the start date of the round.'
            f'First day of the round is: {start_date}, end_date: {end_date} ')
    if not start_date >= date.today():
        raise ValueError(
            f'Rounds can only be future dated. The selected start date is in the past ({datetime.strftime(start_date, "%d %b")}) ,'
            f' today\'s date is : {datetime.strftime(datetime.today(), "%d %b")}')
    ladder_rounds = list(
        LadderRound.objects.filter(ladder=ladder).filter(end_date__gte=start_date))

    if len(ladder_rounds) > 0:
        raise ValueError(
            f'Rounds may not overlap.  '
            f'The selected start date for this round is before the end date of a previous round\'s end date!: '
            f'This round\'s start date:  {datetime.strftime(start_date, "%d %b")} '
            f'overlaps with end date of previous round: {datetime.strftime(ladder_rounds[0].end_date, "%d %b")}'
        )
    return ladder_round


def re_open_round(ladder_round):
    matches = Match.objects.filter(ladder_round=ladder_round)
    if matches:
        for match in matches:
            match.delete()
    ladder_round.status = ladder_round.OPEN
    ladder_round.save()
    return True


def date_for_day_of_the_year(day_of_the_year, year):
    if isinstance(day_of_the_year, str):
        day_of_the_year = int(day_of_the_year)
    if isinstance(year, str):
        year = int(year)

    return datetime(year, 1, 1) + timedelta(days=day_of_the_year - 1)


def save_scheduled_matches(ladder_round, scheduled_matches):
    counter = 0
    # each save is a new schedule so it is important to delete all previous scheduled matches for the ladder_round
    historic_matches = MatchSchedule.objects.filter(ladder_round=ladder_round)
    if historic_matches:
        for historic_match in historic_matches:
            historic_match.delete()
    for each_day in scheduled_matches:
        for match in each_day['matches']:
            match_schedule = save_scheduled_match(ladder_round, match['match'], each_day['day'], match['court'],
                                                  match['timeslot'])
            counter += 1
    return counter


def save_scheduled_match(ladder_round, match_id, day, court, timeslot):
    round_match_schedule = RoundMatchSchedule.objects.get(ladderround=ladder_round)
    days = len(round_match_schedule.match_days.split(','))
    start_time = round_match_schedule.start_time
    time_slot = datetime.strptime(timeslot, '%H:%M').time()
    time_slot_in_min = time_slot.hour * 60 + time_slot.minute
    start_time_in_min = start_time.hour * 60 + start_time.minute
    time_difference_in_min = time_slot_in_min - start_time_in_min

    print(f'Time slot: {time_slot_in_min} - start_time: {start_time_in_min} = {time_difference_in_min}')
    row = (time_difference_in_min) / round_match_schedule.time_interval
    column = court
    print(f'column: {column} + number_of_courts: {round_match_schedule.number_of_courts} * (row-1) ({row} - 1)')
    grid_location = int(column) + int(round_match_schedule.number_of_courts * (row))
    print(f'Gridlocation: {grid_location}')
    match_schedule = MatchSchedule(
        day=date_for_day_of_the_year(day, ladder_round.start_date.strftime('%Y')),
        court=court,
        time_slot=datetime.strptime(timeslot, '%H:%M').time(),
        match=Match.objects.get(id=match_id),
        ladder_round=ladder_round,
        time_grid_location=grid_location)
    match_schedule.save()
    return match_schedule


def validate_and_create_ladder_rounds(ladder, number_of_rounds, first_round_start_date, duration_of_round):
    print(f'{type(ladder.start_date)}')
    print(f'{type(first_round_start_date)}')
    try:
        if duration_of_round == 'weekly':
            time_duration_of_a_round = timedelta(weeks=1)
        elif duration_of_round == 'fortnightly':
            time_duration_of_a_round = timedelta(weeks=2)

        if first_round_start_date:
            start_date = first_round_start_date
        else:
            start_date = ladder.start_date

        if number_of_rounds == "":
            if ladder.end_date is None:
                raise ValueError('The number_of_rounds OR the ladder.end_date must be set!')
            else:
                time_duration_of_a_round = None
                # If the number of rounds and ladder.end_date is selected then the number of of rounds takes precedence
                # calculate the number of rounds based on the length of the ladder (end_date - start_date)/duration_of_round
                time_difference = (ladder.end_date - ladder.start_date)
                if duration_of_round == 'weekly':
                    number_of_rounds = int(time_difference.days / 7)
                elif duration_of_round == 'fortnightly':
                    number_of_rounds = int(time_difference.days / 14)
                elif duration_of_round == 'monthly':
                    number_of_rounds = int(time_difference.days / 30)
                else:
                    number_of_rounds = 1

            print(f'Number of rounds: {number_of_rounds}')
        ladder_rounds = []

        for i in range(number_of_rounds):
            end_date = get_round_end_date(start_date, duration_of_round)
            ladder_round = LadderRound(
                ladder=ladder,
                start_date=start_date,
                end_date=end_date,
            )
            ladder_round.save()
            ladder_rounds.append(ladder_round)
            start_date = end_date + timedelta(days=1)

        return ladder_rounds
    except ValueError as error:
        raise error


def get_round_end_date(start_date, duration_of_round):
    end_date = None
    if duration_of_round == 'weekly':
        time_duration_of_a_round = timedelta(days=6)
        end_date = start_date + time_duration_of_a_round
    elif duration_of_round == 'fortnightly':
        time_duration_of_a_round = timedelta(days=13)
        end_date = start_date + time_duration_of_a_round
    elif duration_of_round == 'monthly':
        end_date = start_date + relativedelta(months=+1)
        end_date = end_date - timedelta(days=1)
    print(f'start_date: {start_date}, end_date: {end_date}')
    return end_date


def generate_round_match_schedule(match_days, number_of_courts, start_time, end_time, time_interval, number_of_games):
    if isinstance(match_days, list):
        match_days_str = ",".join(map(str, match_days))
    if is_int(number_of_games):
        number_of_games = int(number_of_games)
    else:
        number_of_games = 0

    if number_of_games > 0:
        number_of_time_slots = int(float(number_of_games) / float(number_of_courts) + 1)

        end_time = add_intervals_to_start_time(start_time, time_interval, int(number_of_time_slots))

    number_of_timeslots = get_number_of_timeslots(start_time, end_time, time_interval)
    round_match_schedule = RoundMatchSchedule.objects.create(match_days=match_days_str,
                                                             number_of_courts=number_of_courts,
                                                             start_time=start_time,
                                                             end_time=end_time,
                                                             number_of_timeslots=number_of_timeslots,
                                                             time_interval=int(time_interval))
    round_match_schedule.save()

    return round_match_schedule


def validate_and_create_ladder(ladder_name, ladder_start_date, ladder_end_date):
    if ladder_name:
        ladder = Ladder(
            title=ladder_name
        )
        ladder.start_date = datetime.strptime(ladder_start_date, '%Y-%m-%d').date()
        if ladder_end_date:
            ladder.end_date = datetime.strptime(ladder_end_date, '%Y-%m-%d').date()

        try:
            ladder.status = ladder.OPEN
            ladder.save()
        except IntegrityError:
            raise ValueError(f'The supplied title is not unique: {ladder_name}')
        return ladder
    else:
        raise ValueError(f'The name of the ladder needs to be set cannot be None: {ladder_name}')


'''
function used to determine the day of the year for the days of the week selected based on the start date
of the round.  This is needed because the RoundMatchSchedule is constructed with the day of the year rather than the day
 of the week.
 
Function returns a list of the match days as day of the year
'''


def setup_match_days(round_start_date, week_days):
    match_days = []
    round_start_week_day = round_start_date.weekday()
    round_start_date_day_of_year = round_start_date.timetuple().tm_yday
    print(f'day of the week the ladder round starts on: {round_start_week_day}')
    days_of_the_week = map(convert_list_of_day_names_to_day_of_week, week_days)
    for day in days_of_the_week:
        if round_start_week_day > day:
            diff = round_start_week_day - day
            day_of_match_day = round_start_date_day_of_year - diff + 7
            match_days.append(day_of_match_day)
        elif round_start_week_day < day:
            diff = day - round_start_week_day
            day_of_match_day = round_start_date_day_of_year + diff
            match_days.append(day_of_match_day)
        elif round_start_week_day == day:
            match_days.append(round_start_date_day_of_year)

    return match_days


def convert_list_of_day_names_to_day_of_week(week_day):

    if week_day == 'Monday':
        return 0
    elif week_day == 'Tuesday':
        return 1
    elif week_day == 'Wednesday':
        return 2
    elif week_day == 'Thursday':
        return 3
    elif week_day == 'Friday':
        return 4
    elif week_day == 'Saturday':
        return 5
    elif week_day == 'Sunday':
        return 6
    else:
        raise ValueError(f'The value does not appear to be a day of the week: {week_day}')


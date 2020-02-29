from .models import PlayersInLadderRound, PlayerRanking
from .models import Ladder
from .models import LadderRound
from .models import Match
from players.models import Player
from datetime import datetime


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


def ensure_player_not_already_in_round(round_id, player):
    same_players_in_round = PlayersInLadderRound.objects.filter(player=player)
    if len(same_players_in_round) > 0:
        for each_player in same_players_in_round:
            same_players_in_round.delete()


def add_player_to_round(round_id, player):
    player_to_add = PlayersInLadderRound()
    ladder_round = LadderRound.objects.get(id=round_id)
    if isinstance(player, Player):
        player_to_add.player = player
    else:
        player_to_add.player = Player.objects.get(id=player)
    ensure_player_not_already_in_round(round_id, player_to_add.player)
    player_to_add.ladder_round = ladder_round
    player_to_add.save()


def remove_player_from_round(round_id, player):
    if isinstance(player, Player):
        player_to_remove = PlayersInLadderRound.objects.get(player=player)
    else:
        player_to_remove = PlayersInLadderRound.objects.get(player=Player.objects.get(id=player))
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
        player_ranking_change = -1
    elif games_won == 3:
        player_ranking_change = -2
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
        matches_played_in_as_player1 = Match.objects.filter(player1=player) \
            .filter(result__gt=Match.NOT_PLAYED) \
            .order_by('-last_updated')

        matches_played_in_as_player2 = Match.objects.filter(player2=player) \
            .filter(result__gt=Match.NOT_PLAYED) \
            .order_by('-last_updated')
    else:
        ladder_rounds = LadderRound.objects.all().filter(ladder=ladder)
        matches_played_in_as_player1 = Match.objects.filter(player1=player) \
            .filter(result__gt=Match.NOT_PLAYED) \
            .filter(ladder_round__in=ladder_rounds) \
            .order_by('-last_updated')

        matches_played_in_as_player2 = Match.objects.filter(player2=player) \
            .filter(result__gt=Match.NOT_PLAYED) \
            .filter(ladder_round__in=ladder_rounds) \
            .order_by('-last_updated')
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
    all_rounds = LadderRound.objects.all().filter(ladder=ladder).filter(
        status__in=[LadderRound.CREATED, LadderRound.OPEN, LadderRound.CLOSED, LadderRound.COMPLETED]) \
        .order_by('start_date')
    all_players = list(Player.objects.all().order_by('ranking'))
    for each_player in all_players:
        player_matches = matches_player_played_in(each_player, ladder)
        rounds_player_had_matches = []
        for each_round in all_rounds:
            games = []
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

    full_details = {'title': ladder.title,
                    'start_date': ladder.start_date,
                    'rounds': [{
                        'test': 'test'
                    }]}
    return all_player_matches


def fix_date_played(matches):
    for match in matches:
        if match.date_played is None:
            match.date_played = datetime.today()
            match.save()
    return True

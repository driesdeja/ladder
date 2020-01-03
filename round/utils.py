from .models import PlayersInLadderRound
from .models import Ladder
from .models import LadderRound
from .models import Match
from players.models import Player


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
    if match.games_for_player1 == 3 and match.games_for_player2 == 3:
        messages.append(match.player1.first_name + ' and ' + match.player2.first_name + ' cannot both have won 3 games.')
    if match.games_for_player1 == 3 and match.result == match.PLAYER_1_DEFAULTED:
        messages.append('Player 1 cannot win 3 games and default the game.')
    if match.games_for_player2 == 3 and match.result == match.PLAYER_2_DEFAULTED:
        messages.append('Player 2 cannot win 3 games and default the game.')
    if match.games_for_player1 < 3 and match.games_for_player2 < 3:
        if not (match.games_for_player1 == 3 or match.games_for_player2 == 3):
            messages.append('At least 1 player must have the winning number of sets (3)')
    return messages

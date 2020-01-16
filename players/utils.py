from .models import Player


def update_ladder_ranking(player, action, new_ranking):
    if new_ranking <= 0:
        new_ranking = 1
    if action == 'add':
        '''Select all players where their current ranking is equal or higher than the new players ranking '''
        players = Player.objects.filter(ranking__gte=new_ranking).order_by('ranking')
        '''If the new player's ranking in 0 then we make him no 1 and move everyone else one down the ranking (increase
        their ranking with one)'''
        print(len(players))
        print(players[len(players) - 1])
        if new_ranking == 0:
            player.ranking = len(players) + 1
        else:
            player.ranking = new_ranking
            for each_player in players:
                each_player.ranking = each_player.ranking + 1
                each_player.save()
        player.save()

    if action == 'delete':
        players = Player.objects.filter(ranking__gt=player.ranking).order_by('ranking')
        for each_player in players:
            each_player.ranking = each_player.ranking - 1
            each_player.save()
    if action == 'change':
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
                    player.ranking = new_ranking
                    player.save()
                else:
                    players = Player.objects.filter(ranking__gte=new_ranking).order_by('ranking')
                    for each_player in players:
                        each_player.ranking = each_player.ranking + 1
                        each_player.save()
                    player.ranking = new_ranking
                    player.save()

def sort_by_ranking(player):
    return player.ranking


def ranking_change(games_won):
    if games_won == 0:
        player_ranking_change = 1
    elif games_won == 1:
        player_ranking_change = 0
    elif games_won == 2:
        player_ranking_change = -1
    elif games_won == 3:
        player_ranking_change = -2
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

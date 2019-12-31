from .models import Player


def update_ladder_ranking(player, action, new_ranking):
    if action == 'add':
        '''Select all players where their current ranking is equal or higher than the new players ranking '''
        players = Player.objects.filter(ranking__gte=new_ranking).order_by('ranking')
        '''If the new player's ranking in 0 then we make him no 1 and move everyone else one down the ranking (increase
        their ranking with one)'''
        print(len(players))
        print(players[len(players)-1])
        if new_ranking == 0:
            player.ranking = len(players)+1
        else:
            player.ranking = new_ranking
            for each_player in players:
                each_player.ranking = each_player.ranking + 1
                each_player.save()
        player.save()

    if action == 'delete':
        players = Player.objects.filter(ranking__gt=player.ranking).order_by('ranking')
        for each_player in players:
            each_player.ranking = each_player.ranking-1
            each_player.save()
    if action == 'change':
        if player.ranking > new_ranking:
            players = Player.objects.filter(ranking__gte=new_ranking).filter(ranking__lt=player.ranking)
            for each_player in players:
                each_player.ranking = each_player.ranking+1
                each_player.save()
            player.ranking = new_ranking
        else:
            if player.ranking < new_ranking:
                if player.ranking != 0:
                    players = Player.objects.filter(ranking__gt=player.ranking).filter(ranking__lte=new_ranking)
                    for each_player in players:
                        each_player.ranking = each_player.ranking-1
                        each_player.save()
                    player.ranking = new_ranking
                else:
                    players = Player.objects.filter(ranking__gte=new_ranking).order_by('ranking')
                    for each_player in players:
                        each_player.ranking = each_player.ranking + 1
                        each_player.save()
                    player.ranking = new_ranking


def sort_by_ranking(player):
    return player.ranking

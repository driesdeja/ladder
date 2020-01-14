from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Player
from .forms import PlayerForm
from .utils import update_ladder_ranking


def list_players(request):
    context = {
        'title': 'Player List',
        'players': Player.objects.all().order_by('ranking')
    }
    return render(request, 'players/player_list.html', context)


@login_required()
def edit_player(request, player_id):
    form = PlayerForm(request.POST or None)
    player = Player.objects.get(id=player_id)
    if request.POST:
        if request.POST.get("delete") == 'Delete':
            print('deleting ' + str(player))
            update_ladder_ranking(player, 'delete', '')
            player.delete()

            context = {
                'title': 'Player List',
                'players': Player.objects.all().order_by('ranking')
            }
            return redirect('/players/', context)
        if form.is_valid():
            player.last_name = form.cleaned_data.get('last_name')
            player.first_name = form.cleaned_data.get('first_name')
            player.contact_number = form.cleaned_data.get('contact_number')
            if player.ranking != form.cleaned_data.get('ranking'):
                update_ladder_ranking(player, 'change', form.cleaned_data.get('ranking'))
            player.ranking = form.cleaned_data.get('ranking')
            player.save()
        context = {
            'title': 'Player List',
            'players': Player.objects.all().order_by('ranking')
        }
        return redirect('/players/', context)

    context = {
        'form': form,
        'player': player
    }
    return render(request, 'players/edit_player.html', context)


@login_required()
def create_player(request):
    form = PlayerForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            new_player = Player()
            new_player.first_name = form.cleaned_data.get('first_name')
            new_player.last_name = form.cleaned_data.get('last_name')
            new_player.contact_number = form.cleaned_data.get('contact_number')
            # new_player.save()
            update_ladder_ranking(new_player, 'add', form.cleaned_data.get('ranking'))
            form = PlayerForm()
    context = {
        'form': form
    }
    return render(request, 'players/create_player.html', context)


@login_required()
def reset_rankings(request):
    players = Player.objects.all().order_by('ranking')
    for idx, player in enumerate(players):
        # old_ranking = player.ranking
        player.ranking = idx + 1
        # print(str(idx) + str(player) + ' ' + str(old_ranking) + ' ' + str(player.ranking))
        player.save()

    return redirect(list_players)

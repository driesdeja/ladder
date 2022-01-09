"""Player views"""
from io import TextIOWrapper
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse
from round.utils import update_ladder_ranking
from .models import Player
from .forms import PlayerForm


from .utils import get_file_of_players, \
    extract_players_from_file, \
    save_players, \
    get_pdf_file



def list_players(request):
    """Builds a list of players, either all or only Active players"""
    if request.POST:
        if request.POST.get("toggle-active"):
            players = Player.objects.all().order_by('ranking')
            all_players = True
        else:
            players = Player.objects.filter(status=Player.ACTIVE).order_by('ranking')
            all_players = False
    else:
        players = Player.objects.filter(status=Player.ACTIVE).order_by('ranking')
        all_players = False
    context = {
        'title': 'Player List',
        'players': players,
        'all_players': all_players
    }
    return render(request, 'players/player_list.html', context)


@login_required()
def edit_player(request, player_id):
    """view to edit players"""
    form = PlayerForm(request.POST or None)
    player = Player.objects.get(id=player_id)
    if request.POST:
        if form.is_valid():
            player.last_name = form.cleaned_data.get('last_name')
            player.first_name = form.cleaned_data.get('first_name')
            player.contact_number = form.cleaned_data.get('contact_number')
            if player.ranking != form.cleaned_data.get('ranking'):
                update_ladder_ranking(player,
                                    'change',
                                    form.cleaned_data.get('ranking'),
                                    form.cleaned_data.get('effective_date')
                                    )
            player.status = form.cleaned_data.get('status')
            player.ranking = form.cleaned_data.get('ranking')
            player.save()
        return redirect(list_players)

    context = {
        'form': form,
        'player': player
    }
    return render(request, 'players/edit_player.html', context)


@login_required()
def create_player(request):
    """View to create a player"""
    form = PlayerForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            new_player = Player()
            new_player.first_name = form.cleaned_data.get('first_name')
            new_player.last_name = form.cleaned_data.get('last_name')
            new_player.contact_number = form.cleaned_data.get('contact_number')
            # new_player.save()
            update_ladder_ranking(new_player,
                                'add',
                                form.cleaned_data.get('ranking'),
                                form.cleaned_data.get('effective_date')
                                )
            form = PlayerForm()
    context = {
        'form': form
    }
    return render(request, 'players/create_player.html', context)


@login_required()
def reset_rankings(request):
    """Utility view to reset all rankings"""
    players = Player.objects.filter(status=Player.ACTIVE).order_by('ranking')
    for idx, player in enumerate(players):
        # old_ranking = player.ranking
        player.ranking = idx + 1
        # print(str(idx) + str(player) + ' ' + str(old_ranking) + ' ' + str(player.ranking))
        player.save()

    return redirect(list_players)


@permission_required('players.add_player')
def import_players(request):
    """View to import players"""
    players = []
    if request.POST:
        if request.POST.get('import'):
            players_file = TextIOWrapper(request.FILES['file'])
            players = extract_players_from_file(players_file)
        elif request.POST.get('cancel'):
            messages.warning(request, 'Player import cancelled!')
            players = None
            redirect(import_players)
        elif request.POST.get('save'):
            players = request.POST.get('players')

            records_created = save_players(players)
            messages.info(request, f'Successfully imported {records_created} players!')
            return redirect(list_players)
    context = {
        'players': players
    }

    return render(request, 'players/import_players.html', context)


@permission_required('players.add_player')
def export_players(request):
    """View to export players"""
    filename = 'players.csv'
    file_to_download = get_file_of_players()
    with open(file_to_download, encoding=str) as file_to_download:
        response = HttpResponse(file_to_download, content_type='application/txt')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


def download_players(request):
    """View to download players in a pdf file"""
    filename = 'player_list.pdf'
    pdf_file = get_pdf_file('player_list')
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

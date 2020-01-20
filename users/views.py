from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm
from round.models import PlayerRanking, PlayersInLadderRound, Match
from round.utils import matches_player_played_in

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            messages.success(request, f'You have successfully registered, please log in! ')
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    context = {
        'form': form
    }
    return render(request, 'users/register.html', context)


@login_required
def profile(request):
    player_rankings = PlayerRanking.objects.filter(player=request.user.profile.player)
    competed_in_rounds = PlayersInLadderRound.objects.filter(player=request.user.profile.player)
    ladder_rounds_competed_in = []
    for competed_in_round in competed_in_rounds:
        ladder_rounds_competed_in.append(competed_in_round.ladder_round)
    matches_played_in = matches_player_played_in(request.user.profile.player)
    context = {
        'player_rankings': player_rankings,
        'ladder_rounds_competed_in': ladder_rounds_competed_in,
        'matches': matches_played_in
    }
    return render(request, 'users/profile.html', context)

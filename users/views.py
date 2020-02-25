from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, PlayerUpdateForm, UserUpdateForm
from round.models import PlayerRanking, PlayersInLadderRound, Match, Ladder
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
    if request.POST:
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = PlayerUpdateForm(request.POST, instance=request.user.profile.player)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your profile has been updated!')
            redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = PlayerUpdateForm(instance=request.user.profile.player)
    player_rankings = PlayerRanking.objects.filter(player=request.user.profile.player).order_by('-last_updated')
    competed_in_rounds = PlayersInLadderRound.objects.filter(player=request.user.profile.player)

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
        matches_played_in.extend(matches_player_played_in(request.user.profile.player, each_ladder))
    context = {
        'player_rankings': player_rankings,
        'ladders_competed_in': ladders_competed_in,
        'ladder_rounds_competed_in': ladder_rounds_competed_in,
        'matches': matches_played_in,
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile.html', context)

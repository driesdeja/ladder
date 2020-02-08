import datetime
from django import forms
from .models import Ladder, LadderRound, Match


class LadderForm(forms.ModelForm):
    class Meta:
        model = Ladder
        fields = [
            'title',
            'start_date',
            'end_date',
            'status'
        ]


class LadderStatusForm(forms.ModelForm):
    class Meta:
        model = Ladder
        fields = [
            'end_date',
        ]

class LadderRoundForm(forms.ModelForm):

    class Meta:
        model = LadderRound
        fields = [
            'start_date',
            'end_date',
            'ladder',
        ]

    def clean_start_date(self, *args, **kwargs):
        ladder = Ladder.objects.get(id=self.data.get("ladder"))
        start_date = self.cleaned_data.get("start_date")
        if not start_date >= ladder.start_date:
            raise forms.ValidationError(
                "The round can only start after the ladder started. Check the start date of the round.")
        if not start_date >= datetime.date.today():
            raise forms.ValidationError(
                "Rounds can only be future dated")
        ladder_rounds = LadderRound.objects.filter(ladder=ladder)

        return start_date


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            'games_for_player1',
            'games_for_player2',
            'result'
        ]

        def clean(self):
            print('Validation')
            games_for_player1 = int(self.cleaned_data.get('games_for_player1'))
            games_for_player2 = int(self.cleaned_data.get('games_for_player2'))
            result = int(self.data.get('result'))
            if result == 0:  # Not Played
                raise forms.ValidationError(
                    'The result cannot be not played, please select another option'
                )
            elif result == 1:  # Player 1 Won
                if games_for_player1 != 3:
                    raise forms.ValidationError(
                        'If player 1 won then they should have won 3 games'
                    )
            elif result == 2:  # Player 2 Won
                if games_for_player2 != 3:
                    raise forms.ValidationError(
                        'If player 2 won then player 2 should have won 3 games'
                    )
            elif result == 3:  # Play1er 1 Defaulted
                if games_for_player2 != 3:
                    raise forms.ValidationError(
                        'Player 2 should be awarded three games if player 1 defaulted'
                    )
            elif result == 4:  # Play1er 2 Defaulted
                if games_for_player1 != 3:
                    raise forms.ValidationError(
                        'Player 1 should be awarded three games if player 2 defaulted'
                    )
            elif result == 5:  # Game cancelled
                if games_for_player2 > 0 or games_for_player1 > 0:
                    raise forms.ValidationError(
                        'Both players should be awarded 0 games as the game was cancelled'
                    )
            return self.cleaned_data

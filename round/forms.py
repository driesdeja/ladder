import datetime
from django import forms
from .models import Ladder, LadderRound


class LadderForm(forms.ModelForm):
    class Meta:
        model = Ladder
        fields = [
            'title',
            'start_date',
            'end_date',
            'status'
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
        for ladder_round in ladder_rounds:
            print(ladder_round)
        return start_date

from django.contrib import admin
from .models import LadderRound, PlayersInLadderRound, Draw, MatchResult

admin.site.register(LadderRound)
admin.site.register(PlayersInLadderRound)
admin.site.register(Draw)
admin.site.register(MatchResult)

# Register your models here.

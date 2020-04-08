from django.contrib import admin
from .models import Ladder, \
    LadderRound, \
    PlayersInLadderRound, \
    Match, \
    MatchResult, \
    MatchSchedule, \
    RoundMatchSchedule

admin.site.register(Ladder)
admin.site.register(LadderRound)
admin.site.register(PlayersInLadderRound)
admin.site.register(Match)
admin.site.register(MatchResult)
admin.site.register(MatchSchedule)
admin.site.register(RoundMatchSchedule)

# Register your models here.

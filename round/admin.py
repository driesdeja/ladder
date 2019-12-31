from django.contrib import admin
from .models import Ladder, \
                    LadderRound, \
                    PlayersInLadderRound, \
                    Match, \
                    MatchResult

admin.site.register(Ladder)
admin.site.register(LadderRound)
admin.site.register(PlayersInLadderRound)
admin.site.register(Match)
admin.site.register(MatchResult)

# Register your models here.

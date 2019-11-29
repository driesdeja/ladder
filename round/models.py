from django.db import models
from players import models as player_models


class Ladder(models.Model):
    CREATED = 0
    OPEN = 1
    CLOSED = 2
    COMPLETED = 3
    CANCELLED = 4

    Status = (
        (CREATED, 'Created'),
        (OPEN, 'Open'),
        (CLOSED, 'Closed'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled')
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=Status, default=CREATED)


class PlayersInLadder(models.Model):
    player = models.ForeignKey(player_models.Player, on_delete=models.PROTECT)
    ladder = models.ForeignKey(Ladder, on_delete=models.PROTECT)
    date_entered = models.DateField(auto_now_add=True)
    date_withdrawn = models.DateField(null=True)


class PlayerLadderRanking(models.Model):
    player_in_ladder = models.ForeignKey(PlayersInLadder, on_delete=models.PROTECT)
    ranking = models.IntegerField(default=0)
    eff_from = models.DateField(null=True)
    eff_to = models.DateField(null=True)
    last_updated = models.DateTimeField(auto_now=True)


class LadderRound(models.Model):
    CREATED = 0
    OPEN = 1
    CLOSED = 2
    COMPLETED = 3
    CANCELLED = 4

    Status = (
        (CREATED, 'Created'),
        (OPEN, 'Open'),
        (CLOSED, 'Closed'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled')
    )

    date = models.DateField()
    status = models.IntegerField( choices=Status, default=CREATED)

    def __str__(self):
        return 'Date :' + self.date.strftime("%d %b %Y") + ' Status: ' + str(self.status)


class PlayersInLadderRound(models.Model):
    player = models.ForeignKey(player_models.Player, on_delete=models.CASCADE)
    ladder_round = models.ForeignKey(LadderRound, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.player) + ' - ' + str(self.ladder_round)


class MatchResult(models.Model):
    description = models.CharField(max_length=30)

    def __str__(self):
        return self.description


class Draw(models.Model):
    ladder_round = models.ForeignKey(LadderRound, on_delete=models.CASCADE)
    player1 = models.ForeignKey(player_models.Player, on_delete=models.PROTECT, related_name='player_1')
    player2 = models.ForeignKey(player_models.Player, on_delete=models.PROTECT, related_name='player_2')
    games_for_player1 = models.IntegerField(default=0)
    games_for_player2 = models.IntegerField(default=0)
    match_result = models.ForeignKey(MatchResult, on_delete=models.PROTECT)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

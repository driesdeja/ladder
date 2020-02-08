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
    title = models.CharField(max_length=101)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=Status, default=CREATED)

    class Meta:
        permissions = [
            ('can_administrate_ladder', 'Can administrate the ladder')
        ]

    def __str__(self):
        return self.title


class LadderRound(models.Model):
    CREATED = 0
    OPEN = 1
    CLOSED = 2
    COMPLETED = 3
    CANCELLED = 4

    Status = [
        (CREATED, 'Created'),
        (OPEN, 'Open'),
        (CLOSED, 'Closed'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled')
    ]

    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=Status, default=CREATED)
    ladder = models.ForeignKey(Ladder, on_delete=models.CASCADE)


class PlayersInLadderRound(models.Model):
    player = models.ForeignKey(player_models.Player, on_delete=models.CASCADE)
    ladder_round = models.ForeignKey(LadderRound, on_delete=models.CASCADE)
    ranking = models.IntegerField(default=0)

    def __str__(self):
        return str(self.player) + ' - ' + str(self.ladder_round)


class MatchResult(models.Model):
    NOT_PLAYED = 0
    PLAYER_1_WON = 1
    PLAYER_2_WON = 2
    PLAYER_1_DEFAULTED = 3
    PLAYER_2_DEFAULTED = 4
    CANCELLED = 5

    Result = [
        (NOT_PLAYED, 'Not Played'),
        (PLAYER_1_WON, 'Player 1 Won'),
        (PLAYER_2_WON, 'Player 2 Won'),
        (PLAYER_1_DEFAULTED, 'Player 1 Defaulted'),
        (PLAYER_2_DEFAULTED, 'Player 2 Defaulted'),
        (CANCELLED, 'Cancelled')
    ]

    result = models.IntegerField(choices=Result, default=NOT_PLAYED)

    def __str__(self):
        return self.Result[self.result][1]


class Match(models.Model):
    NOT_PLAYED = 0
    PLAYER_1_WON = 1
    PLAYER_2_WON = 2
    PLAYER_1_DEFAULTED = 3
    PLAYER_2_DEFAULTED = 4
    CANCELLED = 5

    Result = [
        (NOT_PLAYED, 'Not Played'),
        (PLAYER_1_WON, 'Player 1 Won'),
        (PLAYER_2_WON, 'Player 2 Won'),
        (PLAYER_1_DEFAULTED, 'Player 1 Defaulted'),
        (PLAYER_2_DEFAULTED, 'Player 2 Defaulted'),
        (CANCELLED, 'Cancelled')
    ]

    ladder_round = models.ForeignKey(LadderRound, on_delete=models.CASCADE)
    player1 = models.ForeignKey(player_models.Player, on_delete=models.PROTECT, related_name='player_1')
    player2 = models.ForeignKey(player_models.Player, on_delete=models.PROTECT, related_name='player_2')
    games_for_player1 = models.IntegerField(default=0)
    games_for_player2 = models.IntegerField(default=0)
    date_played = models.DateField(null=True)
    result = models.IntegerField(choices=Result, default=NOT_PLAYED)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Matches',
        ordering = ['player1__ranking']

    def __str__(self):
        return '\nDraw' \
               '\n\tRound: ' + str(self.ladder_round) + \
               '\n\tPlayer1: ' + self.player1.first_name + \
               '\n\tPlayer2: ' + self.player2.first_name + \
               '\n\tGames for Player1: ' + str(self.games_for_player1) + \
               '\n\tGames for Player2: ' + str(self.games_for_player2) + \
               '\n\tMatch Result: ' + str(self.result) + \
               '\n\tDate Created: ' + str(self.date_created) + \
               '\n\tLast Updated: ' + str(self.last_updated)


class PlayerRanking(models.Model):
    player = models.ForeignKey(player_models.Player, on_delete=models.PROTECT)
    ranking = models.IntegerField(default=0)
    eff_from = models.DateTimeField()
    eff_to = models.DateTimeField(null=True)
    last_updated = models.DateTimeField(auto_now=True)
    reason_for_change = models.TextField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f'{self.player.first_name} ranking {self.ranking} effective from {self.eff_from} to ' \
               f'{self.eff_to}. It was changed on {self.last_updated} because {self.reason_for_change}'

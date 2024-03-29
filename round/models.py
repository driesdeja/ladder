from django.db import models
from players import models as player_models
from django.utils.timezone import now


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

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=101, unique=True)
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
        return f'id: {self.id}, Title: {self.title}, Start Date: {self.start_date}, End Date: {self.end_date}'


class RoundMatchSchedule(models.Model):
    THIRTY_MINUTES = 30
    FOURTY_FIVE_MINUTES = 45
    SIXTY_MINUTES = 60

    time_intervals = [
        (THIRTY_MINUTES, '30 min'),
        (FOURTY_FIVE_MINUTES, '45 min'),
        (SIXTY_MINUTES, '60 min')
    ]

    id = models.AutoField(primary_key=True)
    match_days = models.TextField()
    number_of_courts = models.IntegerField()
    number_of_timeslots = models.IntegerField(default=0)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True)
    time_interval = models.IntegerField(choices=time_intervals, default=THIRTY_MINUTES)

    def __str__(self):
        return f'Match Days: {self.match_days} - ' \
               f'Number of Courts: {self.number_of_courts} - ' \
               f'Start Time: {self.start_time} - ' \
               f'End Time: {self.end_time} ' \
               f'Time Interval: {self.time_interval}'


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

    id = models.AutoField(primary_key=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=Status, default=CREATED)
    ladder = models.ForeignKey(Ladder, on_delete=models.CASCADE)
    match_schedule = models.ForeignKey(RoundMatchSchedule, on_delete=models.CASCADE, null=True, blank=True)


class PlayersInLadderRound(models.Model):
    id = models.AutoField(primary_key=True)
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

    id = models.AutoField(primary_key=True)
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

    id = models.AutoField(primary_key=True)
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
        return f'id: {self.id} ladder_round: {self.ladder_round} date_played: {self.date_played} '


class PlayerRanking(models.Model):
    id = models.AutoField(primary_key=True)
    player = models.ForeignKey(player_models.Player, on_delete=models.PROTECT)
    ranking = models.IntegerField(default=0)
    eff_from = models.DateTimeField()
    eff_to = models.DateTimeField(null=True)
    last_updated = models.DateTimeField(auto_now=True)
    reason_for_change = models.TextField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f'{self.player.first_name} ranking {self.ranking} effective from {self.eff_from} to ' \
               f'{self.eff_to}. It was changed on {self.last_updated} because {self.reason_for_change}'


class MatchSchedule(models.Model):
    OPEN = 0
    CLOSED = 1

    Status = [
        (OPEN, 'Open'),
        (CLOSED, 'Closed')
    ]

    id = models.AutoField(primary_key=True)
    day = models.DateField(default=now)
    court = models.IntegerField(default=1)
    time_slot = models.TimeField()
    match = models.ForeignKey(Match, null=True, on_delete=models.CASCADE)
    ladder_round = models.ForeignKey(LadderRound, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status, default=OPEN)
    time_grid_location = models.IntegerField(default=0)

    def __str__(self):
        return f'day: {self.day} - ' \
               f'court: {self.court}' \
               f'time_slot: {self.time_slot} : ' \
               f' - Round start date: {self.ladder_round.start_date}' \
               f'time_grid_location: {self.time_grid_location}'

from django.test import TestCase
from datetime import date, datetime, timedelta, time
from .models import PlayersInLadderRound, Ladder, LadderRound, Match, MatchResult, RoundMatchSchedule, MatchSchedule
from players.models import Player
from .utils import add_player_to_round, ensure_player_not_already_in_round, ranking_change, update_ladder_ranking, \
    get_full_ladder_details, date_range, add_intervals_to_start_time, get_number_of_timeslots, \
    create_match_schedule_with_round_match_schedule, validate_and_create_ladder_round, date_for_day_of_the_year, \
    save_scheduled_matches, validate_and_create_ladder_rounds


# Create your tests here.
class RoundUtilsTestCase(TestCase):

    def setUp(self):
        self.list_of_players = []
        self.player1 = Player.objects.create(first_name='Prince', last_name='Charming', contact_number='021329015',
                                             ranking=1)
        self.player2 = Player.objects.create(first_name='Princess', last_name='Fiona', contact_number='021329015',
                                             ranking=3)
        self.player3 = Player.objects.create(first_name='Mickey', last_name='Mouse', contact_number='021329015',
                                             ranking=4)
        self.player4 = Player.objects.create(first_name='Tinker', last_name='Bell', contact_number='021329015',
                                             ranking=5)
        self.player5 = Player.objects.create(first_name='Peter', last_name='Pan', contact_number='021329015', ranking=6)
        self.player6 = Player.objects.create(first_name='Lord', last_name='Farquaad', contact_number='021329015',
                                             ranking=2)
        self.player7 = Player.objects.create(first_name='Robin', last_name='Hood', contact_number='021329015',
                                             ranking=7)
        self.player8 = Player.objects.create(first_name='Tom', last_name='Thumb', contact_number='021329015', ranking=8)

        self.list_of_players = Player.objects.all()

        self.ladder = Ladder.objects.create(title='Fairy Tale Ladder', start_date=date.today())

        self.ladder_round = LadderRound.objects.create(start_date=date.today(),
                                                       end_date=date.today() + timedelta(days=7),
                                                       ladder=self.ladder)

        match1 = Match.objects.create(player1=Player.objects.get(ranking=1), player2=Player.objects.get(ranking=2),
                                      ladder_round=LadderRound.objects.all().first())
        match2 = Match.objects.create(player1=Player.objects.get(ranking=3), player2=Player.objects.get(ranking=4),
                                      ladder_round=LadderRound.objects.all().first())
        match3 = Match.objects.create(player1=Player.objects.get(ranking=5), player2=Player.objects.get(ranking=6),
                                      ladder_round=LadderRound.objects.all().first())
        match4 = Match.objects.create(player1=Player.objects.get(ranking=7), player2=Player.objects.get(ranking=8),
                                      ladder_round=LadderRound.objects.all().first())

        match1.games_for_player1 = 3
        match1.games_for_player2 = 0
        match1.result = Match.PLAYER_1_WON
        match1.date_played = datetime.now()
        match1.save()

        match2.games_for_player1 = 3
        match2.games_for_player2 = 0
        match2.date_played = datetime.now()
        match2.result = Match.PLAYER_1_WON
        match2.save()

        match3.games_for_player1 = 2
        match3.games_for_player2 = 3
        match3.date_played = datetime.now()
        match3.result = Match.PLAYER_2_WON
        match3.save()

        match4.games_for_player1 = 1
        match4.games_for_player2 = 3
        match4.date_played = datetime.now()
        match4.result = Match.PLAYER_2_WON
        match4.save()

        last_week_round = LadderRound.objects.create(start_date=datetime.today() - timedelta(days=7),
                                                     end_date=datetime.today() - timedelta(days=1),
                                                     ladder=self.ladder)
        # create one that started 2 weeks ago
        two_weeks_ago_round = LadderRound.objects.create(start_date=datetime.today() - timedelta(days=14),
                                                         end_date=datetime.today() - timedelta(days=6),
                                                         ladder=self.ladder)
        # create one that started 3 weeks ago
        three_weeks_ago_round = LadderRound.objects.create(start_date=datetime.today() - timedelta(days=21),
                                                           end_date=datetime.today() - timedelta(days=13),
                                                           ladder=self.ladder)

        # populate the rounds with Matches

        match1 = Match.objects.create(player1=Player.objects.get(ranking=1), player2=Player.objects.get(ranking=2),
                                      ladder_round=last_week_round)
        match2 = Match.objects.create(player1=Player.objects.get(ranking=3), player2=Player.objects.get(ranking=4),
                                      ladder_round=last_week_round)
        match3 = Match.objects.create(player1=Player.objects.get(ranking=5), player2=Player.objects.get(ranking=6),
                                      ladder_round=last_week_round)
        match4 = Match.objects.create(player1=Player.objects.get(ranking=7), player2=Player.objects.get(ranking=8),
                                      ladder_round=last_week_round)

        match1.games_for_player1 = 1
        match1.games_for_player2 = 3
        match1.result = Match.PLAYER_2_WON
        match1.date_played = datetime.now() - timedelta(days=3)
        match1.save()

        match2.games_for_player1 = 3
        match2.games_for_player2 = 0
        match2.date_played = datetime.now() - timedelta(days=3)
        match2.result = Match.PLAYER_1_WON
        match2.save()

        match3.games_for_player1 = 2
        match3.games_for_player2 = 3
        match3.date_played = datetime.now() - timedelta(days=3)
        match3.result = Match.PLAYER_2_WON
        match3.save()

        match4.games_for_player1 = 1
        match4.games_for_player2 = 3
        match4.date_played = datetime.now() - timedelta(days=3)
        match4.result = Match.PLAYER_2_WON
        match4.save()

        # populate the rounds with Matches

        match1 = Match.objects.create(player1=Player.objects.get(ranking=1), player2=Player.objects.get(ranking=2),
                                      ladder_round=two_weeks_ago_round)
        match2 = Match.objects.create(player1=Player.objects.get(ranking=3), player2=Player.objects.get(ranking=4),
                                      ladder_round=two_weeks_ago_round)
        match3 = Match.objects.create(player1=Player.objects.get(ranking=5), player2=Player.objects.get(ranking=6),
                                      ladder_round=two_weeks_ago_round)
        match4 = Match.objects.create(player1=Player.objects.get(ranking=7), player2=Player.objects.get(ranking=8),
                                      ladder_round=two_weeks_ago_round)

        match1.games_for_player1 = 1
        match1.games_for_player2 = 3
        match1.result = Match.PLAYER_2_WON
        match1.date_played = datetime.now() - timedelta(days=3)
        match1.save()

        match2.games_for_player1 = 3
        match2.games_for_player2 = 0
        match2.date_played = datetime.now() - timedelta(days=3)
        match2.result = Match.PLAYER_1_WON
        match2.save()

        match3.games_for_player1 = 2
        match3.games_for_player2 = 3
        match3.date_played = datetime.now() - timedelta(days=3)
        match3.result = Match.PLAYER_2_WON
        match3.save()

        match4.games_for_player1 = 1
        match4.games_for_player2 = 3
        match4.date_played = datetime.now() - timedelta(days=3)
        match4.result = Match.PLAYER_2_WON
        match4.save()

        # create the RoundMatchSchedule

        # populate the rounds with Matches

        match1 = Match.objects.create(player1=Player.objects.get(ranking=1), player2=Player.objects.get(ranking=2),
                                      ladder_round=three_weeks_ago_round)
        match2 = Match.objects.create(player1=Player.objects.get(ranking=3), player2=Player.objects.get(ranking=4),
                                      ladder_round=three_weeks_ago_round)
        match3 = Match.objects.create(player1=Player.objects.get(ranking=5), player2=Player.objects.get(ranking=6),
                                      ladder_round=three_weeks_ago_round)
        match4 = Match.objects.create(player1=Player.objects.get(ranking=7), player2=Player.objects.get(ranking=8),
                                      ladder_round=three_weeks_ago_round)

        match1.games_for_player1 = 1
        match1.games_for_player2 = 3
        match1.result = Match.PLAYER_2_WON
        match1.date_played = datetime.now() - timedelta(days=3)
        match1.save()

        match2.games_for_player1 = 3
        match2.games_for_player2 = 0
        match2.date_played = datetime.now() - timedelta(days=3)
        match2.result = Match.PLAYER_1_WON
        match2.save()

        match3.games_for_player1 = 2
        match3.games_for_player2 = 3
        match3.date_played = datetime.now() - timedelta(days=3)
        match3.result = Match.PLAYER_2_WON
        match3.save()

        match4.games_for_player1 = 1
        match4.games_for_player2 = 3
        match4.date_played = datetime.now() - timedelta(days=3)
        match4.result = Match.PLAYER_2_WON
        match4.save()

    def test_add_player_to_round(self):
        add_player_to_round(self.ladder_round.id, Player.objects.get(first_name='Tom'))
        player_in_round = PlayersInLadderRound.objects.get(player=Player.objects.get(first_name='Tom'))
        self.assertIsNotNone(self, player_in_round)

    def test_ensure_player_not_already_in_round(self):
        add_player_to_round(self.ladder_round.id, Player.objects.get(first_name='Tom'))
        ensure_player_not_already_in_round(self.ladder_round, Player.objects.get(first_name='Tom'))
        with self.assertRaises(PlayersInLadderRound.DoesNotExist):
            PlayersInLadderRound.objects.get(player=Player.objects.get(first_name='Tom'))

    def test_ranking_change(self):
        self.assertEqual(ranking_change(3), -2)
        self.assertEqual(ranking_change(2), -1)
        self.assertEqual(ranking_change(1), 0)
        self.assertEqual(ranking_change(0), 1)
        with self.assertRaises(ValueError):
            ranking_change(4)
            ranking_change(-1)
            ranking_change(None)

    def test_update_ladder_ranking(self):
        # Adding a new player to the list
        new_player = Player.objects.create(first_name='Super', last_name='Man', contact_number='021329015', ranking=0)
        update_ladder_ranking(new_player, 'add', 0)
        players = Player.objects.all().order_by('ranking')
        self.assertEqual(new_player.ranking, len(players))

        # Peter won 3 games in his match, Position on ladder decreases by 2
        peter = Player.objects.filter(first_name='Peter').first()
        new_ranking = peter.ranking + ranking_change(3)
        update_ladder_ranking(peter, 'change', new_ranking)
        self.assertEqual(peter.ranking, 4)

        # Lord Farquaad won 2 games, so ranking position decreases by 1
        lord = Player.objects.filter(first_name='Lord').first()
        new_ranking = lord.ranking + ranking_change(2)
        # print(new_ranking)
        update_ladder_ranking(lord, 'change', new_ranking)
        self.assertEqual(lord.ranking, 1)

        # Mickey won 0 games, so ranking position increases by 1 (moves further away from 1)
        mickey = Player.objects.filter(first_name='Mickey').first()
        new_ranking = mickey.ranking + ranking_change(0)
        print(new_ranking)
        update_ladder_ranking(mickey, 'change', new_ranking)
        self.assertEqual(mickey.ranking, 6)

        update_ladder_ranking(lord, 'delete', None)
        lord.delete()
        self.assertEqual(Player.objects.get(first_name='Prince').ranking, 1)

        all_players = Player.objects.all().order_by('ranking')

        tinker = Player.objects.filter(first_name='Tinker').first()
        update_ladder_ranking(tinker, 'change', len(all_players) + 100)

        # Eyeball validation of the rules
        # players = Player.objects.all().order_by('ranking')
        # for player in players:
        #     print(f'{player.first_name} ranking: {player.ranking}')

    # Not sure if capture match should be tested.  The important issue was the order in which the matches were
    # to be processed as that will influence ranking.  This has been resolved by using order_by on the Match model to
    # ensure that the Matches are always processed from the highest ranked player to the lowest rank.
    # that might be something to test that the ranking results are predictable.
    def test_capture_match_results(self):
        matches = Match.objects.all()
        for match in matches:
            print(match)
        self.assertTrue(True)

    def test_get_full_ladder_details(self):
        # add additional LadderRounds
        # create one that started a week ago

        ladder = Ladder.objects.all().first()
        ladder_rounds = list(LadderRound.objects.all().filter(ladder=ladder))
        ladder_details = get_full_ladder_details(ladder)
        print(ladder_details)

        self.assertIsNotNone(self, ladder_details)

    def test_date_range(self):
        dates = date_range(datetime.now(), datetime.now() + timedelta(5))
        for day in dates:
            print(day)
        self.assertIsNotNone(dates)

    def test_add_intervals_to_start_time(self):
        start_time = '18:00'
        interval = 30
        number_of_intervals = 4
        end_time_obj = add_intervals_to_start_time(start_time, interval, number_of_intervals)
        end_time_str = end_time_obj.strftime('%H:%M')
        self.assertEqual(end_time_str, '20:00')

    def test_get_number_of_timeslots(self):
        start_time = datetime.strptime('18:00', '%H:%M')
        end_time = datetime.strptime('22:00', '%H:%M')
        time_interval = 60
        number_of_timeslots = get_number_of_timeslots(start_time, end_time, time_interval)
        self.assertEqual(number_of_timeslots, 4)

    def test_create_match_schedule_with_round_match_schedule(self):

        ladder_round = LadderRound.objects.all().first()
        match_day = str(ladder_round.start_date.timetuple().tm_yday)
        start_time = datetime.strptime('18:00', '%H:%M').time()
        end_time = datetime.strptime('18:00', '%H:%M').time()
        time_interval = 30
        number_of_courts = 4
        number_of_timeslots = 8
        round_match_schedule = RoundMatchSchedule.objects.create(match_days=match_day,
                                                                 number_of_courts=number_of_courts,
                                                                 number_of_timeslots=number_of_timeslots,
                                                                 start_time=start_time,
                                                                 end_time=end_time,
                                                                 time_interval=time_interval)
        ladder_round.match_schedule = round_match_schedule
        ladder_round.save()
        create_match_schedule_with_round_match_schedule(ladder_round, round_match_schedule)
        match_schedules = MatchSchedule.objects.filter(ladder_round=ladder_round)
        self.assertEqual(32, len(match_schedules))

    def test_validate_and_create_ladder_round(self):
        start_date = date.today() + timedelta(weeks=10)
        end_date = start_date + timedelta(days=7)

        ladder_round = validate_and_create_ladder_round(self.ladder, start_date, end_date)
        self.assertIsNotNone(ladder_round)
        self.assertTrue(ladder_round.start_date == start_date)
        with self.assertRaises(ValueError):
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=7)
            validate_and_create_ladder_round(self.ladder, start_date, end_date)
            start_date = date.today() - timedelta(days=7)
            end_date = start_date + timedelta(days=7)
            validate_and_create_ladder_round(self.ladder, start_date, end_date)

    def test_date_for_day_of_the_year(self):
        # non leap year
        year = 2019
        day = 60
        date_for_year = date_for_day_of_the_year(day, year)
        self.assertEqual(date_for_year, datetime(2019, 3, 1))
        year = 2020
        day = 60
        date_for_year = date_for_day_of_the_year(day, year)
        self.assertEqual(date_for_year, datetime(2020, 2, 29))
        # test with string
        year = '2020'
        day = '60'
        date_for_year = date_for_day_of_the_year(day, year)
        self.assertEqual(date_for_year, datetime(2020, 2, 29))

    def test_save_scheduled_matches(self):

        ladder_round = LadderRound.objects.all().first()
        match_day = str(ladder_round.start_date.timetuple().tm_yday)
        start_time = datetime.strptime('18:00', '%H:%M').time()
        end_time = datetime.strptime('18:00', '%H:%M').time()
        time_interval = 30
        number_of_courts = 4
        number_of_timeslots = 8
        round_match_schedule = RoundMatchSchedule.objects.create(match_days=match_day,
                                                                 number_of_courts=number_of_courts,
                                                                 number_of_timeslots=number_of_timeslots,
                                                                 start_time=start_time,
                                                                 end_time=end_time,
                                                                 time_interval=time_interval)
        ladder_round.match_schedule = round_match_schedule
        ladder_round.save()

        match1 = Match.objects.create(player1=Player.objects.get(ranking=1), player2=Player.objects.get(ranking=2),
                                      ladder_round=LadderRound.objects.all().first())
        match2 = Match.objects.create(player1=Player.objects.get(ranking=3), player2=Player.objects.get(ranking=4),
                                      ladder_round=LadderRound.objects.all().first())
        match3 = Match.objects.create(player1=Player.objects.get(ranking=5), player2=Player.objects.get(ranking=6),
                                      ladder_round=LadderRound.objects.all().first())
        match4 = Match.objects.create(player1=Player.objects.get(ranking=7), player2=Player.objects.get(ranking=8),
                                      ladder_round=LadderRound.objects.all().first())

        scheduled_matches = [{'day': '86',
                              'matches': [{'timeslot': '18:00', 'match': match1.id, 'court': 1},
                                          {'timeslot': '18:00', 'match': match2.id, 'court': 2},
                                          {'timeslot': '18:00', 'match': match3.id, 'court': 3},
                                          {'timeslot': '18:00', 'match': match4.id, 'court': 4}]}
                             ]
        number_of_matches_saved = save_scheduled_matches(LadderRound.objects.all().first(), scheduled_matches)
        print(f'Number of matches saved: {number_of_matches_saved}')
        matches = MatchSchedule.objects.filter(ladder_round=ladder_round)
        for match in matches:
            print(match)
        self.assertTrue(number_of_matches_saved == 4)
        # test if the delete works
        number_of_matches_saved = save_scheduled_matches(LadderRound.objects.all().first(), scheduled_matches)
        saved_scheduled_matches = MatchSchedule.objects.filter(ladder_round=LadderRound.objects.all().first())
        self.assertTrue(len(saved_scheduled_matches) == 4)

    def test_setup_ladder_rounds(self):
        ladder = Ladder(
            title="Test Ladder",
            start_date=datetime.today().date(),
        )
        # ten rounds, weekly, no end date
        number_of_rounds = 10
        first_round_start_date = ladder.start_date
        duration_of_round = 'weekly'
        # duration_of_round = 'fortnightly'
        ladder_rounds = validate_and_create_ladder_rounds(ladder, number_of_rounds, first_round_start_date, duration_of_round)
        print(f'ten rounds, weekly, no end date - ladder_rounds should be 10: {len(ladder_rounds)}')
        self.assertTrue(len(ladder_rounds) == 10)

        # fortnightly, end_date 20 weeks later
        number_of_rounds = None
        end_date = datetime.today() + timedelta(weeks=20)
        ladder.end_date = end_date.date()
        duration_of_round = 'fortnightly'
        ladder_rounds = validate_and_create_ladder_rounds(ladder, number_of_rounds, first_round_start_date, duration_of_round)
        print(f'fortnightly, end_date 20 weeks later - ladder_rounds should be 10: {len(ladder_rounds)}')

        self.assertTrue(len(ladder_rounds) == 10)

        # monthly, end_date 52 weeks
        number_of_rounds = None
        duration_of_round = "monthly"
        end_date = datetime.today() + timedelta(weeks=52)
        ladder.end_date = end_date.date()
        ladder_rounds = validate_and_create_ladder_rounds(ladder, number_of_rounds, first_round_start_date, duration_of_round)
        print(f'monthly, end_date 52 weeks - ladder_rounds should be 12: {len(ladder_rounds)}')

        self.assertTrue(len(ladder_rounds) == 12)





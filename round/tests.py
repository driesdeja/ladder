from django.test import TestCase
from datetime import date, datetime
from .models import PlayersInLadderRound, Ladder, LadderRound
from players.models import Player
from .utils import add_player_to_round, ensure_player_not_already_in_round, ranking_change, update_ladder_ranking


# Create your tests here.
class RoundUtilsTestCase(TestCase):

    def setUp(self):
        self.list_of_players = []
        Player.objects.create(first_name='Prince', last_name='Charming', contact_number='021329015', ranking=1)
        Player.objects.create(first_name='Lord', last_name='Farquaad', contact_number='021329015', ranking=2)
        Player.objects.create(first_name='Princess', last_name='Fiona', contact_number='021329015', ranking=3)
        Player.objects.create(first_name='Mickey', last_name='Mouse', contact_number='021329015', ranking=4)
        Player.objects.create(first_name='Tinker', last_name='Bell', contact_number='021329015', ranking=5)
        Player.objects.create(first_name='Peter', last_name='Pan', contact_number='021329015', ranking=6)
        Player.objects.create(first_name='Robin', last_name='Hood', contact_number='021329015', ranking=7)
        Player.objects.create(first_name='Tom', last_name='Thumb', contact_number='021329015', ranking=8)

        self.list_of_players = Player.objects.all()

        self.ladder = Ladder.objects.create(title='Fairy Tale Ladder', start_date=date.today())

        self.ladder_round = LadderRound.objects.create(start_date=date.today(), ladder=self.ladder)

    def test_add_player_to_round(self):
        add_player_to_round(self.ladder_round.id, Player.objects.get(first_name='Tom'))
        player_in_round = PlayersInLadderRound.objects.get(player=Player.objects.get(first_name='Tom'))
        self.assertIsNotNone(self, player_in_round)

    def test_ensure_player_not_already_in_round(self):
        add_player_to_round(self.ladder_round.id, Player.objects.get(first_name='Tom'))
        ensure_player_not_already_in_round(self.ladder_round.id, Player.objects.get(first_name='Tom'))
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
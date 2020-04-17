import csv
import os
import json
from io import TextIOWrapper
from .models import Player
from django.conf import settings



def get_file_of_players():
    file_name = 'players.csv'
    file_path = os.path.join(settings.DOWNLOAD_ROOT, file_name)
    with open(file_path, 'w') as csv_file:
        fieldnames = ['ranking', 'first_name', 'last_name', 'email', 'contact_number']

        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        players = Player.objects.all().order_by('ranking')
        for player in players:
            csv_writer.writerow(
                {'ranking': player.ranking,
                 'first_name': player.first_name,
                 'last_name': player.last_name,
                 'email': player.last_name,
                 'contact_number': player.contact_number
                 })

    return file_path


def extract_players_from_file(players_file):
    fieldnames = ['ranking', 'first_name', 'last_name', 'email', 'contact_number']

    reader = csv.DictReader(players_file)
    players = []
    for row in reader:
        players.append(row)
    return players


def save_players(players):
    players_as_json = json.loads(players)
    for player in players_as_json:
        Player.objects.create(ranking=player['ranking'],
                              first_name=player['first_name'],
                              last_name=player['last_name'],
                              email=player['email'],
                              contact_number=player['contact_number'])
    return len(players_as_json)

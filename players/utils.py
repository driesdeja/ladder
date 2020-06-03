import csv
import os
import json
import io
from io import TextIOWrapper
from .models import Player
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, Image, Spacer
from reportlab.platypus.tables import TableStyle


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


def get_pdf_file(data_to_download):

    players = Player.objects.all().order_by('ranking')
    player_list = []
    for each_player in players:
        player_list.append([each_player.ranking,
                            each_player.first_name,
                            each_player.last_name,
                            each_player.email,
                            each_player.contact_number])

    doc = io.BytesIO()

    pdf = SimpleDocTemplate(doc, pagesize=A4)

    # Header Table with the logos
    franklin_logo = os.path.join(settings.MEDIA_ROOT, 'images/franklin_logo.png')
    squash_auckland_logo = os.path.join(settings.MEDIA_ROOT, 'images/squash_auckland.png')
    franklin_logo_image = Image(franklin_logo)
    franklin_logo_image.drawWidth = 100
    franklin_logo_image.drawHeight = 55

    squash_auckland_logo_image = Image(squash_auckland_logo)
    squash_auckland_logo_image.drawWidth = 100
    squash_auckland_logo_image.drawHeight = 30

    document_title = "Franklin Squash Club Ladder"

    header_table = Table([[franklin_logo_image, document_title, squash_auckland_logo_image]])

    # Header Table Style
    header_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#CD6620')),
        ('FONTSIZE', (1, 0), (1, 0), 20),
        ('FONTNAME', (1, 0), (1, 0), 'Times-BoldItalic')
    ])

    header_table.setStyle(header_table_style)

    spacer = Spacer(1, 10)

    # List with all of the players.
    if data_to_download == 'player_list':
        data = Table(get_player_list())
    else:
        data = None

    page_elements = [header_table, spacer, data]

    pdf.build(page_elements)

    doc.seek(0)

    return doc


def get_player_list():
    players = Player.objects.all().order_by('ranking')
    player_list = []
    for each_player in players:
        player_list.append([each_player.ranking,
                            each_player.first_name,
                            each_player.last_name,
                            each_player.email,
                            each_player.contact_number])
    return player_list

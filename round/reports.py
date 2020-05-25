import io
import os

from .models import LadderRound, MatchSchedule

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, Image, Spacer
from reportlab.platypus.tables import TableStyle
from reportlab.lib.units import mm

from .utils import date_for_day_of_the_year, add_minutes, get_match_schedule_grid_location


def get_pdf_match_schedule(ladder_round):
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

    # Round Schedule and Match Schedule

    scheduled_matches = MatchSchedule.objects.filter(ladder_round=ladder_round, match__isnull=False).order_by('time_grid_location')
    round_match_schedule = ladder_round.match_schedule

    data_list = []

    # Day Table
    match_days = round_match_schedule.match_days.split(',')
    time_slots = round_match_schedule.number_of_timeslots
    number_of_courts = round_match_schedule.number_of_courts
    for idx, day in enumerate(match_days, start=1):
        date_of_day = date_for_day_of_the_year(day, ladder_round.start_date.year)
        print(date_of_day)
        time_slot_table_list = []
        for time_slot in range(time_slots):
            time_slot_time = add_minutes(round_match_schedule.start_time, time_slot * round_match_schedule.time_interval)
            matches_in_slot = []
            for court in range(number_of_courts):
                grid_location = get_match_schedule_grid_location(idx, time_slot+1, court+1, number_of_courts, time_slots)
                match = [x for x in scheduled_matches if x.time_grid_location == grid_location]
                if match:
                    match_in_slot_table = Table([
                        [f'{match[0].match.player1.first_name} {match[0].match.player1.last_name}'],
                        ['vs'],
                        [f'{match[0].match.player2.first_name} {match[0].match.player2.last_name}']
                    ], colWidths=(45*mm), rowHeights=None)
                    match_in_slot_table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.green),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ])
                    match_in_slot_table.setStyle(match_in_slot_table_style)
                    matches_in_slot.append(match_in_slot_table)
            time_slot_table = Table([
                [time_slot_time.strftime('%H:%M')],
                matches_in_slot
            ], rowHeights=None)
            time_slot_table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFAE78')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black)
            ])
            time_slot_table.setStyle(time_slot_table_style)
            time_slot_table_list.append(time_slot_table)
            print(time_slot_time)
        day_table = Table([
            [date_of_day.strftime('%A %-d %b, %Y')],
            [time_slot_table_list]
        ])
        data_list.append(day_table)

    data = Table([data_list])

    page_elements = [header_table, spacer, data]

    doc = io.BytesIO()

    pdf = SimpleDocTemplate(doc, pagesize=A4)

    pdf.build(page_elements)

    doc.seek(0)

    return doc

from django import template
from round.utils import add_minutes, date_for_day_of_the_year

register = template.Library()


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def times(number):
    if isinstance(number, str):
        try:
            number = int(number)
        except ValueError:
            return 1
    return range(number)


@register.filter
def as_list(string, delimiter):
    return string.split(delimiter)


@register.simple_tag
def timeslot(start_time, counter, interval):
    if isinstance(start_time, str):
        start_time = int(start_time)
    minutes = counter * interval
    return add_minutes(start_time, minutes)

@register.filter
def date_for_day_of_year(day, year):
    return date_for_day_of_the_year(day, year)

@register.simple_tag
def grid_location(day, time_slot, court, number_of_courts, number_of_timeslots):
    location = court + number_of_courts*(time_slot-1) + (number_of_timeslots*number_of_courts*(day-1))
    return location

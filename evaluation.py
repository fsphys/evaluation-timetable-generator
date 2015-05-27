#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Documentation, License etc.

@package evaluation
'''
import sys
import os
import glob
import json
import urllib.request
import csv
from datetime import datetime, time

from simpleodspy.sodsspreadsheet import SodsSpreadSheet
from simpleodspy.sodsods import SodsOds

###
# Configuration options
###

###
# Configuration for the current term
###

# get this from http://www.kithub.de/api/#!/terms/GET-terms---format-_get_0
term_id = 10222 # Sommersemester 2015
#term_id = 7895  # Wintersemester 2014/15
# term_id = 7022 # Sommersemester 2014
# term_id = 4521 # Wintersemester 2013/14

# start and end time of the interval, in KitHub's datetime format,
# for example "2014-06-09T00:00:00+02:00"
eva_starttime_str = "2015-06-01T00:00:00+02:00"
eva_endtime_str = "2015-06-19T23:59:59+02:00"

###
# General options
###

# set to True for more output
verbose_output = True
# set to true if you want the timetable printed to stdout
terminal_timetable = False

input_file = "input.csv"
lecturers_file = "lecturers.csv"
rooms_file = "rooms.csv"
output_file = "timetable.ods"
output_comparison_file = "output.ods"

# translation of weekdays
# TODO: change to strftime
weekdays = {1: "Montag", 2: "Dienstag",
            3: "Mittwoch", 4: "Donnerstag", 5: "Freitag"}
weekdays_short = {1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr"}

# path of the directory where the data downloaded from the API is stored
json_directory = "courses"

# as %z is the offset with the format +HHMM, and without :,
# delete all : while parsing
datetime_format = "%Y-%m-%dT%H%M%S%z"  # 2014-06-11T19:00:00+02:00

# start time of blocks in the timetable
timetable_blocks = [{'time': time(hour=8, minute=0), 'block': 1},
                    {'time': time(hour=9, minute=45), 'block': 2},
                    {'time': time(hour=11, minute=30), 'block': 3},
                    {'time': time(hour=14, minute=0), 'block': 4},
                    {'time': time(hour=15, minute=45), 'block': 5},
                    {'time': time(hour=17, minute=30), 'block': 6}]

font_family = "Liberation Sans"
font_size_name = "12pt"
font_size = "10pt"

block_separator_border = "2pt solid #000000"
block_separator_appointments = "1pt solid #000000"

###
# End of configuration options
###

# rows, columns
# TODO: change everything to row, column
spreadsheet_timetable = SodsSpreadSheet(200, 20)

output_comparison_col_exclude = 4
output_comparison_col_uebung = 5
output_comparison_col_praktikum = 6
output_comparison_col_found_appointment = 7
output_comparison_col_name_vvz = 8

class Course:

    def __init__(self, id, lvnr, name, lecturers):
        self.id = int(id)
        self.lvnr = int(lvnr)
        self.name = name
        self.name_short = ""
        self.category = ""
        # TODO: rename to lecturers
        self.lecturers = [_.strip() for _ in lecturers.split(",")]
        # all occurrences over the whole semester
        self.appointments = []
        # just occurrences within the time frame, containing a list of
        # [weekday, block] pairs
        # TODO: choose a better name
        self.occurrences = []


class Appointment:

    def __init__(self, start, end, room):
        self.start = start
        self.end = end
        self.room = room

    def is_within_eva_period(self):
        return self.start > eva_starttime and self.start < eva_endtime

    def get_timetable_block(self):
        count = len(timetable_blocks)
        for i in range(0, count):
            # if event starts later than the last block starts, assign it to
            # the last block
            if self.start.time() >= timetable_blocks[i]['time'] and (i == count - 1 or self.start.time() < timetable_blocks[i + 1]['time']):
                return timetable_blocks[i]['block']


# download data of all courses into subdirectory
def get_courses(course_numbers):
    for course_number in course_numbers:
        get_course(course_number)


# download data in json format of one course to a file
def get_course(course_lvnr):
    if os.path.isfile("{0}/{1}.json".format(json_directory, course_lvnr)):
        verbose("course {0} already downloaded.".format(course_lvnr))
        return
    try:
        print("fetch course '{0}'.".format(course_lvnr))

        # use rest api to access data
        response = urllib.request.urlopen(
            "http://www.kithub.de/api/terms/{0}/events.json?type=detail&no={1}".format(term_id, course_lvnr)).readall().decode('utf8')
        # TODO: catch exceptions for next line
        data = json.loads(response)

        if not os.path.exists(json_directory):
            os.makedirs(json_directory)
        with open("{0}/{1}.json".format(json_directory, course_lvnr), 'w') as file:
            file.write(json.dumps(data, indent=2, sort_keys=True))

    except urllib.error.URLError as err:
        print("ERROR: URLError while fetching course '{0}': {1}".format(
            course_lvnr, err.reason))
    except urllib.error.HTTPError as err:
        print("ERROR: HTTPError '{0}' while fetching course '{1}': {2}".format(
            err.code, course_lvnr, err.reason))
    except ValueError:
        print("ERROR: ValueError while parsing content as JSON for course '{0}'.".format(
            course_lvnr))
    except:
        print(
                "ERROR: Unexpected error while fetching course '{0}': ".format(course_lvnr))
        print(sys.exc_info()[0])


def build_timetable():
    # iterate over all courses
    for course_lvnr, course in courses.items():
        found_appointment = False
        # iterate over all events
        for appointment in course.appointments:
            if appointment.is_within_eva_period():
                found_appointment = True

                # get information about position in timetable
                weekday = appointment.start.isoweekday()
                block = appointment.get_timetable_block()

                # append the date to the list of dates in the timetable
                if course_lvnr not in timetable[weekday][block]:
                    timetable[weekday][block][course_lvnr] = []
                timetable[weekday][block][course_lvnr].append(appointment)

                # append this [weekday, block] to the list of occurrences
                if [weekday, block] not in course.occurrences:
                    course.occurrences.append([weekday, block])

        if not found_appointment:
            courses_missed[course.lvnr] = course


def load_course_from_filesystem(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    if len(data) > 1:
        print(
                "WARNING: There is more than 1 object encoded in file {0}. Please have a look. For now, I only import the first.".format(filename))
    obj = data[0]
    # TODO: check if it's a dictionary
    course = Course(
            obj['id'], obj['no'], obj['name'], obj['lecturer'])
    course.appointments = course_parse_appointments(obj['dates'])
    return course


# replace datetime in string format by an actual datetime object
def course_parse_appointments(dates):
    appointments = []
    for date in dates:
        appointment = Appointment(parse_datetime(
            date["start_time"]), parse_datetime(date["end_time"]), date["room"])
        appointments.append(appointment)
    # sort the list by start date
    appointments.sort(key=lambda appointment: appointment.start)
    return appointments


# parse the datetime format of the kithub api and return a datetime object
def parse_datetime(str):
    str = str.replace(":", "")
    # ignore timezones
    return datetime.strptime(str, datetime_format).replace(tzinfo=None)


def verbose(str):
    if verbose_output:
        print(str)


def print_timetable(str):
    if terminal_timetable:
        print(str)

def column_name_from_number(column_number):
    return spreadsheet_timetable.encodeColName(column_number)


def cell_coordinate(row_number, column_number):
    return spreadsheet_timetable.encodeCellName(row_number, column_number)


# content must be string
def print_cell(spreadsheet, row_number, column_number, content, font_size=font_size, font_family=font_family):
    spreadsheet.setValue(cell_coordinate(row_number, column_number), content)
    spreadsheet.setStyle(cell_coordinate(row_number, column_number), font_family = font_family)
    spreadsheet.setStyle(cell_coordinate(row_number, column_number), font_size = font_size)


def print_row(spreadsheet, row_number, row):
    for i, cell in enumerate(row):
        print_cell(spreadsheet, row_number, i+1, cell)

def load_aliases_from_filesystem(filename):
    target = {}
    # get list of rooms and aliases from the configuration file
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        row_counter = 0
        for row in csvreader:
            if row_counter > 0:
                if not row[0] in target:
                    alias = row[1].strip()
                    # if there is no alias, use the original name
                    if alias == "":
                        alias = row[0]
                    target[row[0]] = alias
                else:
                    print("ERROR: Doubled entry in {0}, line {1}: {2}.".format(filename, row_counter, row[0]))
            row_counter += 1
        verbose("Read {0} rooms from {1}".format(row_counter, filename))
    return target

def write_aliases(filename, source):
    # write alias file back to disk
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(['Name', 'Alias'])
        for name, alias in source.items():
            if alias == name:
                alias = ""
            csvwriter.writerow([name, alias])


# holds all courses as Course objects with course.lvnr as key
courses = {}
# holds courses for which no appointment was found within the time interval
courses_missed = {}

# holds aliases for rooms
rooms = {}
new_rooms = False
# holds aliases for lecturers
lecturers = {}
new_lecturers = False

eva_starttime = parse_datetime(eva_starttime_str)
eva_endtime = parse_datetime(eva_endtime_str)

print("Printing time interval {0} to {1}".format(eva_starttime, eva_endtime))

with open(input_file, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    row_counter = 0
    for row in spamreader:
        if row_counter > 0 and row[output_comparison_col_exclude - 1] != "x":
            get_course(row[0])
            course = load_course_from_filesystem("{0}/{1}.json".format(json_directory, int(row[0])))
            course.category = row[1]
            course.name_short = row[2]
            if row[output_comparison_col_uebung - 1] == "x":
                course.name_short += " +Übung"
            if row[output_comparison_col_praktikum - 1] == "x":
                course.name_short += " +Prakt"
            if row[1] != "":
                course.name_short += " ({0})".format(row[1])
            courses[course.lvnr] = course
        row_counter += 1

lecturers = load_aliases_from_filesystem(lecturers_file)
rooms = load_aliases_from_filesystem(rooms_file)

# check if there are more lecturers
for course in courses.values():
    for lecturer in course.lecturers:
        # add to list of lecturer aliases
        if not lecturer in lecturers:
            lecturers[lecturer] = lecturer
            new_lecturers = True
if new_lecturers:
    verbose("Courses have lecturers that are not yet in {0}".format(lecturers_file))
    write_aliases(lecturers_file, lecturers)

# check if there are more rooms
for course in courses.values():
    for appointment in course.appointments:
        # add to list of lecturer aliases
        if not appointment.room in rooms:
            rooms[appointment.room] = appointment.room
            new_rooms = True
if new_rooms:
    verbose("Courses have rooms that are not yet in {0}".format(rooms_file))
    write_aliases(rooms_file, rooms)


spreadsheet_output_comparison = SodsSpreadSheet(row_counter, 10)

# holds all days, and within them all blocks and within these the courses
timetable = {}

for day in range(1, 6):
    blocks = {}
    for block in range(1, 9):
        blocks[block] = {}
    timetable[day] = blocks

# assemble the timetable
build_timetable()

# spreadsheet columns and rows start at 1, plus leave the first empty
column_start = 2
row_start = 2

# number of columns and rows per entry
appointment_width = 2
appointment_height = 3

# get maximum number of lectures that has to be fit into each block
# but set it to 1 at least
block_height = {}
for block in range(1, 9):
    block_height[block] = 1

for block in range(1, 9):
    for weekday in range(1, 6):
        new_height = len(timetable[weekday][block])
        if new_height > block_height[block]:
            block_height[block] = new_height

# print first column: block numbers
current_row = row_start + 1
for block in range(1, 9):
    print_cell(spreadsheet_timetable, current_row, column_start, str(block))
    current_row += block_height[block] * appointment_height

# print timetable
for weekday in range(1, 6):
    print_timetable("{0}".format(weekdays[weekday]))
    weekday_column = column_start + 1 + (weekday-1) * appointment_width
    block_row_start = row_start + 1
    print_cell(spreadsheet_timetable, row_start, weekday_column, weekdays[weekday], font_size_name)
    for block in range(1, 9):
        print_timetable("  {0}. Block".format(block))
        for i, course_lvnr in enumerate(timetable[weekday][block].keys()):
            course = courses[course_lvnr]
            print_timetable("    {0}, {1}".format(course.name, ", ".join([lecturers[_] for _ in course.lecturers])))
            course_row_start = block_row_start + i*appointment_height
            print_cell(spreadsheet_timetable, course_row_start, weekday_column, course.name_short, font_size_name)
            print_cell(spreadsheet_timetable, course_row_start + 1, weekday_column, ", ".join([lecturers[_] for _ in course.lecturers]))
            course_room = ""
            course_dates = ""
            for appointment in timetable[weekday][block][course_lvnr]:
                print_timetable("      {0}, {1}".format(appointment.start.strftime("%d.%m."), rooms[appointment.room]))
                if course_dates != "":
                    course_dates += ", "
                course_dates += appointment.start.strftime("%d.%m.")
                if course_room != str(rooms[appointment.room]):
                    if course_room != "":
                        course_room += ", "
                    course_room += str(rooms[appointment.room])
            course_other_dates = ""
            for weekday_other, block_other in course.occurrences:
                if not (weekday_other == weekday and block_other == block):
                    print_timetable(
                        "      Auch {0}/{1}".format(weekdays_short[weekday_other], block_other))
                    if course_other_dates != "":
                        course_other_dates += ", "
                    course_other_dates += "{0}/{1}".format(weekdays_short[weekday_other], block_other)
                    for appointment_other in timetable[weekday_other][block_other][course_lvnr]:
                        print_timetable(
                            "        {0}".format(appointment_other.start.strftime("%d.%m.")))
            if course_other_dates != "":
                course_dates += "; auch " + course_other_dates
            print_cell(spreadsheet_timetable, course_row_start, weekday_column + 1, course_room)
            print_cell(spreadsheet_timetable, course_row_start + 2, weekday_column, course_dates)
        block_row_start += block_height[block] * appointment_height


# set borders on timetable

# first the horizontal ones
block_row_start = row_start + 1
timetable_last_row = sum(block_height.values()) * appointment_height + block_row_start
for row in range(block_row_start, timetable_last_row, 3):
    spreadsheet_timetable.setStyle("{0}:{1}".format(cell_coordinate(row, column_start+1), cell_coordinate(row, 5*appointment_width + column_start)), border_top=block_separator_appointments)

# print first column: block numbers
current_row = row_start + 1
for block in range(1, 9):
    spreadsheet_timetable.setStyle("{0}:{1}".format(cell_coordinate(current_row, column_start+1), cell_coordinate(current_row, 5*appointment_width + column_start)), border_top=block_separator_border)
    current_row += block_height[block] * appointment_height

# now the vertical ones
# no border right of Friday
for weekday in range(1, 5):
    weekday_column = column_start + 1 + (weekday-1) * appointment_width + 1
    spreadsheet_timetable.setStyle("{0}:{1}".format(cell_coordinate(row_start, weekday_column), cell_coordinate(timetable_last_row - 1, weekday_column)), border_right=block_separator_border)

print("Für die folgenden {0} Veranstaltungen wurde kein Termin im gewählten Zeitfenster gefunden:".format(len(courses_missed.values())))
if not courses_missed:
    print("  keine")
else:
    for course in courses_missed.values():
        print("{0}, {1}, {2}".format(course.lvnr, course.name, course.lecturers))


if os.path.exists(output_file):
    if input("File '{0}' already exists, overwrite? (y/N) ".format(output_file)) == "y":
        os.remove(output_file)
    else:
        print("Abort.")
        exit(1)

# produce ODS file for timetable
Sods_ods = SodsOds(spreadsheet_timetable)
Sods_ods.save(output_file)

# produce ODS file for comparison of input and output
with open(input_file, newline='') as csvfile_input:
    spamreader = csv.reader(csvfile_input, delimiter=',', quotechar='"')

    first_line = True
    for i, row in enumerate(spamreader):
        if first_line:
            # copy the table header
            print_row(spreadsheet_output_comparison, i+1, row)
            spreadsheet_output_comparison.setValue(cell_coordinate(i+1, output_comparison_col_name_vvz), "Name aus VVZ")
            spreadsheet_output_comparison.setValue(cell_coordinate(i+1, output_comparison_col_found_appointment), "Termin gefunden?")
            first_line = False
        else:
            print_row(spreadsheet_output_comparison, i+1, row)
            if int(row[0]) not in courses_missed and int(row[0]) not in courses:
                found_appointment = "…"
            elif int(row[0]) not in courses_missed:
                found_appointment = "ja"
            else:
                found_appointment = "nein"
            if found_appointment != "…":
                spreadsheet_output_comparison.setValue(cell_coordinate(i+1, output_comparison_col_name_vvz), courses[int(row[0])].name)
                spreadsheet_output_comparison.setValue(cell_coordinate(i+1, output_comparison_col_found_appointment), found_appointment)
                # color the cell if the name is different as this could be an issue
                if row[2] != courses[int(row[0])].name:
                    spreadsheet_output_comparison.setStyle(cell_coordinate(i+1, output_comparison_col_name_vvz), background_color= "#ff0000")
            # color the cell if no appointment was found in the given time interval
            if found_appointment == "nein":
                spreadsheet_output_comparison.setStyle(cell_coordinate(i+1, output_comparison_col_found_appointment), background_color= "#ff0000")
            elif found_appointment == "…":
                spreadsheet_output_comparison.setStyle(cell_coordinate(i+1, output_comparison_col_found_appointment), background_color= "#ffffe0")


if os.path.exists(output_comparison_file):
    if input("File '{0}' already exists, overwrite? (y/N) ".format(output_comparison_file)) == "y":
        os.remove(output_comparison_file)
    else:
        print("Abort.")
        exit(1)

Sods_ods = SodsOds(spreadsheet_output_comparison)
Sods_ods.save(output_comparison_file)

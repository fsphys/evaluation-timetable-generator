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
from datetime import datetime, time
from pprint import pprint

###
# Configuration options
###

# Lehrveranstaltungsnummern of courses to get from KitHub
lvnrs = [4010031, 4010111, 4010011]

# translation of weekdays
# TODO: change to strftime
weekdays = {1: "Montag", 2: "Dienstag",
            3: "Mittwoch", 4: "Donnerstag", 5: "Freitag"}
weekdays_short = {1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr"}

# get this from http://www.kithub.de/api/#!/terms/GET-terms---format-_get_0
term_id = 7895  # Wintersemester 2014/15
# term_id = 7022 # Sommersemester 2014
# term_id = 4521 # Wintersemester 2013/14

# path of the directory where the data downloaded from the API is stored
json_directory = "courses"

# as %z is the offset with the format +HHMM, and without :,
# delete all : while parsing
datetime_format = "%Y-%m-%dT%H%M%S%z"  # 2014-06-11T19:00:00+02:00

# start and end time of the interval, in KitHub's datetime format,
# for example "2014-06-09T00:00:00+02:00"
eva_starttime_str = "2014-12-01T00:00:00+02:00"
eva_endtime_str = "2014-12-12T23:59:59+02:00"

# start time of blocks in the timetable
timetable_blocks = [{'time': time(hour=8, minute=0), 'block': 1},
                    {'time': time(hour=9, minute=45), 'block': 2},
                    {'time': time(hour=11, minute=30), 'block': 3},
                    {'time': time(hour=14, minute=0), 'block': 4},
                    {'time': time(hour=15, minute=45), 'block': 5},
                    {'time': time(hour=17, minute=30), 'block': 6}]

###
# End of configuration options
###


class Course:

    def __init__(self, id, lvnr, name, lecturer):
        self.id = id
        self.lvnr = lvnr
        self.name = name
        self.lecturer = lecturer
        # all occurrences over the whole semester
        # TODO: choose a better name
        self.dates = []
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
def get_course(course_number):
    try:
        verbose("fetch course '{0}'.".format(course_number))

        # use rest api to access data
        response = urllib.request.urlopen(
            "http://www.kithub.de/api/terms/{0}/events.json?type=detail&no={1}".format(term_id, course_number)).readall().decode('utf8')
        # TODO: catch exceptions for next line
        data = json.loads(response)

        if not os.path.exists(json_directory):
            os.makedirs(json_directory)
        with open("{0}/{1}.json".format(json_directory, course_number), 'w') as file:
            # TODO: unicode? ü gets written as \u00fc
            file.write(json.dumps(data, indent=2, sort_keys=True))

    except urllib.error.URLError as err:
        print("URLError while fetching course '{0}': {1}".format(
            course_number, err.reason))
    except urllib.error.HTTPError as err:
        print("HTTPError '{0}' while fetching course '{1}': {2}".format(
            err.code, course_number, err.reason))
    except ValueError:
        print("ValueError while parsing content as JSON for course '{0}'.".format(
            course_number))
    except:
        print(
            "Unexpected error while fetching course '{0}': ".format(course_number))
        print(sys.exc_info()[0])


def build_timetable():
    # iterate over all courses
    for course_id, course in courses.items():
        found_date = False
        # iterate over all events
        for date in course.dates:
            if date.is_within_eva_period():
                found_date = True

                # get information about position in timetable
                weekday = date.start.isoweekday()
                block = date.get_timetable_block()

                # append the date to the list of dates in the timetable
                if not course_id in timetable[weekday][block]:
                    timetable[weekday][block][course_id] = []
                timetable[weekday][block][course_id].append(date)

                # append this [weekday, block] to the list of occurrences
                if not [weekday, block] in course.occurrences:
                    course.occurrences.append([weekday, block])

        #sorted(timetable[weekday][block][course_id], key=lambda appointment: appointment.start)

        if not found_date:
            print(
                "ERROR: Did not find any date within the evaluation period for the course '{0}', LV-Nr. {1}!".format(course.name, course.lvnr))


def load_courses_from_filesystem():
    for file in glob.glob("{0}/*.json".format(json_directory)):
        with open(file, 'r') as f:
            data = json.load(f)
        if len(data) > 1:
            print(
                "There is more than 1 object encoded in file {0}. Please have a look. For now, I import them all.".format(file))
        for i, object in enumerate(data):
            course = Course(
                object['id'], object['no'], object['name'], object['lecturer'])
            course.dates = course_parse_dates(object['dates'])
            courses[course.id] = course
            #print("{0}. {1}, {2}, {3}, {4}".format(i, course.id, course.lvnr, course.name, course.lecturer))
            # for i, date in enumerate(course.dates):
            #print("  {0}. {1}–{2} in {3}".format(i, date.start, date.end, date.room))


# replace datetime in string format by an actual datetime object
def course_parse_dates(dates):
    dates_list = []
    for date in dates:
        date_object = Appointment(parse_datetime(
            date["start_time"]), parse_datetime(date["end_time"]), date["room"])
        dates_list.append(date_object)
    # sort the list by start date
    dates_list.sort(key=lambda appointment: appointment.start)
    return dates_list


# parse the datetime format of the kithub api and return a datetime object
def parse_datetime(str):
    str = str.replace(":", "")
    # ignore timezones
    return datetime.strptime(str, datetime_format).replace(tzinfo=None)


def verbose(str):
    print(str)


eva_starttime = parse_datetime(eva_starttime_str)
eva_endtime = parse_datetime(eva_endtime_str)

print("Printing time interval {0} to {1}".format(eva_starttime, eva_endtime))

# holds all courses as Course objects with course.id as key
courses = {}

# holds all days, and within them all blocks and within these the courses
timetable = {}

for day in range(1, 6):
    blocks = {}
    for block in range(1, 9):
        blocks[block] = {}
    timetable[day] = blocks

# download data from KitHub, this saves them to disk
get_courses(lvnrs)

# load the files
load_courses_from_filesystem()

# assemble the timetable
build_timetable()

# print timetable
for weekday in range(1, 6):
    print("{0}".format(weekdays[weekday]))
    for block in range(1, 9):
        print("  {0}. Block".format(block))
        for course_id in timetable[weekday][block].keys():
            course = courses[course_id]
            print("    {0}, {1}".format(course.name, course.lecturer))
            for date in timetable[weekday][block][course_id]:
                print("      {0}".format(date.start.strftime("%d.%m.")))
            for otherweekday, otherblock in course.occurrences:
                if not (otherweekday == weekday and otherblock == block):
                    print(
                        "      Auch {0}/{1}".format(weekdays_short[otherweekday], otherblock))
                    for appointment in timetable[otherweekday][otherblock][course_id]:
                        print(
                            "        {0}".format(appointment.start.strftime("%d.%m.")))

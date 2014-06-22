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

class Course:
  dates = []
  
  def __init__(self, name, lecturer):
    self.name = name
    self.lecturer = lecturer


class Date:
  def __init__(self, start, end, room):
    self.start = start
    self.end   = end
    self.room  = room
  
  def is_within_eva_period(self):
    return self.start > eva_starttime and self.start < eva_endtime
  
  def get_timetable_block(self):
    count = len(timetable_blocks)
    for i in range(0, count):
      # if event starts later than the last block starts, assign it to the last block
      if self.start.time() >= timetable_blocks[i]['time'] and (i == count - 1 or self.start.time() <= timetable_blocks[i+1]['time']):
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
    response = urllib.request.urlopen("http://www.kithub.de/api/terms/{0}/events.json?type=detail&no={1}".format(term_id, course_number)).readall().decode('utf8')
    # TODO: catch exceptions
    data = json.loads(response)
    
    if not os.path.exists(json_directory):
      os.makedirs(json_directory)
    with open("{0}/{1}.json".format(json_directory, course_number), 'w') as file:
      # TODO: unicode? ü gets written as \u00fc
      file.write(json.dumps(data, indent=2, sort_keys=True))
      #pprint(response, stream=file)
      #file.write(response)
    
  except urllib.error.URLError as err:
    print("URLError while fetching course '{0}': {1}".format(course_number, err.reason))
  except urllib.error.HTTPError as err:
    print("HTTPError '{0}' while fetching course '{1}': {2}".format(err.code, course_number, err.reason))
  except ValueError:
    print("ValueError while parsing content as JSON for course '{0}'.".format(course_number))
  except:
    print("Unexpected error while fetching course '{0}': ".format(course_number))
    print(sys.exc_info()[0])

def build_timetable():
  # iterate over all courses
  for course in courses:
    # iterate over all events
    for date in course.dates:
      if date.is_within_eva_period():
        # include in the timetable
        weekday = date.start.isoweekday()
        block   = date.get_timetable_block()
        timetable[weekday][block].append(course.name)

def load_courses_from_filesystem():
  for file in glob.glob("{0}/*.json".format(json_directory)):
    with open(file, 'r') as f:
      data = json.load(f)
    if len(data) > 1:
      print("There is more than 1 object encoded in file {0}. Please have a look. For now, I import them all.".format(file))
    for o in data:
      course = Course(o['name'], o['lecturer'])
      course.dates = course_parse_dates(o['dates'])
      courses.append(course)

# replace datetime in string format by an actual datetime object
def course_parse_dates(dates):
  dates_list = []
  for date in dates:
    date_object = Date(parse_datetime(date["start_time"]), parse_datetime(date["end_time"]), date["room"])
    dates_list.append(date_object)
  return dates_list

# parse the datetime format of the kithub api and return a datetime object
def parse_datetime(str):
  str = str.replace(":", "")
  # ignore timezones
  dt = datetime.strptime(str, datetime_format).replace(tzinfo=None)
  return dt

def verbose(str):
  print(str)


# TODO: recognize if a course has no event within the evaluation period

term_id = 7022 # Sommersemester 2014
#term_id = 4521 # Wintersemester 2013/14
json_directory = "courses"

# as %z is the offset with the format +HHMM, and without :, 
# delete all : while parsing
datetime_format = "%Y-%m-%dT%H%M%S%z" # 2014-06-11T19:00:00+02:00

eva_starttime = parse_datetime("2014-06-09T00:00:00+02:00")
eva_endtime   = parse_datetime("2014-06-27T23:59:59+02:00")

timetable_blocks = [{'time': time(hour= 8, minute= 0), 'block': 1},
                    {'time': time(hour= 9, minute=45), 'block': 2},
                    {'time': time(hour=11, minute=30), 'block': 3},
                    {'time': time(hour=14, minute= 0), 'block': 4},
                    {'time': time(hour=15, minute=45), 'block': 5},
                    {'time': time(hour=17, minute=30), 'block': 6}]

# holds all courses
courses = []

# holds all days, and within them all blocks and within these the courses
timetable = {}

for day in range(1, 6):
  blocks = {}
  for block in range(1, 9):
    blocks[block] = []
  timetable[day] = blocks

#get_courses([4010021, 4010041, 4012142])
load_courses_from_filesystem()
build_timetable()

#for course in courses:
#  print(course)
  
pprint(timetable)

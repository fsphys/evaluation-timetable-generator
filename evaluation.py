#!/usr/bin/env python3
'''
Documentation, License etc.

@package evaluation
'''
import sys
import os
import glob
import json
import urllib.request
import datetime

term_id = 7022 # Sommersemester 2014
#term_id = 4521 # Wintersemester 2013/14
json_directory = "courses"

# as %z is the offset with the format +HHMM, and without :, 
# delete all : while parsing
datetime_format = "%Y-%m-%dT%H%M%S%z" # 2014-06-11T19:00:00+02:00

eva_starttime = "2014-06-09T00:00:00+02:00"
eva_endtime   = "2014-06-27T23:59:59+02:00"

courses = []

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
    
    if not os.path.exists(json_directory):
      os.makedirs(json_directory)
    with open("{0}/{1}.json".format(json_directory, course_number), 'w') as file:
      file.write(response)
    
  except urllib.error.URLError as err:
    print("URLError while fetching course '{0}': {1}".format(course_number, err.reason))
  except urllib.error.HTTPError as err:
    print("HTTPError '{0}' while fetching course '{1}': {2}".format(err.code, course_number, err.reason))
  except ValueError:
    print("ValueError while parsing content as JSON for course '{0}'.".format(course_number))
  except:
    print("Unexpected error while fetching course '{0}': ".format(course_number))
    print(sys.exc_info()[0])

#def generate_timetable():
#  load_courses_from_filesystem()
  
def load_courses_from_filesystem():
  for file in glob.glob("{0}/*.json".format(json_directory)):
    with open(file, 'r') as f:
      data = json.loads(f.read())
    if len(data) > 1:
      print("There is more than 1 object encoded in file {0}. Please have a look. For now, I import them all.".format(file))
    for o in data:
      course_parse_datetime(o)
      courses.append(o)

# replace datetime in string format by an actual datetime object
def course_parse_datetime(course):
  for event in course["dates"]:
    event["start_time"] = parse_datetime(event["start_time"])
    event["end_time"]   = parse_datetime(event["end_time"])

# parse the datetime format of the kithub api and return a datetime object
def parse_datetime(str):
  str = str.replace(":", "")
  dt = datetime.datetime.strptime(str, datetime_format)
  return dt

def verbose(str):
  print(str)

#get_courses([4010021, 4010041, 4012142])
load_courses_from_filesystem()

for course in courses:
  print(course)
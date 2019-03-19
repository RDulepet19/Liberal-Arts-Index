
# coding: utf-8

# MIT License
# 
# Copyright (c) 2019 Riya Dulepet <riyadulepet123@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Thanks to the entire Columbia INCITE team for suggestions/recommendations, collaboration, critic, advice, and mentoring. This code was generated as part of internship @INCITE Columbia for Lit Index project.

# # Scraper for Morehouse College Course Description

# ## Setup environment
# * Make sure Java is installed
# * Download [Apache Tika](http://apache.mirrors.ionfish.org/tika/tika-app-1.19.1.jar)

# ## Download Morehouse College Course Descriptions
# * [Download Morehouse College Course Description PDF](https://www.morehouse.edu/media/admissions/Course-Catalog-2018-2019_rev1107-2018.pdf)
# 
# 

# ## Extract Plain Text file from PDF using Apache TIKA
# * java -jar tika-app-1.19.1.jar -t Course-Catalog-2018-2019_rev1107-2018.pdf > Morehouse-College-Catalog-2018-2019.txt
# 

# ### Extract manually exact name and unit ID
# [IPED website](https://nces.ed.gov/collegenavigator/?q=Morehouse&s=all&id=140553#general)
# * `UnitID`	140553
# * `Name`	Morehouse College

# In[ ]:


INSTITUTION_ID = '140553'
INSTITUTION_NAME = 'Morehouse College'
CATALOG_YEAR = '2018' # It's the 2018-2019 academic year catalog
CATALOG_URL = 'https://www.morehouse.edu/media/admissions/Course-Catalog-2018-2019_rev1107-2018.pdf'


# In[ ]:


import numpy as np
import re
import json

# constants
# added manually following departments to map courses
MAP_DEPARTMENTS = {"AAS":"African American Studies",                    "MSL":"Military Science and Leadership",                    "CHI":"Chinese Studies",                    "HSOC":"Sociology",                    "BUS":"Business",                    "HCHE":"Chemistry",                    "HECO":"Economics",                    "HUST":"Urban Studies",                    "HCTM":"Cinema, Television, & Emerging Media Studies",                    "General Education":"General Education", "BIO":"Biology",                    "BA":"Business Administration", "CHE":"Chemistry",                    "COM":"Communications", "CSC":"Computer Science",                    "EGR":"Engineering", "ECO":"Economics",                    "ENG":"English", "HIS":"History",                    "HPED":"Health and Physical Education",                    "HLS":"Leadership Studies", "MTH":"Mathematics",                    "FLF":"French", "FLG":"German",                    "FLJ":"Japanese", "FLP":"Portuguese",                    "FLS":"Spanish", "HMUS":"Music",                    "PHI":"Philosophy", "REL":"Religion",                    "PHY":"Physics", "PSC":"Political Science",                    "PSY":"Psychology", "SOC":"Sociology",                    "UST":"Urban Studies"}

REGEX_PREREQUISITE = r'Prerequisite[s]*:\s*(.*?)\.*$'
PATTERN_REGEX_PREREQUISITE = re.compile(REGEX_PREREQUISITE, re.IGNORECASE)
REGEX_COREQUISITE = r'Co\-*requisite[s]*:\s*(.*?)\.|Co\-*requisite[s]*:\s*(.*?)\.*$'
PATTERN_REGEX_COREQUISITE = re.compile(REGEX_COREQUISITE, re.IGNORECASE)


# In[ ]:


class Department:
    line_no = 0
    code = ""
    desc = ""

class Course:
    line_no = 0
    dept_code = ""
    title = ""
    code = ""
    desc = ""
    credit_hours = ""

Departments = {}
Courses = {}
Delimiters = {}


# In[ ]:


# department names extraction with line numbers
import re
pattern = re.compile("^[A-Z]+\s+[A-Z]{0,}\s*\(([A-Z]+)\)|^Courses in ([\w ]{1,})$")

num_matches = 0
for i, line in enumerate(open('Morehouse-College-Catalog-2018-2019.txt')):
    for match in re.finditer(pattern, line):
        match_tokens = list(match.groups())
        match_tokens = [word.strip() for word in match_tokens if word]
        
        print('Found on line %s: %s' % (i+1, match_tokens[0]))
        a_dept = Department()
        a_dept.line_no = i+1
        a_dept.code = match_tokens[0]
        a_dept.desc = MAP_DEPARTMENTS[match_tokens[0]]
        Departments[int(a_dept.line_no)] = a_dept
        
        num_matches += 1
print("num_matches=", num_matches)


# for key in sorted(Departments.keys()):
#     print("%s: %s" % (key, Departments[key].desc))

# In[ ]:


# strong indicator of end of department
import re

num_matches = 0
for i, line in enumerate(open('Morehouse-College-Catalog-2018-2019.txt')):
    if line.strip().isupper():
        # look for all upper case lines
    # for match in re.finditer(pattern, line):
        # match_tokens = list(match.groups())
        # match_tokens = [word.strip() for word in match_tokens if word]
        
        # print('Found on line %s: %s' % (i+1, match_tokens[0]))
        # Delimiters[int(i+1)] = match_tokens[0]
        print('Found on line %s: %s' % (i+1, line.strip()))
        Delimiters[int(i+1)] = line.strip()
        num_matches += 1
print("num_matches=", num_matches)


# for key in sorted(Delimiters.keys()):
#     print("%s: %s" % (key, Delimiters[key]))

# In[ ]:


def getClosestDelimiterLineNo(course_line_no):
    for key in sorted(Delimiters.keys()):
        if key > course_line_no:
            return key
    return -1

def getClosestDepartment(course_line_no):
    dept_match = ""
    
    for key in sorted(Departments.keys()):
        # print("%s: %s" % (key, Departments[key].desc))
        if key > course_line_no:
            break
        dept_match = Departments[key].code
        
    return dept_match


# In[ ]:


# course number, title, credit hours extraction with line numbers
import re
pattern = re.compile("^ *([A-Z0-9\-]{3,9} [A-Z0-9\-]{0,4})[\.]{0,1} (.*) +([\d\-]{1,4}) +[\w]{0,6} *hours* *$|^ *([A-Z0-9\-]{3,9})[\.]{0,1}\ (.*) +([\d\-]{1,4}) +[\w]{0,6} *hours* *$")

num_matches = 0
for i, line in enumerate(open('Morehouse-College-Catalog-2018-2019.txt')):
    # print("outer loop")
    for match in re.finditer(pattern, line):
        # print("inner loop")
        match_tokens = list(match.groups())
        match_tokens = [word.strip() for word in match_tokens if word]
        if any(x in match_tokens[1] for x in ["hour", "hours", "Elective"]):
            continue
        print('Found on line %s: %s' % (i+1, line))
        dept_pattern = re.compile("^([A-Z]+)")
        dept_name = re.match(dept_pattern, match_tokens[0])
        # initialize new course
        a_course = Course()
        a_course.line_no = int(i+1)
        a_course.dept_code = ""
        a_course.ignore = False
        a_course.title = match_tokens[1].strip()
        a_course.code = match_tokens[0].strip()
        a_course.desc = ""
        a_course.closest_delimeter = -1
        a_course.offerings = ""
        a_course.description = ""
        a_course.prerequisites = ""
        a_course.corequisites = ""
        a_course.notes = ""
        a_course.requirements = ""
        
        a_course.credit_hours = match_tokens[2].strip()
        if (dept_name):
            a_course.dept_code = match_tokens[0][dept_name.span()[0]:dept_name.span()[1]].strip()
            a_course.code = match_tokens[0][dept_name.span()[1]:].strip()
            # print("\tdepartment_code = ", a_course.dept_code)
            # print("\tcourse_no = ", a_course.code)
        else:
            a_course.dept_code = getClosestDepartment(int(i+1))
        a_course.closest_delimeter = getClosestDelimiterLineNo(int(i+1))
        # print('\tclosest delimiter = ', a_course.closest_delimeter)
        ################## HANDLE SOME SPECIAL CASES
        # handle some special cases with messed up title (mixed with either course number or credit hours)
        # case 1: messed up credit hours mixed in title
        split_fields = a_course.title.split("0 to")
        if len(split_fields) == 2:
            # yes match
            a_course.title = split_fields[0].strip()
            a_course.credit_hours = "0 to " + a_course.credit_hours.strip()
        # case 2: messed up course number mixed in title
        if not re.match("^[A-Z]", a_course.title):
            # doesn't start with caps letter, then something is messed and mixed
            courseno_pattern = re.compile("^(.*?)\.*\s([A-Z].*)$")
            # courseno_pattern = re.compile("^([0-9]+[A-Z]*[\-][0-9]+[A-Z]*)\.*\s(.*)$")
            found_courseno_in_title = re.findall(courseno_pattern, a_course.title)
            if len(found_courseno_in_title) > 0:
                a_course.code = a_course.code + " " + found_courseno_in_title[0][0]
                a_course.code = a_course.code.strip()
                a_course.title = found_courseno_in_title[0][1]
        # case 4: (Fall) and 401 (Spring) The Africana Studies Capstone
        courseno_pattern = re.compile("^(\(Fall\)\sand\s\d+\s\(Spring\))\s(.*)")
        found_courseno_in_title = re.findall(courseno_pattern, a_course.title)
        if len(found_courseno_in_title) > 0:
            a_course.code = a_course.code + ' ' + found_courseno_in_title[0][0]
            a_course.title = found_courseno_in_title[0][1]
        # skip if empty
        if a_course.code.strip():
            Courses[a_course.line_no] = a_course
        num_matches += 1
print("num_matches=", num_matches)        


# In[ ]:


for key in sorted(Courses.keys()):
    print("%d: %s, %s, %s, %s" % (key, Courses[key].dept_code, Courses[key].code, Courses[key].title, Courses[key].credit_hours))


# In[ ]:


# now go through the file again to fill course description
current_course = None
num_empty_lines = 0
for i, line in enumerate(open('Morehouse-College-Catalog-2018-2019.txt')):
    if i+1 in Courses.keys():
        # print("found course at: %d" % (i+1))
        current_course = Courses[i+1]
        num_empty_lines = 0
    else:
        if current_course:
            if  (i+1 > current_course.line_no) and (i+1 < current_course.closest_delimeter):
                # check if empty line
                if not line.strip():
                    num_empty_lines += 1
                else:
                    num_empty_lines = 0
                    # if we find course pattern inside course, then ignore the course
                    course_pattern = re.compile("^\s*([A-Z0-9\-]{3,9}\s[A-Z0-9\-]{0,4})[\.]{0,1}\s(.*)\s+([\d\-]{1,4})|^\s*([A-Z0-9\-]{3,9})[\.]{0,1}\\s(.*)\s+([\d\-]{1,4})")
                    found_course_patterns = re.findall(course_pattern, line.strip())
                    if len(found_course_patterns) > 0:
                        # bunch of empty lines so assume end of current course
                        current_course.ignore = True
                        current_course = None
                        num_empty_lines = 0
                    else:
                        current_course.desc += " "
                        current_course.desc += line.strip()
                # if num_empty_lines >= 4:
                    # bunch of empty lines so assume end of current course
                    # current_course = None
                    # num_empty_lines = 0


# In[ ]:


# fill prerequisite and corequisite details, if present
for key in sorted(Courses.keys()):
    course = Courses[key]
    if not course.ignore:
        val = PATTERN_REGEX_PREREQUISITE.findall(course.desc)
        if len(val) > 0:
            course.prerequisites = val[0]
        val = PATTERN_REGEX_COREQUISITE.findall(course.desc)
        if len(val) > 0:
            val = [word.strip() for word in val[0] if word]
            course.corequisites = val[0]


# In[ ]:


for key in sorted(Courses.keys()):
    if not Courses[key].ignore:
        print("\n%d: %s, %s, %s, %s" % (key, Courses[key].dept_code, Courses[key].code, Courses[key].title, Courses[key].credit_hours))
        print ("\t%s" % (Courses[key].desc))
        print ("\t\tPrerequisites: %s" % (Courses[key].prerequisites))
        print ("\t\tcorequisites: %s" % (Courses[key].corequisites))


# In[ ]:


import pandas as pd
      
def dump_output(courses, file_to_save):
    df_college = pd.DataFrame(columns=['ipeds_id', 'ipeds_name', 'catalog_year', 'url',                                        'subject', 'subject_code', 'course_number', 'description',                                        'course_name', 'credits', 'prereqs', 'corequisites_raw',                                        'offerings_raw', 'notes_raw', 'requirements_raw'])
    for key in sorted(courses.keys()):
        course = Courses[key]
        # handle only records with course description, otherwise ignore
        if not course.ignore:
            df_college.loc[len(df_college)] = [INSTITUTION_ID, INSTITUTION_NAME,                                                CATALOG_YEAR, CATALOG_URL,                                                MAP_DEPARTMENTS[course.dept_code],                                                course.dept_code,                                                course.code,                                                course.desc,                                                course.title,                                                course.credit_hours,                                                course.prerequisites, course.corequisites,                                                course.offerings,                                                course.notes,                                                course.requirements]
    df_college.to_csv(file_to_save, index=False)


# In[ ]:


dump_output(Courses, "data/morehouse_college_raw.csv")


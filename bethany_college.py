
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

# # Scraper for Bethany College Course Description

# ## Setup environment
# * Make sure Java is installed
# * Download [Apache Tika](http://apache.mirrors.ionfish.org/tika/tika-app-1.19.1.jar)

# ## Download Bethany College Course Descriptions
# * [Download Bethany College Course Description PDF](http://2a2fc3rfbvx3l0sao396kxen-wpengine.netdna-ssl.com/academics/wp-content/uploads/sites/4/2018/08/Course-Catalogue-FINAL-8-27-18.pdf)
# 
# 

# ## Extract Plain Text file from PDF using Apache TIKA
# * java -jar tika-app-1.19.1.jar -t Course-Catalogue-FINAL-8-27-18.pdf > bethany_college_course_catalog.txt
# 

# ### Extract manually exact name and unit ID
# [IPED website](https://nces.ed.gov/collegenavigator/?q=bethany+college&s=all&id=237181)
# * `UnitID`	237181
# * `Name`	Bethany College

# In[1]:


INSTITUTION_ID = '237181'
INSTITUTION_NAME = 'Bethany College'
CATALOG_YEAR = '2018' # It's the 2018-2019 academic year catalog
CATALOG_URL = 'http://2a2fc3rfbvx3l0sao396kxen-wpengine.netdna-ssl.com/academics/wp-content/uploads/sites/4/2018/08/Course-Catalogue-FINAL-8-27-18.pdf'


# In[2]:


import numpy as np
import re
# constants
# added manually following departments to map courses
MAP_DEPARTMENTS = { "BIOL":"Biology",                    "ACCT":"Accounting",                    "BUSI":"Business",                    "COMM":"Communications",                    "EDUC":"Education",                    "RDNG":"Reading",                    "SPED":"Special Education",                    "HIST":"History",                    "ENGL":"English",                    "PHIL":"Philosophy",                    "INTD":"Interdisciplinary",                    "HLTH":"Health",                    "CHEM":"Chemistry",                    "ECON":"Economics",                    "MATH":"Mathematics",                    "PHYS":"Physics",                    "PSYC":"Psychology",                    "SOCI":"Sociology",                    "MUSI":"Music",                    "THEA":"Theatre",                    "SPED":"Special Education",                    "EQUI":"Equine Studies",                    "POLS":"Political Science",                    "RELS":"Religious Studies",                    "PHED":"Physical Education",                    "CPSC":"Computer Science",                    "SOWO":"Social Work",                    "VISA":"Visual Art",                    "FDST":"Fundamental Studies",                    "BFYE":"Bethany First-Year Experience",                    "PASS":"Program for Academic and Social Success",                    "GENS":"General Science",                    "CHIN":"Chinese",                    "JAPN":"Japanese",                    "SPAN":"Spanish",                    "FREN":"French",                    "GRMN":"German",                    "HEBR":"Hebrew",                    "FINA":"Fine Arts",                    "ARBC":"Arabic",                    "ITAL":"Italian",                    "WLAC":"World Languages",                    "SOSC":"Social Science",                    "CRJU":"Criminal Justice",                    "HSEM":"Honors core"
}

# REGEX_DEPARTMENT_NAME = r'^\w+{1,}\s+Courses*\s*$'
# PATTERN_REGEX_DEPARTMENT_NAME = re.compile(REGEX_DEPARTMENT_NAME)

REGEX_NEW_COURSE = r"^([A-Z]{4})\s+(\d+\-*\d+)\s+(.*)\s(\d+\-*\s*\d*)\s*[credit]{0,}s*\s*[each]{0,}\s*$"
PATTERN_REGEX_NEW_COURSE = re.compile(REGEX_NEW_COURSE) #, re.IGNORECASE)
REGEX_ALT_NEW_COURSE = r"^([A-Z]{4})\s+(\d+\-*\d+)\s+(.*)\sNon\-C*c*redit\s*$"
PATTERN_ALT_REGEX_NEW_COURSE = re.compile(REGEX_ALT_NEW_COURSE) #, re.IGNORECASE)


# In[3]:


import json

class Course:
    'Common base class for all courses'
    REGEX_OFFERINGS = r'Offered\s*(.*?)\.'
    PATTERN_REGEX_OFFERINGS = re.compile(REGEX_OFFERINGS, re.IGNORECASE)

    REGEX_NOT_OFFERINGS = r'Not Offered\s*(.*?)\.'
    PATTERN_REGEX_NOT_OFFERINGS = re.compile(REGEX_NOT_OFFERINGS, re.IGNORECASE)
    
    REGEX_PARTIAL_COURSE_NAME = r'^.*?\)\s+[A-Z]'
    PATTERN_REGEX_PARTIAL_COURSE_NAME = re.compile(REGEX_PARTIAL_COURSE_NAME, re.IGNORECASE)
    
    REGEX_PREREQUISITE = r'Prerequisite[s]*:\s*(.*?)\.*$'
    PATTERN_REGEX_PREREQUISITE = re.compile(REGEX_PREREQUISITE, re.IGNORECASE)

    REGEX_COREQUISITE = r'Co\-*requisite[s]*:\s*(.*?)\.|Co\-*requisite[s]*:\s*(.*?)\.*$'
    PATTERN_REGEX_COREQUISITE = re.compile(REGEX_COREQUISITE, re.IGNORECASE)
    
    REGEX_NOTES = r'Note[s]*:\s*(.*?)\.'
    PATTERN_REGEX_NOTES = re.compile(REGEX_NOTES, re.IGNORECASE)


    # make class JSON serializable
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
        
    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4, width=1)
    
    def __init__(self, course_num = "", name = "", credit_hours = "0", dept_code = ""):
        # initialize class
        self.course_num = course_num
        self.name = name
        self.credit_hours = credit_hours
        self.dept_code = dept_code
        
        # other member variables
        self.offerings = ""
        self.description = ""
        self.prerequisites = ""
        self.corequisites = ""
        self.notes = ""
        self.requirements = ""

    def set_name(self, name):
        self.name = name
    
    def set_dept_code(self, dept_code):
        self.dept_code = dept_code

    def set_course_num(self, course_num):
        self.course_num = course_num
    
    def set_credit_hours(self, credit_hours):
        self.credit_hours = credit_hours

    def set_offering(self, offerings):
        self.offerings = offerings
    
    def check_and_update_offerings_description_lines(self, line):
        self.description += " "
        self.description += line


# In[4]:


import pandas as pd
      
def dump_output(courses, file_to_save):
    df_college = pd.DataFrame(columns=['ipeds_id', 'ipeds_name', 'catalog_year', 'url',                                        'subject', 'subject_code', 'course_number', 'description',                                        'course_name', 'credits', 'prereqs', 'corequisites_raw',                                        'offerings_raw', 'notes_raw', 'requirements_raw'])
    for course in courses:
        # skip courses that have course description less than 65 characters or
        # if the course starts with [ or (, then ignore that course
        # if (not re.search('^[\[\(]', course.description)) and (len(course.description) > 65):
        # also ignore any content in paranthesis in course.name
        df_college.loc[len(df_college)] = [INSTITUTION_ID, INSTITUTION_NAME,                                            CATALOG_YEAR, CATALOG_URL,                                            MAP_DEPARTMENTS[course.dept_code],                                            course.dept_code,                                            course.course_num,                                            course.description.strip(),                                            course.name,                                            course.credit_hours,                                            course.prerequisites.strip(), course.corequisites.strip(),                                            course.offerings.strip(),                                            course.notes.strip(),                                            course.requirements.strip()]
    df_college.to_csv(file_to_save, index=False)


# In[5]:


import re, random
Courses = []

def main():
    global INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, CATALOG_URL
    global Courses 
    
    found_new_course = False
    # keep track of last two lines (to avoid false positives when identifying new course)
    prev_prev_line = ""
    prev_line = ""
    current_course = None

    fname = "bethany_college_course_catalog.txt"
    with open(fname) as fp:
        lines = fp.read().splitlines()

    for i, line in enumerate(lines):
        line = line.replace(u'\xa0', u' ')#.strip()
        line = line.strip()
        if 0 == len(line):
            # empty line or maybe end of current course
            found_new_course = False
            continue
        else:
            # look for new course
            new_course = PATTERN_REGEX_NEW_COURSE.findall(line)
            new_non_credit_course = PATTERN_ALT_REGEX_NEW_COURSE.findall(line)
            if len(new_course) > 0:
                # create new course
                course = Course()
                course.set_dept_code(new_course[0][0])
                course.set_course_num(new_course[0][1])
                course.set_name(new_course[0][2])
                course.set_credit_hours(new_course[0][3])
                current_course = course
                found_new_course = True
                
                Courses.append(course)
            elif len(new_non_credit_course) > 0:
                # create new course
                course = Course()
                course.set_dept_code(new_non_credit_course[0][0])
                course.set_course_num(new_non_credit_course[0][1])
                course.set_name(new_non_credit_course[0][2])
                course.set_credit_hours("0")
                current_course = course
                found_new_course = True
                
                Courses.append(course)
            else:
                # irrelevant line or update fields within the current course
                if current_course and found_new_course:
                    # non-empty line, please assume everything is related to course description
                    current_course.check_and_update_offerings_description_lines(line)

    # now iterate through all courses , and normalize all course
    # descriptions by extracting Prerequisites, Notes, Offerings, Recommendations, Lecture/Labs, 
    for course in Courses:
        val = course.PATTERN_REGEX_PREREQUISITE.findall(course.description)
        if len(val) > 0:
            course.prerequisites = val[0]
        val = course.PATTERN_REGEX_COREQUISITE.findall(course.description)
        if len(val) > 0:
            course.corequisites = val[0][0]
        val = course.PATTERN_REGEX_NOTES.findall(course.description)
        if len(val) > 0:
            course.notes = val[0]


# In[6]:


if __name__== "__main__":
    main()
    dump_output(Courses, "data/bethany_college_raw.csv")


# In[ ]:


run_sample_test(-1, -1)


# In[ ]:


import re
REGEX_NEW_COURSE = r"^([A-Z]{4})\s+(\d+\-*\d+)\s+(.*)\s(\d+\-*\s*\d*)\scredits*$"
PATTERN_REGEX_NEW_COURSE = re.compile(REGEX_NEW_COURSE) #, re.IGNORECASE)
line = "BIOL 487-488 Independent Study 2-4 credits"
new_course = PATTERN_REGEX_NEW_COURSE.findall(line)
dept_code = new_course[0][0]
code = new_course[0][1]
name = new_course[0][2]
credit_hours = new_course[0][3]


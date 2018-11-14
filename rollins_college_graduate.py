#!/usr/bin/env python
# coding: utf-8

# MIT License
# 
# Copyright (c) 2018 Riya Dulepet <riyadulepet123@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Thanks to the entire Columbia INCITE team for suggestions/recommendations, collaboration, critic, advice, and mentoring. This code was generated as part of internship @INCITE Columbia for Lit Index project.

# # Scraper for Rollins College Course Description

# ## Setup environment
# * Make sure Java is installed
# * Download [Apache Tika](http://apache.mirrors.ionfish.org/tika/tika-app-1.19.1.jar)

# ## Download Rollins College Course Descriptions
# * [Download Rollins College Undergraduate Course Description PDF](https://www.rollins.edu/evening/documents/catalogs/UndergraduateCatalog.pdf) and rename to rollins-college-UndergraduateCatalog.pdf
# * [Download Rollins College Graduate Course Description PDF](https://www.rollins.edu/evening/documents/catalogs/GraduateCatalog.pdf) and rename to rollins-college-GraduateCatalog.pdf
# 

# ## Extract Plain Text file from PDF using Apache TIKA
# * java  -jar tika-app-1.19.1.jar -t rollins-college-UndergraduateCatalog.pdf > rollins-college-UndergraduateCatalog.txt*
# * java  -jar tika-app-1.19.1.jar -t rollins-college-GraduateCatalog.pdf > rollins-college-GraduateCatalog.txt*
# 

# ### Extract manually exact name and unit ID
# [IPED website](https://nces.ed.gov/ipeds/datacenter/InstitutionList.aspx?addUnitID=acaeb1b4b0ab)
# * `UnitID`	136950
# * `Name`	Rollins College

# In[107]:


INSTITUTION_ID = '136950'
INSTITUTION_NAME = 'Rollins College'
CATALOG_YEAR = '2018' # It's the 2018-2019 academic year catalog
UNDERGRADUATE_CATALOG_URL = 'https://www.rollins.edu/evening/documents/catalogs/UndergraduateCatalog.pdf'
GRADUATE_CATALOG_URL = 'https://www.rollins.edu/evening/documents/catalogs/GraduateCatalog.pdf'


# ### Rules of extraction (for each department)
# * Sequence is important
# * Line starting with **COURSES** - Indicates start of course descriptions
# * Line starting with **FACULTY** - Indicates end of course descriptions
# * Department name is line that contains case-sensitive, for example ACCOUNTING (ACC) or ART HISTORY (ART) on its own
# 
# ### Rules of Extraction (for each course)
# * Sequence is important
# * Line containing **Semester Hour(s)** at the end should be treated as new course
# * Ignore all empty lines
# * Example line in the format "WLE 101 Introduction to Outdoor Education 4 Semester Hours" is start of a new course
# * It should be broken into `Course Code` (alphanumeric), `Course Title` (string could be multiple words), `Credit Hours` (floating point number with decimal) **Credit Hours**
# * The next non-empty line should be treated as `Course Description` (some paragraph/multiple lines of text, should be combined into one line)
# * The `Course Description` can be used to parse out optionally, `Offerings`, `Prerequisites`, `Lessons`, `Labs`, and `Notes`
# 
# 
# ## Solution Architecture
# #### To extract desired Course Descriptions, we define primarily two classes:
# * `Department`
# * `Course`
# #### In addition:
# * `Department` is a container for number of `Course`(s)
# * `Departments` is a `list/collection` of `Department`
# #### Processing Methodology implements the Rules described earlier for parsing each `Department` and each `Course' within it

# In[147]:


import re
# constants
# added manually following departments since it doesn't exist in catalog but courses still exist
MAP_GRADUATE_DEPARTMENTS = {"BACS":"Applied Behavior Analysis And Clinical Science",                             "CPY":"Clinical Mental Health Counseling",                             "PSY":"Clinical Mental Health Counseling",                             "EDU":"Education", "EED": "Elementary Education",                             "RED":"Reading in Elementary Education",                             "MHR":"Human Resource Management",                             "MLS":"Liberal Studies", "MPH":"Public Health"}


REGEX_START_NEXT_DEPARTMENT = r'^\s*COURSE DESCRIPTIONS\s*$'
PATTERN_REGEX_START_NEXT_DEPARTMENT = re.compile(REGEX_START_NEXT_DEPARTMENT)

REGEX_END_CURRENT_DEPARTMENT = r'^\s*FACULTY\s*$'
PATTERN_REGEX_END_CURRENT_DEPARTMENT = re.compile(REGEX_END_CURRENT_DEPARTMENT, re.IGNORECASE)

REGEX_END_DEPARTMENTS = r'^\s*BOARD OF TRUSTEES\s*$'
PATTERN_REGEX_END_DEPARTMENTS = re.compile(REGEX_END_DEPARTMENTS)

REGEX_DEPARTMENT_NAME = r'^([A-Z ]+)\s*\([A-Z]+\)\s*$'
PATTERN_REGEX_DEPARTMENT_NAME = re.compile(REGEX_DEPARTMENT_NAME)


REGEX_NEW_COURSE = r'^\s*(\b[A-Z]{3,4}\b\s+\b[0-9]{3,4}[A-Z]{0,1}\b):*\s+(.*)\[(\d\-*\d*)\]\s*$'
PATTERN_REGEX_NEW_COURSE = re.compile(REGEX_NEW_COURSE)

REGEX_DOCUMENT_HEADER = r'^\s*[0-9]+\s*$'
PATTERN_REGEX_DOCUMENT_HEADER = re.compile(REGEX_DOCUMENT_HEADER)

IGNORE_DOCUMENT_HEADER_PATTERN_LINES = ['Electives']

REGEX_DEBUG = r'PSY 683: Advanced Multicultural Counseling Practicum'
PATTERN_REGEX_DEBUG = re.compile(REGEX_DEBUG)


# In[148]:


import json

class Course:
    'Common base class for all courses'
    REGEX_OFFERINGS = r'Offered\s*(.*?)\.'
    PATTERN_REGEX_OFFERINGS = re.compile(REGEX_OFFERINGS, re.IGNORECASE)

    REGEX_PREREQUISITE = r'Prerequisite[s]*:\s*(.*?)\.'
    PATTERN_REGEX_PREREQUISITE = re.compile(REGEX_PREREQUISITE, re.IGNORECASE)

    REGEX_COREQUISITE = r'Co\-*requisite[s]*:\s*(.*?)\.'
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
    
    def __init__(self, code = None, name = None, credit_hours = None):
        # initialize class
        self.code = code
        self.name = name
        self.credit_hours = credit_hours
        
        # other member variables
        self.offerings = ""
        self.description = ""
        self.prerequisites = ""
        self.corequisites = ""
        self.notes = ""

    def set_code(self, code):
        self.code = code
    
    def set_name(self, name):
        self.name = name
    
    def set_credit_hours(self, credit_hours):
        self.credit_hours = credit_hours
    
    def check_and_update_offerings_description_lines(self, line):
        self.description += " "
        self.description += line


# In[149]:


import json
class Department:
    'Common base class for all departments'

    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4, width=1)
    
    def __init__(self, institution_id = None, institution_name = None,                  catalog_year = None, url = None, name = None, num_of_courses = None):
        # initialize class
        self.institution_id = institution_id
        self.institution_name = institution_name
        self.catalog_year = catalog_year
        self.url = url
        self.department_name = name
        self.courses = []

    # make class JSON serializable
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
    def set_department_name(self, department_name):
        self.department_name = MAP_GRADUATE_DEPARTMENTS[department_name]

    def add_course(self, course):
        self.courses.append(course)
        
    def display_institution_id(self):
        print ("Institution ID: %s" % self.institution_id)
        
    def display_institution_name(self):
        print ("Institution Name: %s" % self.institution_name)
        
    def display_department_name(self):
        print ("Department Name: %s" % self.department_name)

    def display_number_of_courses(self):
        print ("Number of Courses: %d" % len(self.courses))


# In[150]:


import pandas as pd
      
def dump_output(departments, file_to_save):
    df_college = pd.DataFrame(columns=['ipeds_id', 'ipeds_name', 'catalog_year', 'url',                                        'subject', 'subject_code', 'course_number', 'description',                                        'course_name', 'credits', 'prereqs', 'corequisites_raw',                                        'offerings_raw', 'notes_raw'])
    for department in departments:
        for course in department.courses:
            # handle only records with course description, otherwise ignore
            if course.description.strip():
                df_college.loc[len(df_college)] = [department.institution_id, department.institution_name,                                                    department.catalog_year, department.url,                                                    department.department_name.strip(),                                                    re.compile(r'^([A-Za-z]+)(.*)$').findall(course.code)[0][0],                                                    re.compile(r'^([A-Za-z]+)(.*)$').findall(course.code)[0][1],                                                    course.description.strip(), course.name.strip(),                                                    str(course.credit_hours),                                                    course.prerequisites.strip(), course.corequisites.strip(),                                                    course.offerings.strip(),                                                    course.notes.strip()]
    df_college.to_csv(file_to_save, index=False)


# In[166]:


import re, random
Departments = []
all_departments_found = []

def main():
    global INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, CATALOG_URL
    global Departments 
    
    found_start_departments = False
    found_course = False
    # keep track of last two lines (to avoid false positives when identifying new course)
    prev_prev_line = ""
    prev_line = ""

    fname = "rollins-college-GraduateCatalog.txt"
    with open(fname) as fp:
        lines = fp.read().splitlines()

    for i, line in enumerate(lines):
        line = line.replace(u'\xa0', u' ').strip()
        
        if (0 == len(line) or PATTERN_REGEX_DOCUMENT_HEADER.search(line) or line in IGNORE_DOCUMENT_HEADER_PATTERN_LINES):
            # empty line or document header line that gets printed in text, so skip/ignore
            # keep track of last two lines
            prev_prev_line = prev_line.strip()
            prev_line = line.strip()
            continue

        if not found_start_departments and PATTERN_REGEX_START_NEXT_DEPARTMENT.search(line):
            found_start_departments = True
            found_course = False
        elif found_start_departments:
            if PATTERN_REGEX_END_DEPARTMENTS.search(line):
                # print("THIS IS THE END")
                # exit parsing we are done!
                break
            elif PATTERN_REGEX_END_CURRENT_DEPARTMENT.search(line):
                # expect next department from now on
                found_start_departments = False
                prev_prev_line = ""
                prev_line = ""
                found_course = False
            else:
                # new course
                new_course = PATTERN_REGEX_NEW_COURSE.findall(line)
                if len(new_course) > 0 and not prev_line:
                    found_course = True
                    # there at least new lines before each course
                    # so initialize fields for new course
                    # so initialize fields for new department, create new department if it doesn't exist
                    new_department = new_course[0][0].split()[0].strip()
                    if new_department not in all_departments_found:
                        department = Department(INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, UNDERGRADUATE_CATALOG_URL)
                        try:
                            department.set_department_name(new_department)
                        except:
                            print("An unexpected error occurred, line=%s, prev_line=%s, prev_prev_line=%s" % (line, prev_line, prev_prev_line))
                            raise                            
                        Departments.append(department)
                        all_departments_found.append(new_department)
                    # create new course
                    course = Course()
                    course.set_code(new_course[0][0])
                    course.set_name(new_course[0][1])
                    course.set_credit_hours(str(new_course[0][2]))

                    Departments[len(Departments)-1].courses.append(course)
                else:
                    # irrelevant line or update fields within the current course
                    if found_course and len(Departments) > 0 and len(Departments[len(Departments)-1].courses) > 0:
                        # non-empty line, please assume everything is related to course description
                        Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_offerings_description_lines(line)
        # keep track of last two lines
        prev_prev_line = prev_line.strip()
        prev_line = line.strip()

    # now iterate through all courses across all departments, and normalize all course
    # descriptions by extracting Prerequisites, Notes, Offerings, Recommendations, Lecture/Labs, 
    for department in Departments:
        for course in department.courses:
            val = course.PATTERN_REGEX_OFFERINGS.findall(course.description)
            if len(val) > 0:
                course.offerings = val[0]
            val = course.PATTERN_REGEX_PREREQUISITE.findall(course.description)
            if len(val) > 0:
                course.prerequisites = val[0]
            val = course.PATTERN_REGEX_COREQUISITE.findall(course.description)
            if len(val) > 0:
                course.corequisites = val[0]
            val = course.PATTERN_REGEX_NOTES.findall(course.description)
            if len(val) > 0:
                course.notes = val[0]


# In[167]:


# sampling test
def run_sample_test(random_department_index, random_course_index):
    if -1 == random_department_index:
        random_department_index = random.randint(0, len(Departments) - 1)
    if -1 == random_course_index:
        random_course_index = random.randint(0, len(Departments[random_department_index].courses) - 1)
    # random_department_index =  14
    # random_course_index =  32

    print("random_department_index = ", random_department_index)
    Departments[random_department_index].display_institution_id()
    Departments[random_department_index].display_institution_name()
    Departments[random_department_index].display_department_name()
    Departments[random_department_index].display_number_of_courses()
    print("random_course_index = ", random_course_index)

    #print("actual courses=",len(departments[random_department_index]["courses"]))
    print("courses length = ", len(Departments[random_department_index].courses))
    print("\tcourse name = ", Departments[random_department_index].courses[random_course_index].name)
    print("\tcourse code = ", Departments[random_department_index].courses[random_course_index].code)
    print("\tofferings = ", Departments[random_department_index].courses[random_course_index].offerings)
    print("\tcourse description = ", Departments[random_department_index].courses[random_course_index].description)
    # print(Departments[random_department_index].courses[random_course_index])
    print("\tprerequisites = ", Departments[random_department_index].courses[random_course_index].prerequisites)
    print("\tnotes = ", Departments[random_department_index].courses[random_course_index].notes)


# In[168]:


if __name__== "__main__":
    main()
    dump_output(Departments, "data/rollins_college_graduate_raw.csv")


# In[55]:


run_sample_test(-1, -1)


# In[75]:


REGEX_NEW_COURSE = r'^\s*(\b[A-Z]{3,4}\b\s+\b[0-9]{3,4}[A-Z]{0,1}\b)\s+(.*)\[(\d\-*\d*)\]\s*$'
PATTERN_REGEX_NEW_COURSE = re.compile(REGEX_NEW_COURSE)
line = "RED 599 Independent Study [3]"
PATTERN_REGEX_NEW_COURSE.findall(line)


# In[ ]:





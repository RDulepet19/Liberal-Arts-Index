
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

# # Scraper for Elmhurst College Course Description

# ## Setup environment
# * Make sure Java is installed
# * Download [Apache Tika](http://apache.mirrors.ionfish.org/tika/tika-app-1.19.1.jar)

# ## Download Elmhurst College Course Descriptions
# * [Download Elmhurst College Course Description PDF](https://www.elmhurst.edu/wp-content/uploads/2018/06/Elmhurst-College-Catalog-2018-2019.pdf)
# 
# 

# ## Extract Plain Text file from PDF using Apache TIKA
# * java -jar tika-app-1.19.1.jar -t Elmhurst-College-Catalog-2018-2019.pdf > Elmhurst-College-Catalog-2018-2019.txt
# 

# ### Extract manually exact name and unit ID
# [IPED website](https://nces.ed.gov/collegenavigator/?q=elmhurst&s=all&id=144962)
# * `UnitID`	144962
# * `Name`	Elmhurst College

# In[9]:


INSTITUTION_ID = '144962'
INSTITUTION_NAME = 'Elmhurst College'
CATALOG_YEAR = '2018' # It's the 2018-2019 academic year catalog
CATALOG_URL = 'https://www.elmhurst.edu/wp-content/uploads/2018/06/Elmhurst-College-Catalog-2018-2019.pdf'


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

# In[10]:


import numpy as np
import re
# constants
# added manually following departments to map courses
MAP_DEPARTMENTS = {"ART":"Art", "BID":"Bidisciplinary", "BIO":"Biology",                    "MTH":"Math", "BUS":"Business", "ECO":"Economics",                    "CHM":"Chemistry", "COM":"Communication", "THE":"Theatre",                    "CSD":"Communication Sciences and Disorders",                    "CS":"Computer Science and Information Systems",                    "CGE":"Computer Game and Entertainment Technology",                    "IS":"Information Systems", "EDU":"Education",                    "ELM":"Elementary Education", "EYC":"Educating Young Children",                    "SEC":"Secondary Education", "SPE":"Special Education",                    "TEL":"Teaching English Learners", "ENG":"English",                    "GEO":"Geography", "POL":"Political Science", "HIS":"History",                    "HON":"Honors", "ICS":"Intercultural Studies",                    "SOC":"Sociology", "KIN":"Kinesiology",                    "MEH":"Medical Humanities", "AME":"Music",                    "MUS":"Music", "AMA":"Applied Music",                    "AMB":"Applied Music", "AMN":"Applied Music",                    "AMC":"Applied Music", "AMD":"Applied Music",                    "AMG":"Applied Music", "AMH":"Applied Music",                    "AMJ":"Applied Music", "AMO":"Applied Music",                    "AMP":"Applied Music", "AMS":"Applied Music",                    "AMT":"Applied Music", "AMV":"Applied Music",                    "AMW":"Applied Music", "NRS":"Nursing",                    "PHL":"Philosophy", "AST":"Astronomy",                    "PHY":"Physics", "PSY":"Psychology",                    "REL":"Religious Study", "CJ":"Criminal Justice",                    "URB":"Urban Studies", "ARB":"Arabic",                    "CHN":"Chinese", "FRN":"French", "GRM":"German",                    "JPN":"Japanese", "SPN":"Spanish",                    "WL":"World Languages", "CPP":"Professional Portfolio",                    "GIS":"Geographic Information Systems", "ISG":"Information Systems",                    "IT":"Information Technology", "SCM":"Supply Chain Management",                    "MBA":"Master of Business Administration",                    "MIT":"Masters in Information Technology",                    "MDS":"Masters in Data Science", "MEC":"Early Childhood Education",                    "MTL":"Masters in Teacher Leadership", "AGS":"Geographic Information Systems",                    "MPH":"Public Health", "MOT":"Occupational Therapy",                    "HCA":"Health Care", "MPM":"Project Management", "APH":"Human Geography",                    "MAT":"Master of Arts in Teaching"}

REGEX_START_DEPARTMENTS = r'^\s*COURSE DESCRIPTIONS\s*$'
PATTERN_REGEX_START_DEPARTMENTS = re.compile(REGEX_START_DEPARTMENTS)

REGEX_END_DEPARTMENTS = r'^BOARD OF TRUSTEES\s*$'
PATTERN_REGEX_END_DEPARTMENTS = re.compile(REGEX_END_DEPARTMENTS)

REGEX_DEPARTMENT_NAME = r'^([A-Z ]+)\s*\([A-Z]+\)\s*$'
PATTERN_REGEX_DEPARTMENT_NAME = re.compile(REGEX_DEPARTMENT_NAME)


REGEX_NEW_COURSE = r"^([A-Z]+)\s+([0-9]+)\s+([A-Z][\w\s\/–\-:'’,“®&]+)"
PATTERN_REGEX_NEW_COURSE = re.compile(REGEX_NEW_COURSE) #, re.IGNORECASE)

REGEX_IGNORE_NEW_COURSE = r'[\[\]]'
PATTERN_REGEX_IGNORE_NEW_COURSE = re.compile(REGEX_IGNORE_NEW_COURSE) #, re.IGNORECASE)


REGEX_DOCUMENT_HEADER = r'^\s*[0-9]+\s*$'
PATTERN_REGEX_DOCUMENT_HEADER = re.compile(REGEX_DOCUMENT_HEADER)


# In[20]:


import json

class Course:
    'Common base class for all courses'
    REGEX_OFFERINGS = r'Offered\s*(.*?)\.'
    PATTERN_REGEX_OFFERINGS = re.compile(REGEX_OFFERINGS, re.IGNORECASE)

    REGEX_NOT_OFFERINGS = r'Not Offered\s*(.*?)\.'
    PATTERN_REGEX_NOT_OFFERINGS = re.compile(REGEX_NOT_OFFERINGS, re.IGNORECASE)
    
    REGEX_PARTIAL_COURSE_NAME = r'^.*?\)\s+[A-Z]'
    PATTERN_REGEX_PARTIAL_COURSE_NAME = re.compile(REGEX_PARTIAL_COURSE_NAME, re.IGNORECASE)
    
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
    
    def __init__(self, code = None, name = None, course_num = None, credit_hours = None):
        # initialize class
        self.code = code
        self.name = name
        self.credit_hours = "0.75"
        self.course_num = course_num
        
        # other member variables
        self.offerings = ""
        self.description = ""
        self.prerequisites = ""
        self.corequisites = ""
        self.notes = ""
        self.requirements = ""

    def set_code(self, code):
        self.code = code
    
    def set_name(self, name):
        self.name = name
        

    def set_course_num(self, course_num):
        self.course_num = course_num
    
    def set_credit_hours(self, credit_hours):
        self.credit_hours = credit_hours

    def set_offering(self, offerings):
        self.offerings = offerings
    
    def check_and_update_offerings_description_lines(self, line):
        # check if credit stuff mixed as first line in course description
        credit_hours_regex = r"^([\d]*\.*[\d]*\s*[,tor\-–\s]*[\dtor,\-–\.\s]*)\s*[course]*\s*credits*"
        credit_hours = re.findall(credit_hours_regex, line.strip())
        if line.strip() in ['.50 credit, or 14 to 17 hours weekly for 1.00 credit.',                       '.25 credit or noncredit',                      '.50 credit; part-time',                      'Non-credit; optional',                      '.25, .50 or .75 credit as needed to earn 8.50 credits',                      'Noncredit',                      '(.50 credit)']:
            self.credit_hours = line.strip()
        elif len(credit_hours) > 0:
            self.credit_hours = credit_hours[0]
        else:
            # handle case of incomplete course name that is mixed up as
            # first line in course description assuming prior course name
            # ends with space indicating partial name
            if self.name.endswith('  '):
                self.name += line
                self.name = self.name.strip()
            else:
                self.description += " "
                self.description += line


# In[21]:


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
        self.department_name = MAP_DEPARTMENTS[department_name]
        # print("\tMAP_DEPARTMENTS=", self.department_name)

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


# In[36]:


import pandas as pd
      
def dump_output(departments, file_to_save):
    df_college = pd.DataFrame(columns=['ipeds_id', 'ipeds_name', 'catalog_year', 'url',                                        'subject', 'subject_code', 'course_number', 'description',                                        'course_name', 'credits', 'prereqs', 'corequisites_raw',                                        'offerings_raw', 'notes_raw', 'requirements_raw'])
    for key, department in Departments.items():
        for course in department.courses:
            # handle only records with course description, otherwise ignore
            course.description = course.description.strip()
            if course.description and not course.description.endswith('courses chosen from:'):
                # make sure course name doesn't contain multiple subject codes
                course.name = course.name.split("(")[0].strip()
                set_potential_course_codes = set(re.findall(r'\b([A-Z][A-Z\s]*[A-Z]|[A-Z])\b', course.name))
                all_subject_codes = set(['ART', 'BID', 'BIO', 'MTH', 'BUS', 'ECO','CHM',                                          'COM', 'THE','CSD','CS','CGE','IS', 'EDU','ELM',                                          'EYC','SEC', 'SPE','TEL', 'ENG','GEO', 'POL', 'HIS',                                          'HON', 'ICS','SOC', 'KIN','MEH', 'AME','MUS', 'AMA', 'AMB',                                          'AMN','AMC', 'AMD','AMG', 'AMH','AMJ', 'AMO','AMP', 'AMS',                                          'AMT', 'AMV','AMW', 'NRS','PHL', 'AST','PHY', 'PSY',                                          'REL', 'CJ','URB', 'ARB','CHN', 'FRN', 'GRM','JPN',                                          'SPN','WL', 'CPP','GIS', 'ISG','IT', 'SCM','MBA','MIT',                                          'MDS', 'MEC','MTL', 'AGS','MPH', 'MOT','HCA', 'MPM', 'APH', 'MAT'])
                if len(set_potential_course_codes & all_subject_codes) > 0:
                    # skip to next course since it is invalid course
                    continue
                
                # skip courses that have course description less than 65 characters or
                # if the course starts with [ or (, then ignore that course
                # if (not re.search('^[\[\(]', course.description)) and (len(course.description) > 65):
                # also ignore any content in paranthesis in course.name
                df_college.loc[len(df_college)] = [department.institution_id, department.institution_name,                                                    department.catalog_year, department.url,                                                    department.department_name.strip(),                                                    course.code,                                                    course.course_num,                                                    course.description.strip(),                                                    course.name,                                                    course.credit_hours,                                                    course.prerequisites.strip(), course.corequisites.strip(),                                                    course.offerings.strip(),                                                    course.notes.strip(),                                                    course.requirements.strip()]
    df_college.to_csv(file_to_save, index=False)


# In[37]:


import re, random
Departments = {}
all_departments_found = []

def main():
    global INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, CATALOG_URL
    global Departments 
    
    found_new_course = False
    # keep track of last two lines (to avoid false positives when identifying new course)
    prev_prev_line = ""
    prev_line = ""
    current_course = None

    fname = "Elmhurst-College-Catalog-2018-2019.txt"
    #fname = "temp.txt"
    with open(fname) as fp:
        lines = fp.read().splitlines()

    for i, line in enumerate(lines):
        line = line.replace(u'\xa0', u' ')#.strip()
        if 0 == len(line):
            # empty line or maybe end of current course
            found_new_course = False
            continue
        else:
            # look for new course
            new_course = PATTERN_REGEX_NEW_COURSE.findall(line)
            if len(new_course) > 0:
                if PATTERN_REGEX_IGNORE_NEW_COURSE.search(line):
                    # ignore false positive
                    continue

                # print(new_course)
                # so initialize fields for new course
                # so initialize fields for new department, create new department if it doesn't exist
                new_department = new_course[0][0].split()[0].strip()
                # print("new_course=", new_course, "new_department=", new_department)
                if new_department not in all_departments_found:
                    department = Department(INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, CATALOG_URL)
                    try:
                        department.set_department_name(new_department)
                    except:
                        print("An unexpected error occurred, line=%s" % (line))
                        raise                            
                    Departments[new_department] = department
                    all_departments_found.append(new_department)
                # create new course
                course = Course()
                course.set_code(new_course[0][0])
                course.set_name(new_course[0][2])
                course.set_course_num(new_course[0][1])
                current_course = course
                found_new_course = True
                
                Departments[new_department].courses.append(course)
            else:
                # irrelevant line or update fields within the current course
                if current_course and found_new_course:
                    # non-empty line, please assume everything is related to course description
                    current_course.check_and_update_offerings_description_lines(line)

    # now iterate through all courses across all departments, and normalize all course
    # descriptions by extracting Prerequisites, Notes, Offerings, Recommendations, Lecture/Labs, 
    for key, department in Departments.items():
        for course in department.courses:
            offerings_regex1 = r"\.\s+([AFSWQ]\w+\s+and\s+[A-Z]\w+)\."
            offerings_regex2 = r"\.*\s+([AFSWQ]\w+)\."
            offerings_regex3 = r"\.\s+([AFSWQ]\w+\s+\w+)\."
            offerings_regex4 = r"\.\s+([AFSWQ]\w+\s+and\/or\s+[A-Z]\w+)\."
            offerings_regex5 = r"\.\s+([AFSWQ]\w+\s+or\s+[A-Z]\w+)\."
            offerings_regex6 = r"Scheduled for (.*?)\."
            requirements_regex = r"\[(.*?)\]"

            offerings_list1 = re.findall(offerings_regex1, course.description)
            offerings_list2 = re.findall(offerings_regex2, course.description)
            offerings_list3 = re.findall(offerings_regex3, course.description)
            offerings_list4 = re.findall(offerings_regex4, course.description)
            offerings_list5 = re.findall(offerings_regex5, course.description)
            offerings_list6 = re.findall(offerings_regex6, course.description)
            
            offerings_list1 = [x for x in offerings_list1 if re.search(r'alternate|years|year|available|annually|spring|fall|quarterly|semesterly|semester|quarter|summer|winter|[0-9]{4}', x, re.IGNORECASE)]
            offerings_list2 = [x for x in offerings_list2 if re.search(r'alternate|years|year|available|annually|spring|fall|quarterly|semesterly|semester|quarter|summer|winter|[0-9]{4}', x, re.IGNORECASE)]
            offerings_list3 = [x for x in offerings_list3 if re.search(r'alternate|years|year|available|annually|spring|fall|quarterly|semesterly|semester|quarter|summer|winter|[0-9]{4}', x, re.IGNORECASE)]
            offerings_list4 = [x for x in offerings_list4 if re.search(r'alternate|years|year|available|annually|spring|fall|quarterly|semesterly|semester|quarter|summer|winter|[0-9]{4}', x, re.IGNORECASE)]
            offerings_list5 = [x for x in offerings_list5 if re.search(r'alternate|years|year|available|annually|spring|fall|quarterly|semesterly|semester|quarter|summer|winter|[0-9]{4}', x, re.IGNORECASE)]
            offerings_list6 = [x for x in offerings_list6 if re.search(r'alternate|years|year|available|annually|spring|fall|quarterly|semesterly|semester|quarter|summer|winter|[0-9]{4}', x, re.IGNORECASE)]

            offerings_list = offerings_list1 + offerings_list2 + offerings_list3 + offerings_list4 + offerings_list5 + offerings_list6
            course.offerings = ', '.join(offerings_list)

            meet_requirements = re.findall(requirements_regex, course.description)
            if len(meet_requirements) > 0:
                course.requirements = meet_requirements[0]

            if not course.offerings.strip():
                val = course.PATTERN_REGEX_OFFERINGS.findall(course.description)
                if len(val) > 0:
                    course.offerings = val[0]
                val = course.PATTERN_REGEX_NOT_OFFERINGS.findall(course.description)
                if len(val) > 0:
                    course.offerings = "Not offered " + val[0]
            val = course.PATTERN_REGEX_PREREQUISITE.findall(course.description)
            if len(val) > 0:
                course.prerequisites = val[0]
            val = course.PATTERN_REGEX_COREQUISITE.findall(course.description)
            if len(val) > 0:
                course.corequisites = val[0]
            val = course.PATTERN_REGEX_NOTES.findall(course.description)
            if len(val) > 0:
                course.notes = val[0]


# In[38]:


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


# In[39]:


if __name__== "__main__":
    main()
    dump_output(Departments, "data/elmhurst_college_raw.csv")


# In[ ]:


run_sample_test(-1, -1)


# In[ ]:


x = "ENG 105 an approved statistics course and one college-level"
lst = set(re.findall(r'\b([A-Z][A-Z\s]*[A-Z]|[A-Z])\b', x))
all_subject_codes = set(['ART', 'BID', 'BIO', 'BUS', 'ECO', 'CHM', 'COM', 'THE', 'CSD', 'CGE', 'CS', 'IS', 'EDU', 'ELM', 'EYC', 'SEC', 'SPE', 'TEL', 'ENG', 'GEO', 'HIS', 'HON', 'ICS', 'KIN', 'MTH', 'MEH', 'AME', 'MUS', 'AMB', 'AMC', 'AMD', 'AMN', 'NRS', 'PHL', 'AST', 'PHY', 'POL', 'PSY', 'REL', 'SOC', 'CJ', 'URB', 'CHN', 'FRN', 'GRM', 'JPN', 'SPN', 'WL', 'CPP', 'GIS', 'ISG', 'IT', 'SCM', 'MBA', 'MIT', 'MDS', 'MEC', 'MTL', 'AGS', 'MPH', 'MOT', 'HCA', 'MPM', 'APH'])
len(lst & all_subject_codes)


# In[ ]:


MAP_DEPARTMENTS["MTH"]


# In[32]:


class xClass:
        val = -1;
        def __init__(self, val):
            self.val = val
arrXClass = {}
a = xClass(10)
b = xClass(20)
arrXClass["a"]=a
arrXClass["b"]=b


# In[33]:


print(arrXClass)


# In[35]:


a.val = 40
for key, obj in arrXClass.items():
#for obj in arrXClass:
    print(obj.val)


# In[ ]:


aa=None
if aa:
    print("fund")
else:
    print("notfund")


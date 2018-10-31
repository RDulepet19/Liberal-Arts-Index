
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

# # Scraper for United States Military Academy Course Description

# ## Setup environment
# * Make sure Java is installed
# * Download [Apache Tika](http://apache.mirrors.ionfish.org/tika/tika-app-1.19.1.jar)

# ## Download United States Military Academy Course Description
# * [Download United States Military Academy Course Description PDF](https://www.usma.edu/curriculum/SiteAssets/SitePages/Course%20Catalog/RedBook_GY2019_20160711.pdf)

# ## Extract Plain Text file from PDF using Apache TIKA
# * java  -jar tika-app-1.19.1.jar -t RedBook_GY2019_20160711.pdf > RedBook_GY2019_20160711.txt*

# ### Extract manually exact name and unit ID
# [IPED website](https://nces.ed.gov/ipeds/datacenter/InstitutionProfile.aspx?unitId=acb4b2abaeb1)
# * `UnitID`	197036
# * `Name`	United States Military Academy

# In[12]:


INSTITUTION_ID = '197036'
INSTITUTION_NAME = 'United States Military Academy'
CATALOG_YEAR = '2016' # It's the 2016-2017 academic year catalog
CATALOG_URL = 'https://www.usma.edu/curriculum/SiteAssets/SitePages/Course%20Catalog/RedBook_GY2019_20160711.pdf'


# ### Rules of extraction (for each department)
# * Sequence is important
# * Line starting with (only number) **Courses** - Use the number of courses within each department to ensure you extract all relevant course entries, this also be treated as start of new department
# * Department name is the line before number of courses, so first find the number of courses and then look for line before that
# 
# ### Rules of Extraction (for each course)
# * Sequence is important
# * Line containing **Credit Hours** should be treated as new course
# * Ignore all empty lines
# * The next non-empty line contains separated by SPACE(s)
# `Course Code` (alphanumeric), `Course Title` (string could be multiple words), `Credit Hours` (floating point number with decimal) **Credit Hours**
# * The next non-empty line should be somehow be considered part of `Credit Hours`
# * The next non-empty line prefixed by **Scope:** (numeric with hyphen)  **Offerings:**
# * The next non-empty line should be treated as `Course Description` (some paragraph/multiple lines of text, should be combined into one line)
# * The next non-empty line(s) contains optionally only (numeric with hyphen) that can be multiple optionally separated by SPACE(s) should be treated as `Offerings`, they should be combined on single line
# * It could also be alternatively special text, **No Course Offerings**, and that should be treated as `Offerings`
# * **Lessons:** (some text) **Labs:**  (some text)
# * **Special Requirements:** (some text)
# * **Prerequisite(s):** (some text, and there could be multiple subsequent lines)
# * **Corequisite(s):** (some text, and there could be multiple subsequent lines)
# * **Disqualifier(s):** (some text)
# 
# ## Solution Architecture
# #### To extract desired Course Descriptions, we define primarily two classes:
# * `Department`
# * `Course`
# #### In addition:
# * `Department` is a container for number of `Course`(s)
# * `Departments` is a `list/collection` of `Department`
# #### Processing Methodology implements the Rules described earlier for parsing each `Department` and each `Course' within it

# In[13]:


import re
# constants
REGEX_START_DEPARTMENTS = r'^PART\s+III:\s+COURSE$'
PATTERN_REGEX_START_DEPARTMENTS = re.compile(REGEX_START_DEPARTMENTS)

REGEX_END_DEPARTMENTS = r'^PART\s+IV:\s+MAJORS$'
PATTERN_REGEX_END_DEPARTMENTS = re.compile(REGEX_END_DEPARTMENTS)

REGEX_NUM_COURSES = r'^([0-9]+).*Courses'
PATTERN_REGEX_NUM_COURSES = re.compile(REGEX_NUM_COURSES)

REGEX_NEW_COURSE = r'^([A-Z0-9]+)\s+(.*)\s+(\d+\.\d+)\s+Credit Hours$'
PATTERN_REGEX_NEW_COURSE = re.compile(REGEX_NEW_COURSE)

REGEX_DOCUMENT_HEADER = r'PART\s+III:\s+COURSE\s+DESCRIPTIONS'
PATTERN_REGEX_DOCUMENT_HEADER = re.compile(REGEX_DOCUMENT_HEADER)


# In[14]:


import json

class Course:
    'Common base class for all courses'
    REGEX_SCOPE = r'^Scope:\s+([0-9\-]+)\s+Offerings:$'
    PATTERN_REGEX_SCOPE = re.compile(REGEX_SCOPE)

    REGEX_OFFERINGS = r'^([0-9\-\s]+){1,}$'
    PATTERN_REGEX_OFFERINGS = re.compile(REGEX_OFFERINGS)

    REGEX_OFFERINGS2 = r'^No Course Offerings$'
    PATTERN_REGEX_OFFERINGS2 = re.compile(REGEX_OFFERINGS2)

    REGEX_OFFERINGS3 = r'^(.*)\s+No Course Offerings$'
    PATTERN_REGEX_OFFERINGS3 = re.compile(REGEX_OFFERINGS3)

    REGEX_LESSONS_LABS = r'^Lessons:\s+(.*)\s+Labs:\s+(.*)$'
    PATTERN_REGEX_LESSONS_LABS = re.compile(REGEX_LESSONS_LABS)

    REGEX_SPECIAL_REQUIREMENTS = r'^Special\s+Requirements:\s+(.*)$'
    PATTERN_REGEX_SPECIAL_REQUIREMENTS = re.compile(REGEX_SPECIAL_REQUIREMENTS)

    REGEX_PREREQUISITE = r'^Prerequisite\(s\):\s+(.*)$'
    PATTERN_REGEX_PREREQUISITE = re.compile(REGEX_PREREQUISITE)

    REGEX_COREQUISITE = r'^Corequisite\(s\):\s+(.*)$'
    PATTERN_REGEX_COREQUISITE = re.compile(REGEX_COREQUISITE)

    REGEX_DISQUALIFIER = r'^Disqualifier\(s\):\s+(.*)$'
    PATTERN_REGEX_DISQUALIFIER = re.compile(REGEX_DISQUALIFIER)

    # make class JSON serializable
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
        
    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4, width=1)
    
    def __init__(self, code = None, name = None, credit_hours = None, extra_credit_hours = None):
        # initialize class
        self.code = code
        self.name = name
        self.credit_hours = credit_hours
        self.extra_credit_hours = extra_credit_hours
        
        # other member variables
        self.scope = ""
        self.offerings = ""
        self.description = ""
        self.lessons = ""
        self.labs = ""
        self.special_requirements = ""
        self.prerequisites = ""
        self.corequisites = ""
        self.disqualifier = ""
        
        # state machine sequence that we expect (in that order)
        self.found_scope = False
        self.found_offerings = False
        self.found_maybe_more_offerings = False
        self.found_lessons_labs = False
        self.found_special_requirements = False
        self.found_prerequisites = False
        self.found_corequisites = False
        self.found_disqualifier = False

    def set_code(self, code):
        self.code = code
    
    def set_name(self, name):
        self.name = name
    
    def set_credit_hours(self, credit_hours):
        self.credit_hours = credit_hours
    
    def set_extra_credit_hours(self, extra_credit_hours):
        self.extra_credit_hours = extra_credit_hours
    
    def is_found_scope(self):
        return self.found_scope
    
    def is_found_offerings(self):
        return self.found_offerings

    def is_found_maybe_more_offerings(self):
        return self.found_maybe_more_offerings

    def is_found_lessons_labs(self):
        return self.found_lessons_labs

    def is_found_special_requirements(self):
        return self.found_special_requirements

    def is_found_prerequisites(self):
        return self.found_prerequisites

    def is_found_corequisites(self):
        return self.found_corequisites

    def is_found_disqualifier(self):
        return self.found_disqualifier
    
    def check_and_update_special_requirement_lines(self, line):
        if not self.is_found_special_requirements():
            new_pattern = self.PATTERN_REGEX_SPECIAL_REQUIREMENTS.findall(line)
            if len(new_pattern) > 0:
                self.special_requirements += " "
                self.special_requirements += new_pattern[0]
                self.found_special_requirements = True
        else:
            # already found special_requirements before
            if not self.is_found_prerequisites() and not self.is_found_corequisites() and not self.is_found_disqualifier():
                # there is false positives to handle due to repeat print in TEXT file due to HEADER/FOOTER
                # so ignore that line
                new_pattern = self.PATTERN_REGEX_SPECIAL_REQUIREMENTS.findall(line)
                if len(new_pattern) == 0:
                    self.special_requirements += " "
                    self.special_requirements += line
    
    def check_and_update_prerequisites_lines(self, line):
        if not self.is_found_prerequisites():
            new_pattern = self.PATTERN_REGEX_PREREQUISITE.findall(line)
            if len(new_pattern) > 0:
                self.prerequisites += " "
                self.prerequisites += new_pattern[0]
                self.found_prerequisites = True
        else:
            # already found prerequisites before
            if not self.is_found_corequisites() and not self.is_found_disqualifier():
                # there is false positives to handle due to repeat print in TEXT file due to HEADER/FOOTER
                # so ignore that line
                new_pattern = self.PATTERN_REGEX_PREREQUISITE.findall(line)
                if len(new_pattern) == 0:
                    self.prerequisites += " "
                    self.prerequisites += line

    def check_and_update_corequisites_lines(self, line):
        if not self.is_found_corequisites():
            new_pattern = self.PATTERN_REGEX_COREQUISITE.findall(line)
            if len(new_pattern) > 0:
                self.corequisites += " "
                self.corequisites += new_pattern[0]
                self.found_corequisites = True
        else:
            # already found corequisites before
            if not self.is_found_disqualifier():
                # there is false positives to handle due to repeat print in TEXT file due to HEADER/FOOTER
                # so ignore that line
                new_pattern = self.PATTERN_REGEX_COREQUISITE.findall(line)
                if len(new_pattern) == 0:
                    self.corequisites += " "
                    self.corequisites += line
    
    def check_and_update_disqualifier_lines(self, line):
        if not self.is_found_disqualifier():
            new_pattern = self.PATTERN_REGEX_DISQUALIFIER.findall(line)
            if len(new_pattern) > 0:
                self.disqualifier += " "
                self.disqualifier += new_pattern[0]
                self.found_disqualifier = True
        else:
            # already found disqualifier before
            # there is false positives to handle due to repeat print in TEXT file due to HEADER/FOOTER
            # so ignore that line
            new_pattern = self.PATTERN_REGEX_DISQUALIFIER.findall(line)
            if len(new_pattern) == 0:
                self.disqualifier += " "
                self.disqualifier += line
        
    def check_and_update_offerings_description_lines(self, line):
        new_offerings = self.PATTERN_REGEX_OFFERINGS.findall(line)
        if len(new_offerings) > 0:
            self.offerings += " "
            self.offerings += new_offerings[0]
            self.found_offerings = True
            self.found_maybe_more_offerings = True
        elif not self.found_offerings:
            new_offerings = self.PATTERN_REGEX_OFFERINGS2.findall(line)
            if len(new_offerings) > 0:
                self.offerings = ""
                self.found_offerings = True
            else:
                new_offerings = self.PATTERN_REGEX_OFFERINGS3.findall(line)
                if len(new_offerings) > 0:
                    # course description is mixed up
                    self.offerings = ""
                    self.description = new_offerings[0]
                    self.found_offerings = True
                elif not self.found_offerings:
                    # assume course description
                    self.description += " "
                    self.description += line

    def check_and_update_scope_line(self, line):
        new_scope = self.PATTERN_REGEX_SCOPE.findall(line)
        if len(new_scope) > 0:
            # marker for scope and offerings and course description
            self.scope = new_scope[0]
            self.found_scope = True

    def check_and_update_lessons_labs(self, line):
        new_lessons_labs = self.PATTERN_REGEX_LESSONS_LABS.findall(line)
        if len(new_lessons_labs) > 0:
            # marker for lessons and labs
            self.lessons = new_lessons_labs[0][0]
            self.labs = new_lessons_labs[0][1]
            self.found_lessons_labs = True


# In[15]:


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
        self.num_of_courses = num_of_courses
        self.courses = []

    # make class JSON serializable
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
    def set_department_name(self, department_name):
        self.department_name = department_name
    
    def set_number_of_courses(self, num_of_courses):
        self.num_of_courses = num_of_courses

    def add_course(self, course):
        self.courses.append(course)
        
    def display_institution_id(self):
        print ("Institution ID: %s" % self.institution_id)
        
    def display_institution_name(self):
        print ("Institution Name: %s" % self.institution_name)
        
    def display_department_name(self):
        print ("Department Name: %s" % self.department_name)

    def display_number_of_courses(self):
        print ("Number of Courses: %d" % self.num_of_courses)


# In[16]:


import pandas as pd
      
def dump_output(departments, file_to_save):
    df_college = pd.DataFrame(columns=['ipeds_id', 'ipeds_name', 'catalog_year', 'url',                                        'subject', 'subject_code', 'course_number', 'description',                                        'course_name', 'credits', 'prereqs',                                        'offerings_raw', 'lessons_raw', 'labs_raw',                                        'special_requirements_raw', 'corequisites_raw',                                        'disqualifier_raw', 'extra_credit_hours_raw'
                                      ])
    for department in departments:
        for course in department.courses:
            # handle only records with course description, otherwise ignore
            if course.description.strip():
                df_college.loc[len(df_college)] = [department.institution_id, department.institution_name,                                                    department.catalog_year, department.url,                                                    department.department_name.strip(),                                                    re.compile(r'^([A-Za-z]+)(.*)$').findall(course.code)[0][0],                                                    re.compile(r'^([A-Za-z]+)(.*)$').findall(course.code)[0][1],                                                    course.description.strip(), course.name.strip(),                                                    course.credit_hours,                                                    course.prerequisites.strip(), course.offerings.strip(),                                                    course.lessons.strip(), course.labs.strip(),                                                    course.special_requirements.strip(),                                                    course.corequisites, course.disqualifier.strip(),                                                    course.extra_credit_hours.strip()]
    df_college.to_csv(file_to_save, index=False)


# In[17]:


import re, random
Departments = []

def main():
    global INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, CATALOG_URL
    global Departments 
    
    found_start_departments = False

    fname = "RedBook_GY2019_20160711.txt"
    with open(fname) as fp:
        lines = fp.read().splitlines()

    for i, line in enumerate(lines):
        line = line.replace(u'\xa0', u' ').strip()
        if (0 == len(line) or PATTERN_REGEX_DOCUMENT_HEADER.search(line)):
            # empty line or document header line that gets printed in text, so skip/ignore
            continue

        if not found_start_departments and PATTERN_REGEX_START_DEPARTMENTS.search(line):
            found_start_departments = True
        elif found_start_departments:
            contains_num_courses = PATTERN_REGEX_NUM_COURSES.findall(line)
            if len(contains_num_courses) > 0:
                # so initialize fields for new department
                department = Department(INSTITUTION_ID, INSTITUTION_NAME, CATALOG_YEAR, CATALOG_URL)
                department.set_department_name(lines[i-1].replace(u'\xa0', u' ').strip())
                department.set_number_of_courses(int(contains_num_courses[0]))
                Departments.append(department)
            elif PATTERN_REGEX_END_DEPARTMENTS.search(line):
                # exit parsing we are done!
                break
            else:
                # new course
                new_course = PATTERN_REGEX_NEW_COURSE.findall(line)
                if len(new_course) > 0:
                    # so initialize fields for new course
                    course = Course()
                    course.set_code(new_course[0][0])
                    course.set_name(new_course[0][1])
                    course.set_credit_hours(str(new_course[0][2]))
                    course.set_extra_credit_hours(lines[i+1].replace(u'\xa0', u' ').strip())

                    Departments[len(Departments)-1].courses.append(course)
                else:
                    # irrelevant line or update fields within the current course
                    if len(Departments) > 0 and len(Departments[len(Departments)-1].courses) > 0:
                        if not Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].is_found_scope():
                            # check and update if scope line
                            Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_scope_line(line)
                        elif not Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].is_found_offerings():
                            # scope already found, so either there is offerings and course description, if relevant line
                            Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_offerings_description_lines(line)
                        else:
                            # either there is more offerings or "lessons and labs"
                            if not Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].is_found_lessons_labs():
                                Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_lessons_labs(line)
                                if not Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].is_found_lessons_labs():
                                    if Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].is_found_maybe_more_offerings():
                                        # found offerings already, multiple lines of offerings, maybe
                                        Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_offerings_description_lines(line)
                            else:
                                # found scope, description, offerings, lessons & labs already, so move on to optional stuff
                                # since special requirements, prerequisites, corequisites, disqualifier can be multiline
                                # until a new course/department/end of departments go reverse sequence order
                                # and add the line without any indicator to the last possible type
                                # disqualifier appears last, followed by corequisites, then prerequisites, and then special requirements

                                # check for disqualifier
                                Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_disqualifier_lines(line)
                                # check for corequisites
                                Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_corequisites_lines(line)
                                # check for prerequisites
                                Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_prerequisites_lines(line)
                                # check for special requirements
                                Departments[len(Departments)-1].courses[len(Departments[len(Departments)-1].courses)-1].check_and_update_special_requirement_lines(line)


# In[18]:


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
    print("\tscope = ",Departments[random_department_index].courses[random_course_index].scope)
    print("\tlessons = ", Departments[random_department_index].courses[random_course_index].lessons)
    print("\tlabs = ", Departments[random_department_index].courses[random_course_index].labs)
    print("\tofferings = ", Departments[random_department_index].courses[random_course_index].offerings)
    print("\tcredit hours = ", Departments[random_department_index].courses[random_course_index].credit_hours)
    print("\textra credit hours = ", Departments[random_department_index].courses[random_course_index].extra_credit_hours)
    print("\tcourse description = ", Departments[random_department_index].courses[random_course_index].description)
    # print(Departments[random_department_index].courses[random_course_index])
    print("\tspecial requirements = ", Departments[random_department_index].courses[random_course_index].special_requirements)
    print("\tprerequisites = ", Departments[random_department_index].courses[random_course_index].prerequisites)
    print("\tcorequisites = ", Departments[random_department_index].courses[random_course_index].corequisites)
    print("\tdisqualifier = ", Departments[random_department_index].courses[random_course_index].disqualifier)


# In[19]:


if __name__== "__main__":
    main()
    dump_output(Departments, "data/united_states_military_academy_raw.csv")


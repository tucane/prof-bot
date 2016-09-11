import requests
import re
import pprint
import json
import prof_setup
import os

AUTH_KEY = 'f10PmtguE4iXA3dpz3mfqsTxZdVCwMXt'
class Course_extractor():

    def __init__(self, code):
        self.code = code

    def get_full_code(arg):
        #since user won't specify the exact course code, we need to check for all possibilities
        #ie if the arg is CSC108 Fall, the possible course code might be CSC108H1F, CSC108Y1F, CSC108H2F etc.
        possible_code = []
        try:
            #user should specify term
            course_code, term = arg.split()
        except:
            return None

        term_code = ""
        credit_code = ""
        if term.lower() == "fall":
            term_code = "F"
            credit_code = "H"
        elif term.lower() == "winter":
            term_code = "S"
            credit_code = "H"
        elif term.lower() == "year":
            term_code = ""
            credit_code = "Y"

        campus_code_list = ["1", "3", "5"]          #1: st.george, 3: scarborough, 5:mississauga
        for campus_code in campus_code_list:
            full_code = course_code + credit_code + campus_code + term_code
            possible_code.append(full_code)
        return possible_code

    #Get info from the data repo
    def load_old_data(code):
        for file in os.listdir("data"):
            if Course_extractor.is_json_file(file):
                if file[:9] == code:
                    return Course_extractor.read_course_file("data/" + file)
        return None

    def read_course_file(file_path):
        file = open(file_path, "r")
        return json.load(file)

    #check if the file name ends with .json
    def is_json_file(name):
        return not re.match("(.*)\.json", name) is None

    def get_prof_set_given_sections(sections):
        prof_set = set()
        for section in sections:
            prof_list = section['instructors']
            for prof in prof_list:
                prof_set.add(prof)
        return prof_set

    def get_prof_set_from_api(json_data):
        if json_data == [] or json_data is None:
            return None
        sections = json_data[0]['meeting_sections']
        return Course_extractor.get_prof_set_given_sections(sections)

    def get_prof_set_from_dataset(json_data):
        if json_data == {} or json_data is None:
            return None
        sections = json_data['meeting_sections']
        return Course_extractor.get_prof_set_given_sections(sections)


    def get_comment_with_code_list(code_list):
        found = False                   #flag for if any campus has this course
        comment = ""
        for code in code_list:
            url = 'https://cobalt.qas.im/api/1.0/courses/search?q="{}"'.format(code)
            r = requests.get(url, headers={'Authorization': AUTH_KEY})
            content = r.content.decode("utf-8")
            prof_set = set()            #a set of profs teaching this course
            try:
                json_data = json.loads(content)
                prof_set = Course_extractor.get_prof_set_from_api(json_data)
            except:     #if the given api is down, we get the info from the data repo
                json_data = Course_extractor.load_old_data(code)
                prof_set = Course_extractor.get_prof_set_from_dataset(json_data)

            if prof_set is None or len(prof_set) == 0:
                continue
            found = True                  #if this course exists across the three campuses
            comment += code + "\n\n"
            data_extract = prof_setup.Data_Extractor()
            data_extract.setup()

            #we only want to print the same prof once
            for prof in prof_set:
                comment += (data_extract.search_prof(prof)) + "\n\n"
                comment += "--------------------------------\n\n"
        if not found:
            comment = ""
        return comment

    def get_comment(self):
        code_list = Course_extractor.get_full_code(self.code)
        return Course_extractor.get_comment_with_code_list(code_list)

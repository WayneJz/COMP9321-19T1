'''
COMP9321 Assignment One Code Template 2019T1
Name:Zhou JIANG
Student ID:z5146092
'''

import csv
import re
import json
import matplotlib.pyplot as plot


def format_words(element):
    ignore_words = {"la", "de"}
    ignore_initials = {"d'", "l'"}
    cleansed_element = list()
    for words in element.split():
        if words in ignore_words or words[:2] in ignore_initials:
            cleansed_element.append(words)
        else:
            cleansed_element.append(words.title())
    element = ' '.join(cleansed_element)
    element = element.rstrip()
    if re.findall("\s", element):
        element = "\"" + element + "\""
    element = element + " "
    return element


def q1():
    with open('accidents_2017.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        line = 0
        for row in reader:
            if line >= 10:
                break
            temp = list()
            for element in row:
                element = format_words(element)
                temp.append(element)
            print((''.join(temp)).rstrip())
            line += 1


def q2():
    origin_file = open('accidents_2017.csv', 'r', encoding='utf-8')
    cleansed_file = open('result_q2.csv', 'w', newline='', encoding='utf-8')
    reader = csv.reader(origin_file)
    writer = csv.writer(cleansed_file)
    for row in reader:
        for element in row:
            if re.findall("Unknown", element, flags=re.I):
                break
        else:
            writer.writerow(row)
    origin_file.close()
    cleansed_file.close()


def q3():
    accident_dict = dict()
    with open('result_q2.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if re.match('District Name', row[1]):
                continue
            if row[1] not in accident_dict.keys():
                accident_dict[row[1]] = 1
            else:
                accident_dict[row[1]] += 1

    print((format_words("District Name") + format_words("Total numbers of accidents")).rstrip())
    for element in sorted(accident_dict.items(), key=lambda x: x[1], reverse=True):
        print(format_words(element[0]) + str(element[1]))


def q4():
    air_quality_list = list()
    with open('air_stations_Nov2017.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if re.match('District Name', row[4]):
                continue
            air_quality_dict = dict()
            air_quality_dict['Station'] = row[0] + ' - ' + row[5]
            air_quality_dict['District Name'] = row[4]
            air_quality_list.append(air_quality_dict)
    print(json.dumps(air_quality_list))

    origin_file = open('air_quality_Nov2017.csv', 'r', encoding='utf-8')
    cleansed_file = open('result_q4.csv', 'w', newline='', encoding='utf-8')
    reader = csv.reader(origin_file)
    writer = csv.writer(cleansed_file)
    not_good_count = 0
    for row in reader:
        if re.match("Good", row[1], flags=re.I) or not re.findall("\w+", row[1]):
            continue
        else:
            writer.writerow(row)
            if not_good_count <= 10:
                temp = list()
                for element in row:
                    element = format_words(element)
                    temp.append(element)
                print((''.join(temp)).rstrip())
                not_good_count += 1

    origin_file.close()
    cleansed_file.close()


def q5():
    '''
    Bonus Question(Optional).
    Put Your Question 5's code in this function.
    '''
    pass 


q1()
q2()
q3()
q4()
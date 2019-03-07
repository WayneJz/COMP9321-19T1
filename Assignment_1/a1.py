'''
COMP9321 Assignment One Code Template 2019T1
Name:Zhou JIANG
Student ID:z5146092
'''

import csv
import re
import json
import os
import matplotlib.pyplot as plot
import numpy as np
import utm


def format_words(element, flag='ALL'):
    ignore_words = {"la", "de"}
    ignore_initials = {"d'", "l'"}
    cleansed_element = list()
    for words in element.split():
        if words in ignore_words or words[:2] in ignore_initials or flag != 'ALL':
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
        format_flag = 'I'
        for row in reader:
            if line >= 10:
                break
            temp = list()
            for element in row:
                element = format_words(element, flag=format_flag)
                temp.append(element)
            print((''.join(temp)).rstrip())
            format_flag = 'ALL'
            line += 1


def q2():
    id_list = list()
    origin_file = open('accidents_2017.csv', 'r', encoding='utf-8')
    cleansed_file = open('result_q2.csv', 'w', newline='', encoding='utf-8')
    reader = csv.reader(origin_file)
    writer = csv.writer(cleansed_file)
    for row in reader:
        if row[0] in id_list:
            continue
        id_list.append(row[0])
        for element in row:
            if re.findall("Unknown", element, flags=re.I):
                break
        else:
            writer.writerow(row)
    origin_file.close()
    cleansed_file.close()


def q3():
    accident_dict = dict()
    if not os.path.exists("result_q2.csv"):
        q2()
    with open('result_q2.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if re.match('District Name', row[1]):
                continue
            if row[1] not in accident_dict.keys():
                accident_dict[row[1]] = 1
            else:
                accident_dict[row[1]] += 1

    print((format_words("District Name") + format_words("Total numbers of accidents", flag='I')).rstrip())
    for element in sorted(accident_dict.items(), key=lambda x: x[1], reverse=True):
        print(format_words(element[0]) + str(element[1]))


def date_split(word):
    convert_month = {'01': 'January', '02': 'February', '03': 'March', '04': 'April',
                     '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                     '09': 'September', '10': 'October', '11': 'November', '12': 'December'}

    search_case = re.search("(\d+)/(\d+)/\d+\s+(\d+):\d+", word)
    return int(search_case.group(1)), convert_month[search_case.group(2)], int(search_case.group(3))


def q4():
    air_stations_list = list()
    station_district_dict = dict()
    with open('air_stations_Nov2017.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if re.match('District Name', row[4]):
                continue
            station_district_dict[row[0]] = row[4]
            air_stations_dict = dict()
            air_stations_dict['Station'] = row[0] + ' - ' + row[5]
            air_stations_dict['District Name'] = row[4]
            air_stations_list.append(air_stations_dict)
    print(json.dumps(air_stations_list))

    air_quality_file = open('air_quality_Nov2017.csv', 'r', encoding='utf-8')
    air_quality_reader = csv.reader(open('air_quality_Nov2017.csv', 'r', encoding='utf-8'))
    not_good_count = 0
    not_good_list = list()
    for row in air_quality_reader:
        if re.match("Good", row[1], flags=re.I) or not re.findall("\w+", row[1]):
            continue
        else:
            if row[0] in station_district_dict.keys():
                day, month, hour = date_split(row[13])
                not_good_list.append([station_district_dict[row[0]], day, month, hour])
            if not_good_count <= 10:
                temp = list()
                for element in row:
                    element = format_words(element)
                    temp.append(element)
                print((''.join(temp)).rstrip())
                not_good_count += 1

    air_quality_file.close()

    accident_file = open('accidents_2017.csv', 'r', encoding='utf-8')
    accident_reader = csv.reader(accident_file)
    accident_air_file = open('result_q4.csv', 'w', newline='', encoding='utf-8')
    accident_air_writer = csv.writer(accident_air_file)
    for row in accident_reader:
        if re.match('District Name', row[1]) or [row[1], int(row[6]), row[5], int(row[7])] in not_good_list:
            accident_air_writer.writerow(row)

    accident_file.close()
    accident_air_file.close()


def q5():
    from PIL import Image
    points = list()
    with open('accidents_2017.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if re.match('Longitude', row[13]):
                continue
            points.append([utm.from_latlon(float(row[14]), float(row[13]))[0],
                           utm.from_latlon(float(row[14]), float(row[13]))[1]])
            # points.append([float(row[14]), float(row[13])])
    print(points)
    x_coordinates = [x[0] for x in points]
    y_coordinates = [y[0] for y in points]

    plot.hist2d(x_coordinates, y_coordinates, bins=100)
    plot.colorbar()

    plot.show()


q1()
q2()
q3()
q4()
q5()
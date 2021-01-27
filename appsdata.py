#!/usr/bin/env python
###################################################################################
#                           Written by Wei, Hang                                  #
#                          weihang_hank@gmail.com                                 #
###################################################################################
"""
This module has the functions to retrieve all the apps data from AppDynamics Controller
"""
import os
import csv
import copy
import tkinter as tk
import tkinter.messagebox
import requests
import json
import base64
from credentials import *

URL_APP = APPD_URL + "/controller/rest/applications"


def readfile(filename):
    """
    This function is to read the file at current directory and convert it to python data
    """
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename)) as file:
        json_text = file.read()

    return json.loads(json_text)


def writefile(filename, dict):
    """
    This function is to write the python dict at current directory and convert it to JSON format file
    """
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename), mode="w") as file:
        file.write(json.dumps(dict, indent=4))


def writecsv(filename, dict):
    """
    This function is to write the python dict at current directory and convert it to CSV format file
    """
    header_list = ["No."]
    for header in dict["1"]:
        header_list.append(header)

    with open(filename, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile, dialect='excel')
        # write the table header
        writer.writerow(header_list)

        # write table row by row, each row is a list
        for seq, item_body in dict.items():
            row = copy.deepcopy(header_list)
            row[0] = seq
            for k, v in item_body.items():
                if k == "Source App/Tier" or k == "Destination App/Tier":
                    AppTier = ""
                    for sub_value in v:
                        AppTier = AppTier + "{}/{}\n".format(sub_value[0], sub_value[1])
                    row[row.index(k)] = AppTier
                else:
                    row[row.index(k)] = v

            writer.writerow(row)
    # csvFile.close()


def get_basic_auth_str(username, password):
    """
    It's the same thing that what requests' HTTPBasicAuth does to a header Authentication
    """
    temp_str = username + ':' + password
    # convert to bytes string
    bytesString = temp_str.encode(encoding="utf-8")
    # base64 encoding
    encodestr = base64.b64encode(bytesString)

    return 'Basic ' + encodestr.decode()


def Query(url, header):
    """
    This function uses GET method to fetch AppD data from specific url and header
    """
    payload = {}
    _url = URL_APP + url
    return requests.request("GET", _url, headers=header, data=payload)
    # return requests.request("GET", URL_TMP, headers=header, data=payload)


def get_appsdict(dynamic):
    """
    This function is used to get full application information from a running AppD or a static local JSON file.
    """
    if dynamic:  # get full application information from a running AppD
        appsdict = {}
        header = {}
        header['Authorization'] = get_basic_auth_str(APPD_LOGIN, APPD_PASS)
        apps = json.loads(Query("?output=JSON", header).text)
        for app in apps:
            appdict = {}
            application = app["name"]
            tiers = json.loads(Query("/" + application + "/tiers?output=JSON", header).text)
            for tier in tiers:
                nodes = json.loads(
                    Query("/" + application + "/tiers/" + tier["name"] + "/nodes?output=JSON", header).text)
                nodelist = []
                for node in nodes:
                    addresslist = node["ipAddresses"]["ipAddresses"]
                    nodelist.append(addresslist[len(addresslist) - 1])
                appdict[tier["name"]] = nodelist
            appsdict[app["name"]] = appdict

        if not appsdict:
            tk.messagebox.showerror(title="Error",
                                    message="Applications do not exist!")
            exit(1)
        else:
            # manually add any app/tier/node_ip here, e.g. those DBs without any AppD agent resides
            appsdict["courseback"]["XIAOZEDB-MySQL-172.16.1.52-5.7.28"] = ["172.16.1.52"]
            appsdict["courseback"]["Internal_DNS"] = ["172.16.2.222"]

    else:  # get full application information from a static local JSON file
        try:
            appsdict = readfile("apps.json")
        except:
            tk.messagebox.showerror(title="Data Fetching Error",
                                    message="Can't find Application Description File locally.")

    return appsdict


def main():
    """
    This main function is just for test.
    """
    print('get_appsdict():\n', get_appsdict(True))
    # print('get_rs(application):\n',get_rs(application))


if __name__ == '__main__':
    main()

#!/usr/bin/env python
###################################################################################
#                           Written by Wei, Hang                                  #
#                          weihang_hank@gmail.com                                 #
###################################################################################
"""
This application directly maps anomalies found by NI to specific Applications, Tiers and Nodes
"""
import os
import requests
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
from my_py.anom2apps.credentials import *
from my_py.anom2apps.appsdata import *

DYNAMIC = False  # use AppDynamics or not, if not, use local JSON file
APPSDICT = get_appsdict(DYNAMIC)  # appsdict is all data we can fetch from AppD during this query


def NI_login():
    """
    Login to NI and return response
    """
    login_url = NI_URL + "/login"

    payload = '{\r\n  \"userName\": \"' + LOGIN + '\",\r\n  \"userPasswd\": \"' + PASSWORD + '\",\r\n  \"domain\": \"DefaultAuth\"\r\n}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.request("POST", login_url, headers=headers, data=payload)
        response.raise_for_status()

    except requests.exceptions.ConnectionError as err1:
        tk.messagebox.showerror(title="Connection Failed", message=err1)
    except requests.HTTPError as err2:
        tk.messagebox.showerror(title="Data Fetching Error", message=err2)

    return response


def NI_Query(url, params):
    """
    Fetch data from NI
    """
    query_url = NI_URL + "/sedgeapi/v1/cisco-nir/api/api/telemetry" + url + params

    payload = {}
    headers = {}

    try:
        response = requests.request("GET", query_url, headers=headers, data=payload)
        response.raise_for_status()

    except requests.exceptions.ConnectionError as err1:
        tk.messagebox.showerror(title="Connection Failed", message=err1)
    except requests.HTTPError as err2:
        tk.messagebox.showerror(title="Data Fetching Error", message=err2)

    return response


def get_apps_info(ip_address):
    """
    This function return all the possible apps and tiers that match the ip addresses.
    Note that since we can't get connections information from AppD (API not opened),
    all the possible apps and tiers may be returned regardless of the protocol, port
    or relationship.
    """
    # TODO: add protocol, port and relationship criteria
    # Parse JSON file
    app_tier_list = []
    for app, tiers in APPSDICT.items():
        for tier, ips in tiers.items():
            if ip_address in ips:
                app_tier_list.append([app, tier])

    return app_tier_list


def do_anom2apps(time_range, anomaly, category, topn):
    """
    This function maps anomalies found by NI to specific Applications, Tiers and Nodes.
    """
    output_dict = {}  # this is the final output for this tool
    if anomaly == "Flows":
        if category == "Top Packet Drop":
            # ni_dict is all data we can fetch from NI during this query
            # NI_login()
            # ni_dict = json.loads(NI_Query("/flows/topFlows.json", "?statName=flow:pktdrop&count=" + topn).text)
            ni_dict = readfile("ni.json")  # for test

            for entry in ni_dict["entries"]:  # each entry is a dict of a flow
                i = str(ni_dict["entries"].index(entry) + 1)
                output_dict[i] = {}
                output_dict[i]["Source IP"] = entry["srcIp"]
                output_dict[i]["Destination IP"] = entry["dstIp"]
                output_dict[i]["Source Port"] = entry["srcPort"]
                output_dict[i]["Destination Port"] = entry["dstPort"]
                if entry["protocolName"] == "":
                    output_dict[i]["Protocol"] = entry["protocol"]
                else:
                    output_dict[i]["Protocol"] = entry["protocolName"]
                output_dict[i]["Source App/Tier"] = get_apps_info(entry["srcIp"])
                output_dict[i]["Destination App/Tier"] = get_apps_info(entry["dstIp"])
                stats = entry["stats"][0]
                output_dict[i]["Anomalies"] = "drop {} packet(s) in {} flow record(s) during {}".format(
                    stats["dropPktCount"], stats["flowRecordCount"], time_range)
                output_dict[i]["Terminal Time"] = stats["terminalTs"]
        else:
            # TODO: Other functions
            pass

    return output_dict


def main():
    """
    This main function presents the main window for you to input data and trigger mapping behavior.
    """

    def do_ok():
        """
        This function triggered when click OK button, begin to micro-segment
        """
        if cbl_01.get() != "" and cbl_02.get() != "" and cbl_03.get() != "" and cbl_04.get() != "":
            output_dict = do_anom2apps(cbl_01.get(), cbl_02.get(), cbl_03.get(), cbl_04.get())

            if output_dict:
                writefile("output.json", output_dict)
                writecsv("output.csv", output_dict)
                tk.messagebox.showinfo('Congratulations!',
                                       "We have successfully stored the results in the output.json and output.csv file, which will be automatically opened for review.")
                os.system(r"start output.json")
                os.system(r"start EXCEL output.csv")
                exit(0)
            else:
                tk.messagebox.showinfo('Notice',
                                       "This function is not supported or we can't get any data from your network.")
        else:
            tk.messagebox.showinfo('Notice', "Please complete all the required fields")

    def do_cancel():
        """
        doing cancel
        """
        exit(0)

    def show_anom_config(event):
        """
        This function is to build anomalies config you selected
        """
        if cbl_02.get() == "Flows":
            cbl_03["values"] = ["", "Top Latency", "Top EP Move", "Top Packet Drop"]
            cbl_03.current(0)
        else:
            # TODO: Other functions
            tk.messagebox.showinfo('Notice', "This function will come soon!")
            cbl_02.current(0)
            cbl_03.current(0)
            cbl_04.current(0)

    # main function begins

    # window is the obj name
    window = tk.Tk()
    window.title('Anomalies-to-AppTiers v0.1 by Wei Hang')
    window.geometry('510x340')

    # Lables
    lb_01 = tk.Label(window, width=20, font=("Arial", 10), anchor='e', text="Time Range:")
    lb_01.place(x=25, y=50, anchor='nw')

    lb_02 = tk.Label(window, width=20, font=("Arial", 10), anchor='e', text="Anomalies:")
    lb_02.place(x=25, y=100, anchor='nw')

    lb_03 = tk.Label(window, width=20, font=("Arial", 10), anchor='e', text="Category:")
    lb_03.place(x=25, y=150, anchor='nw')

    lb_04 = tk.Label(window, width=20, font=("Arial", 10), anchor='e', text="Top N:")
    lb_04.place(x=25, y=200, anchor='nw')

    # star '*' for mandatory field
    # lb_st = tk.Label(window, width=2, fg='red', text="*")
    # lb_st.place(x=200, y=50, anchor='nw')
    #
    # lb_sp = tk.Label(window, width=2, fg='red', text="*")
    # lb_sp.place(x=200, y=100, anchor='nw')
    #
    # lb_se = tk.Label(window, width=2, fg='red', text="*")
    # lb_se.place(x=200, y=150, anchor='nw')

    # Combo Box Lists
    cbl_01 = ttk.Combobox(window, font=("Arial", 10), width=25)
    cbl_01["values"] = ["Last 15 mins", "Last 30 mins", "Last 1 Hour", "Last 3 Hours"]
    cbl_01.current(2)
    # cbl_01.bind("<<ComboboxSelected>>", show_anom_config)
    cbl_01.place(x=220, y=50, anchor='nw')

    cbl_02 = ttk.Combobox(window, font=("Arial", 10), width=25)
    cbl_02["values"] = ["", "Flows", "Statistics", "Resource", "Endpoint"]
    cbl_02.current(0)
    cbl_02.bind("<<ComboboxSelected>>", show_anom_config)
    cbl_02.place(x=220, y=100, anchor='nw')

    cbl_03 = ttk.Combobox(window, font=("Arial", 10), width=25)
    cbl_03["values"] = [""]
    cbl_03.current(0)
    # cbl_03.bind("<<ComboboxSelected>>", set_epg_list)
    cbl_03.place(x=220, y=150, anchor='nw')

    cbl_04 = ttk.Combobox(window, font=("Arial", 10), width=25)
    cbl_04["values"] = ["", "5", "10", "15", "20"]
    cbl_04.current(0)
    cbl_04.place(x=220, y=200, anchor='nw')

    # Buttons
    bt_ok = tk.Button(window, text='OK', width=15, height=2, font=("Arial", 10), command=do_ok)
    bt_ok.place(x=80, y=265, anchor='nw')

    bt_cancel = tk.Button(window, text='Cancel', width=15, height=2, font=("Arial", 10), command=do_cancel)
    bt_cancel.place(x=300, y=265, anchor='nw')

    # Window's mainloop
    window.mainloop()


if __name__ == '__main__':
    main()

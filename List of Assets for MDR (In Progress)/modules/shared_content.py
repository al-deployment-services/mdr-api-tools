#Required Libraries
import ipaddress
import json
import csv
from colorama import Fore, Back, Style
import os
import requests
import time
from datetime import datetime
import click

# Variables
true=True
false=False
auth_header = {}
query_auth_header = {}
deployments_list = []

# Variables from variables.py file in root directory
#from variables import global_url, username, password, alert_logic_cid, deployment_id, csv_file_name, specified_network_key
from testvariables import global_url, username, password, alert_logic_cid, csv_file_name, specified_network_key

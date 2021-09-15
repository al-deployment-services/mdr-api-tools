#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Required Libraries
from colorama import Fore, Back, Style
import argparse
import ipaddress
import json
import csv
import os
import re
import requests
import time
from datetime import datetime

# Permanent Variables
true=True
false=False

# Variables from variables.py file
#from variables import *
from testvariables import *

### Validate Authentication to Alert Logic API
# Function to get AIMS Token with the provided username and password
def get_api_token():
    url = f'{global_url}/aims/v1/authenticate'
    global auth_token
    global token_response
    # User credentials
    aims_user = username
    aims_pass = password
    # Ask the user for their MFA code
    mfa_code = input('Please provide your MFA code: ')
    mfa_payload = {"mfa_code": mfa_code}

    # Tidy up the payload
    mfa_payload = json.dumps(mfa_payload)
    mfa_payload=mfa_payload.replace("'",'"')

    #POST request to the URL using credentials. Load the response into auth_info then parse out the token
    token_response = requests.post(url, mfa_payload, auth=(aims_user, aims_pass))

    if token_response.status_code != 200:
        print(Fore.RED + f'Error: Could not authenticate. Got the following response: {token_response}\n' + Style.RESET_ALL)
        exit()

    auth_info = json.loads(token_response.text)
    auth_token = auth_info['authentication']['token']

# Function to validate the AIMS token was successfully generated, and that it has not expired
def validate_token():
    url = f'{global_url}/aims/v1/token_info'
    headers = {'x-aims-auth-token': f'{auth_token}'}
    global validate_info
    validate_response = requests.get(url, headers=headers)
    validate_info = json.loads(validate_response.text)

    # Get current unix timestamp,make global for later
    global current_time
    current_time = int(time.time())
    # Get token expiration timestamp
    token_expiration = validate_info['token_expiration']
    num_seconds_before_expired=(token_expiration - current_time)

    if num_seconds_before_expired < 0 :
        print(Fore.RED + ' Errror: Could not generate / validate AIMS Token. Please check credentials and try again\n' + Style.RESET_ALL)
        exit()
    else :
        print(Fore.GREEN + ' AIMS token generated and validated.\n' + Style.RESET_ALL)
        time.sleep(1)

# Run the authentication functions and check for errors
if username != '' and password != '':
    global headers
    get_api_token()
    validate_token()
    # Set header for all future API calls
    headers = {
        "x-aims-auth-token": f"{auth_token}",
        "content-type" : "application/json"
    } 
else:
    print (Fore.RED + '\nError: No credentials stored in the configuration file, to allow authentication against the API.\n' + Style.RESET_ALL)
    exit()

# Adding arguments for the script
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-add', '--add_ips_or_fqdns', help='upload the desired external IPs and FQDNs that are specified in the external-fqdns.csv and external-ips.csv files', action='store_true')
parser.add_argument('--delete_all_ips', help='delete all existing external IPs for the CID in the provided variables.py file', action='store_true')
parser.add_argument('--delete_all_fqdns', help='delete all existing external IPs for the CID in the provided variables.py file', action='store_true')
args = parser.parse_args()

# Import all External Assets
def import_external_assets():
    global external_assets_logging
    external_assets_logging=[]
    cidr_values = {
        "24": "256",
        "25": "128",
        "26": "64",
        "27": "32",
        "28": "16",
        "29": "8",
        "30": "4",
        "31": "2",
        "32": "1"
    }

    if not external_fqdns_csv: 
        print(Fore.RED + "    No FQDNs detected in a csv file. Please provide the file path to the list of FQDNs in a .csv in the properties file.\n" + Style.RESET_ALL)
    else:
        #Read from FQDNs csv file
        with open(external_fqdns_csv, newline='') as fqdn_csv_file:
            fqdns_reader = csv.reader(fqdn_csv_file)
            fqdns = list(fqdns_reader)
        
        for fqdn in fqdns:

            fqdn_payload= {
                "operation": "declare_asset",
                "type": "external-dns-name",
                "scope": "config",
                "key": "/external-dns-name/"+fqdn[0]+"",
                "properties": {
                    "name": ""+fqdn[0]+"",
                    "dns_name": ""+fqdn[0]+"",
                    "state": "new"
                }
            }

            create_fqdn_payload=json.dumps(fqdn_payload)
            create_fqdn_url = f'{global_url}/assets_write/v1/{alert_logic_cid}/deployments/{deployment_id}/assets'
            create_fqdn_response = requests.put(create_fqdn_url, create_fqdn_payload, headers=headers)

            if create_fqdn_response.status_code != 201:
                if create_fqdn_response.status_code == 304:
                    print(Fore.YELLOW + f'    Warning: FQDN with name {fqdn} was previously added.')
                else:
                    print(Fore.RED + f'    Error: FQDN with name {fqdn} was unable to be added. Got the following response: ' + Style.RESET_ALL)
                    print(create_fqdn_response)
            else:
                print(Fore.GREEN + f'    FQDN with name {fqdn} added successfully.' + Style.RESET_ALL)

    if not external_ips_csv:
                print(Fore.MAGENTA + '    No external IP addresses to add' + Style.RESET_ALL)
    else:
        #Read from IPs csv file
        with open(external_ips_csv, newline='') as ips_csv_file:
            ips_reader = csv.reader(ips_csv_file)
            ip_entries = list(ips_reader)
        for entry in ip_entries:
            try:
                cidr_check = entry[0].split("/")
            except Exception as e:
                print(Fore.RED + f'    Error: Encountered the following \'{e}\'. Please make sure each row is not populated with blank space.' + Style.RESET_ALL)
                cidr_check = ''
            
            def ip_upload(ip):
                ip_payload= {
                        "operation": "declare_asset",
                        "type": "external-ip",
                        "scope": "config",
                        "key": "/external-ip/"+ip+"",
                        "properties": {
                            "name": ""+ip+"",
                            "ip_address": ""+ip+"",
                            "state": "new"
                        }
                    }

                create_ip_payload=json.dumps(ip_payload)
                create_ip_url = f'{global_url}/assets_write/v1/{alert_logic_cid}/deployments/{deployment_id}/assets'
                create_ip_response = requests.put(create_ip_url, create_ip_payload, headers=headers)

                #This is kicking off when the except below fires for 304s. Need to fix that. (This still valid? RAV - 9-14-21)
                if create_ip_response.status_code != 201:
                    if create_ip_response.status_code == 304:
                        print(Fore.YELLOW + f'    Warning: IP address {ip} was previously added.')
                    else:
                        print(Fore.RED + f'    Error: IP address {ip} was unable to be added. Got the following response: ' + Style.RESET_ALL)
                        print(create_ip_response)
                else :
                    print(Fore.GREEN + f'    IP address {ip} added successfully.' + Style.RESET_ALL)

            if cidr_check == '':
                continue
            elif  len(cidr_check) == 1:
                try: 
                    ip_validation = ipaddress.ip_address(entry[0])
                    ip = entry[0]
                    ip_upload(ip)

                except ValueError:
                    print(Fore.RED + f'    Error: This is not a valid IP address or CIDR range: {entry[0]}' + Style.RESET_ALL)
                    continue
            
            elif len(cidr_check) == 2:
                network_range_start = cidr_check[0]
                network_range_list = network_range_start.split(".")
                fourth_octet = network_range_list.pop()

                cidr_range = cidr_check[1]
                possible_cidrs = list(cidr_values.keys())
                if cidr_range in possible_cidrs:
                    cidr_value = cidr_values[cidr_range]
                    try:
                        ip_validation = ipaddress.ip_address(cidr_check[0])
                        for i in range(int(cidr_value)):
                            increment = int(fourth_octet) + i
                            network_range_list.append(str(increment))
                            ip_address = '.'.join(network_range_list)
                            ip = ip_address
                            network_range_list.pop()

                            ip_upload(ip)

                    except ValueError:
                        print(Fore.RED + f'    Error: The IP in CIDR range: {cidr_check[0]} is not valid.' + Style.RESET_ALL)
                else:
                    print(Fore.RED + f'    Error: CIDR range entries support '"'/24'"' - '"'/32'"'' + f" You provided '/{cidr_range}'" + Style.RESET_ALL)

            else:
                print(Fore.RED + f'    Error: IP list {entry[0]} was in an incorrect format. Please use either 10.10.10.1 or 10.10.10.0/28 per line. CIDR range entries support '"'/24'"' - '"'/32'"'' + Style.RESET_ALL)

    print(Fore.GREEN + f'\nCompleted upload of entries in both files: {external_fqdns_csv} and {external_ips_csv}' + Style.RESET_ALL)

def delete_all_external_ips():
# https://api.cloudinsight.alertlogic.com/assets_query/v1/134234902/deployments/02610749-8C2B-4578-BD82-054225AE278D/assets?asset_types=external-ip
    # Grab a list of all external IPs to iterate throguh and delete
    get_ips_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=external-ip'
    get_ips_request = requests.get(get_ips_url, headers=headers)
    global delete_ips_list 
    delete_ips_list = []

    if get_ips_request.status_code != 200:
        print(Fore.RED + f'Error: Could not query for orphaned hosts. Got the following response: {get_ips_request}\n' + Style.RESET_ALL)
        exit()
    else:
        current_external__ips = json.loads(get_ips_request.text)
        current_external__ips = current_external__ips['assets']
        for current_ip_info in current_external__ips:
            current_ip_key = current_ip_info[0]['key']
            delete_ips_list.append(current_ip_key)

        for key in delete_ips_list:
            key_payload= {
                    "key": ""+key+"",
                    "operation": "remove_asset",
                    "type":"external-ip",
                    "scope":"config",
                }

            delete_key_payload=json.dumps(key_payload)
            # https://api.cloudinsight.alertlogic.com/assets_write/v1/134234902/deployments/02610749-8C2B-4578-BD82-054225AE278D/assets
            delete_ip_url = f'{global_url}/assets_write/v1/{alert_logic_cid}/deployments/{deployment_id}/assets'
            delete_ip_response = requests.put(delete_ip_url, delete_key_payload, headers=headers)

            if delete_ip_response.status_code != 204:
                print(Fore.RED + f'    Error: IP address with key: {key} was unable to be deleted. Got the following response: ' + Style.RESET_ALL)
                print(delete_ip_response)
            else :
                print(Fore.GREEN + f'    IP address with key: {key} deleted successfully.' + Style.RESET_ALL)

def delete_all_external_fqdns():
# https://api.cloudinsight.alertlogic.com/assets_query/v1/134234902/deployments/02610749-8C2B-4578-BD82-054225AE278D/assets?asset_types=external-dns-name
    # Grab a list of all external FQDNs to iterate throguh and delete
    get_fqdns_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=external-dns-name'
    get_fqdns_request = requests.get(get_fqdns_url, headers=headers)
    global delete_fqdns_list 
    delete_fqdns_list = []

    if get_fqdns_request.status_code != 200:
        print(Fore.RED + f'Error: Could not query for orphaned hosts. Got the following response: {get_fqdns_request}\n' + Style.RESET_ALL)
        exit()
    else:
        #print(get_fqdns_request.text)
        current_external__fqdns = json.loads(get_fqdns_request.text)
        current_external__fqdns = current_external__fqdns['assets']
        #print(current_external__fqdns)
        for current_fqdn_info in current_external__fqdns:
            #print(current_fqdn_info)
            current_fqdn_key = current_fqdn_info[0]['key']
            delete_fqdns_list.append(current_fqdn_key)

        #print(delete_fqdns_list)
        for key in delete_fqdns_list:
            key_payload= {
                    "key": ""+key+"",
                    "operation": "remove_asset",
                    "type":"external-dns-name",
                    "scope":"config",
                }

            delete_key_payload=json.dumps(key_payload)
            # https://api.cloudinsight.alertlogic.com/assets_write/v1/134234902/deployments/02610749-8C2B-4578-BD82-054225AE278D/assets
            delete_fqdn_url = f'{global_url}/assets_write/v1/{alert_logic_cid}/deployments/{deployment_id}/assets'
            delete_fqdn_response = requests.put(delete_fqdn_url, delete_key_payload, headers=headers)

            if delete_fqdn_response.status_code != 204:
                print(Fore.RED + f'    Error: FQDN with key: {key} was unable to be deleted. Got the following response: ' + Style.RESET_ALL)
                print(delete_fqdn_response)
            else :
                print(Fore.GREEN + f'    FQDN with key: {key} deleted successfully.' + Style.RESET_ALL)

if args.add_ips_or_fqdns:
    import_external_assets()
elif args.delete_all_ips:
    delete_all_external_ips()
elif args.delete_all_fqdns:
    delete_all_external_fqdns()
#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Required Libraries
from colorama import Fore, Back, Style
import ipaddress
import json
import csv
import os
import re
import requests
import time
#import pandas
from datetime import datetime

# Permanent Variables
true=True
false=False

# Variables from variables.py file
from variables import *
#from testvariables import *

sources_query_url = f'{sources_url}sources/v1/{alert_logic_cid}/hosts'
missing_network_source_list = []
multiple_network_source_list = []
missing_network_full_list = []

### Validate Authentication to Alert Logic API
# Function to get AIMS Token with the provided username and password
def get_api_token():
    url = f'{global_url}aims/v1/authenticate'
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
    url = f'{global_url}aims/v1/token_info'
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

# Find all orphans
def get_orphan_info(sources_query_url):
    sources_query_url = f'{sources_query_url}?status.status=error&status.stream=orphaned'
    sources_query_request = requests.get(sources_query_url, headers=headers)
    #print(sources_query_request)

    if sources_query_request.status_code != 200:
        print(Fore.RED + f'Error: Could not query for orphaned hosts. Got the following response: {sources_query_request}\n' + Style.RESET_ALL)
        exit()

    sources_query_response = json.loads(sources_query_request.text)
    if sources_query_response['total_count'] == 0:
        print(Fore.YELLOW + f'Finish: Count of orphaned hosts is equal 0. Nothing further to check.\n' + Style.RESET_ALL)
        exit()
    else:
        sources_query_response = sources_query_response['hosts']
        #print(sources_query_response)
        # Continue here: find Host/Agent info where Host UUID in list of Host UUID from the function above
        for source in sources_query_response:
            #"al-curl -v https://yard.alertlogic.com/sources/v1/10174534/hosts?status.status=error\&status.stream=orphaned | jq -r '.hosts[] | [.is_archived, .host.name, .host.id, .host.type, .host.metadata.local_ipv4[], .host.metadata.local_ipv4_net[], .host.status.stream, .host.status.status, .host.status.details[].error.code, .host.status.details[].error.description] | @csv'"
            archived = source['is_archived']
            host_name = source['host']['name']
            host_id = source['host']['id']
            host_type = source['host']['type']
            try:
                host_ip_list = source['host']['metadata']['local_ipv4']
            except:
                host_ip_list = source['host']['metadata']['public_ipv4']
            try:
                network_list = source['host']['metadata']['local_ipv4_net']
            except:
                network_list = source['host']['metadata']['public_ipv4_net']
            stream_info = source['host']['status']['stream']
            status_info = source['host']['status']['status']
            details = source['host']['status']['details']
            for detail in details:
                try:
                    multiple_networks = detail['error']['details']['networks'] 
                except Exception as e:
                    #print(f'My error is: {e}')
                    multiple_networks = []
                #print(multiple_networks)
                error_code = detail['error']['code']
                error_description = detail['error']['description']
            #print(multiple_networks)
            if len(multiple_networks) == 0:
                source_dict = {'host_name': host_name, 'host_id': host_id, 'host_type': host_type, 'host_ips': host_ip_list, 'missing_networks': network_list, 'stream_info': stream_info, 'status_info': status_info, 'error_code': error_code, 'error_description': error_description, 'is_archived': archived}
                missing_network_source_list.append(source_dict)
                for network_item in network_list:
                    missing_network_full_list.append(network_item)
            elif len(multiple_networks) > 0:
                multiple_networks_list = []
                network_details = {}
                net_count = 0
                for net in multiple_networks:
                    net_count = net_count + 1
                    network_name = net['network']['name']
                    network_key = net['network']['key']
                    deployment_name = net['deployment']['name']
                    deployment_id = net['deployment']['id']
                    network_entry = f'network_{net_count}'
                    network_dict = {'network_name': network_name, 'network_key': network_key, 'deployment_name': deployment_name, 'deployment_id': deployment_id}
                    #print(network_dict)
                    network_details = {network_entry : network_dict}
                    multiple_networks_list.append(network_details)
                source_dict = {'host_name': host_name, 'host_id': host_id, 'host_type': host_type, 'host_ips': host_ip_list, 'multiple_networks': network_list, 'stream_info': stream_info, 'status_info': status_info, 'error_code': error_code, 'error_description': error_description, 'multiple_networks_list': multiple_networks_list, 'is_archived': archived}
                #print(source_dict)
                multiple_network_source_list.append(source_dict)
            #print(host_ip_list)
    missing_network_set = set(missing_network_full_list)
    
    print(Fore.MAGENTA + f'The unique list of networks that need to be added to a deployment in order for the sources to reclaim are:\n' + Fore.YELLOW + f' {missing_network_set}')
    print(Fore.MAGENTA + f'The count of orphaned hosts/appliances that do not have a network containing their CIDR range: ' + Fore.YELLOW + f'{len(missing_network_source_list)}')
    print(Fore.MAGENTA + f'The count of orphaned hosts/appliances that have multiple networks containing their CIDR range: ' + Fore.YELLOW + f'{len(multiple_network_source_list)}')

get_orphan_info(sources_query_url)

def export_sources_csv():
    if len(missing_network_source_list) > 0:
        source_list_keys = missing_network_source_list[0].keys()
        with open(missing_networks_csv, 'w', encoding='utf8', newline='') as csv_output:
            dict_writer = csv.DictWriter(csv_output, fieldnames=source_list_keys)
            dict_writer.writeheader()
            dict_writer.writerows(missing_network_source_list)

        print(Fore.LIGHTBLUE_EX + ' Creating the CSV file complete with list of sources missing a network' + Style.RESET_ALL)
    
    else:
        print(Fore.LIGHTBLUE_EX + ' There are no sources missing a network CIDR range' + Style.RESET_ALL)
    
    if len(multiple_network_source_list) > 0:
        source_list_keys = multiple_network_source_list[0].keys()
        with open(multiple_networks_csv, 'w', encoding='utf8', newline='') as csv_output:
            dict_writer = csv.DictWriter(csv_output, fieldnames=source_list_keys)
            dict_writer.writeheader()
            dict_writer.writerows(multiple_network_source_list)

        print(Fore.LIGHTBLUE_EX + ' Creating the CSV file complete with list of sources that have multiple network options' + Style.RESET_ALL)

    else:
        print(Fore.LIGHTBLUE_EX + ' There are no sources with multiple network CIDR ranges' + Style.RESET_ALL)

export_sources_csv()

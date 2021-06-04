#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Required Libraries
import ipaddress
import json
import csv
import os
import requests
import time
import pandas
from datetime import datetime

# Permanent Variables
true=True
false=False

# Variables from variables.py file
from variables import *
#from testvariables import *

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
        print(f'Error: Could not authenticate. Got the following response: {token_response}\n')
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
        print(' Errror: Could not generate / validate AIMS Token. Please check credentials and try again\n')
        exit()
    else :
        print(' AIMS token generated and validated.\n')
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
    print ('\nError: No credentials stored in the configuration file, to allow authentication against the API.\n')
    exit()

# Request a list of networks and subnets
networks_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=network'
networks_query_request = requests.get(networks_query_url, headers=headers)

networks_query_response = json.loads(networks_query_request.text)
networks_query_response = networks_query_response['assets']

subnets_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=subnet'
subnets_query_request = requests.get(subnets_query_url, headers=headers)

subnets_query_response = json.loads(subnets_query_request.text)
subnets_query_response = subnets_query_response['assets']

networks_list = []
subnets_list = []
#no_stats_agent_list = []

def network_list_func():
    # Loop through networks and assets output to find assets that fit the criteria to be presented in a csv file
    for network in networks_query_response:
        network = network[0]
        network_name = network['network_name']
        network_key = network['key']

        network_dict = {}
        network_dict = {'network_name': network_name, 'network_key': network_key}
        networks_list.append(network_dict)

network_list_func()

def subnet_list_func():      
    for subnet in subnets_query_response:
        subnet = subnet[0]
        subnet_dict = {}
        subnet_name = subnet['subnet_name']
        subnet_key = subnet['key']
        network_key = subnet['path'][2].split(':')
        network_key = network_key[1]
        try:
            cidr = subnet['cidr_block']
        except:
            cidr = 'Default Subnet'

        for network_dict_entry in networks_list:
            if network_key == network_dict_entry['network_key']:
                network_name = network_dict_entry['network_name']


        subnet_dict = {'subnet_name': subnet_name, 'cidr_range': cidr, 'network_name': network_name}
        subnets_list.append(subnet_dict)

    print(f'The length of the list of networks with stats was: {len(subnets_list)}')

subnet_list_func()
'''
def duplicates_identification():
    df = pandas.DataFrame(subnets_list)
    df_duplicated = df.duplicated(keep=False, subset=['cidr_range'])

    print(df)
    print(df_duplicated)

duplicates_identification()
'''
def export_subnet_csv():
    subnets_list_keys = subnets_list[0].keys()
    with open(csv_file_name, 'w', encoding='utf8', newline='') as csv_output:
        dict_writer = csv.DictWriter(csv_output, fieldnames=subnets_list_keys)
        dict_writer.writeheader()
        dict_writer.writerows(subnets_list)

    print(' Creating the CSV file complete with list of networks')

export_subnet_csv()
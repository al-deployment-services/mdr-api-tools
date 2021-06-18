#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Required Libraries
import ipaddress
import json
import csv
import os
import requests
import time
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
        print(f'Error: Could not authenticate. Got the following response: {token_response}\n')
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

# Request a list of agents and hosts
agents_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=agent'
agents_query_request = requests.get(agents_query_url, headers=headers)

agents_query_response = json.loads(agents_query_request.text)
agents_query_response = agents_query_response['assets']

hosts_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=host'
hosts_query_request = requests.get(hosts_query_url, headers=headers)

hosts_query_response = json.loads(hosts_query_request.text)
hosts_query_response = hosts_query_response['assets']

agent_list = []
no_stats_agent_list = []

def agent_list_func():
    # Loop through agents and assets output to find assets that fit the criteria to be presented in a csv file
    for agent in agents_query_response:
        agent = agent[0]
        host_uuid = agent['host_uuid']
        key = f'/dc/host/{host_uuid}'
        
        for host in hosts_query_response:
            host = host[0]
            if host['key'] == key:
                agent_ip_list = host['local_ipv4']
                agent_ip = agent_ip_list[0]
                agent_name = host['local_hostname']
                agent_network_key = host['path'][2].split(':')
                agent_network_key = agent_network_key[1]
                
                if specified_network_key != '':
                    # Do the following if a network key was specified in the config file
                    def create_agent_dicts():
                        try:
                            # Creating a list of dictionaries, each dictionary is an agent config --- 'last_day_ids': agent['statistics['packets_ids['last_day']']'],
                            last_day_ids_packets = agent['statistics']['packets_ids']['last_day']
                            if agent_network_key == specified_network_key:
                                agent_dict = {'host_name': agent_name, 'agent_ip': agent_ip, 'last_day_packets': last_day_ids_packets, 'network_key': agent_network_key}
                                agent_list.append(agent_dict)

                        except:
                            no_stats_agent_dict = {'host_name': agent_name, 'agent_ip': agent_ip}
                            no_stats_agent_list.append(no_stats_agent_dict)
                    
                    create_agent_dicts()
                        
                elif specified_network_key == '':
                    # Do the following if a no network key was specified in the config file
                    create_agent_dicts()

    print(f'The length of the list of agents with stats was: {len(agent_list)}')
    print(f'The length of the list of agents without stats was: {len(no_stats_agent_list)}')

agent_list_func()

def export_agent_csv():
    agent_list_keys = agent_list[0].keys()
    with open(csv_file_name, 'w', encoding='utf8', newline='') as csv_output:
        dict_writer = csv.DictWriter(csv_output, fieldnames=agent_list_keys)
        dict_writer.writeheader()
        dict_writer.writerows(agent_list)

    print(' Creating the CSV file complete with list of agents')

export_agent_csv()
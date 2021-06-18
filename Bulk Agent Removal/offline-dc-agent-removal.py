#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Required Libraries
import json
import os
import requests
import time
from datetime import datetime

# Permanent Variables
true=True
false=False
agent_list = []

# Variables from variables.py file
from mfavariables import *
#from testmfavariables import *

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
    mfa_payload = mfa_payload.replace("'",'"')

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

# Request all configured agents and hosts in assets
def get_agents_list():
    agents_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=agent'
    agents_query_request = requests.get(agents_query_url, headers=headers)
    agents_query_response = json.loads(agents_query_request.text)
    agents_query_response = agents_query_response['assets']

    hosts_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=host'
    hosts_query_request = requests.get(hosts_query_url, headers=headers)
    hosts_query_response = json.loads(hosts_query_request.text)
    hosts_query_response = hosts_query_response['assets']
    # Filter agents based on criteria

    for agent in agents_query_response:
        agent = agent[0]
        host_uuid = agent['host_uuid']
        host_key_value = f'/dc/host/{host_uuid}'
        agent_name_value = agent['agent_name']
        agent_key_value = agent['key']
        try: 
            agent_status_value = agent['statuses']['master_offline_status']['condition']
        except:
            agent_status_value = 'online'
        for host in hosts_query_response:
            host = host[0]
            if host['key'] == host_key_value and agent_status_value == 'offline':
                # Creating a list of dictionaries, each dictionary is an agent config
                agent_dict = {'agent_name': agent_name_value, 'agent_key': agent['key'], 'host_key': host_key_value, 'agent_status': agent_status_value}
                print(f'This is my agent dictionary: \n {agent_dict}')
                agent_list.append(agent_dict)

    #print(f'The length of this list is: {len(agent_list)}')

def delete_agents_from_list():
    for agent in agent_list:
        delete_agent_payload = {"operation": "remove_asset","scope": "host","type": "agent","key": agent['agent_key']}
        # Tidy up the payload
        delete_agent_payload = json.dumps(delete_agent_payload)
        delete_agent_payload=delete_agent_payload.replace("'",'"')
        # Delete the agent
        agents_delete_url = f'{global_url}/assets_write/v1/{alert_logic_cid}/deployments/{deployment_id}/assets'
        agents_delete_request = requests.put(agents_delete_url, delete_agent_payload, headers=headers)
        
        delete_host_payload = {"operation": "remove_asset","scope": "host","type": "host","key": agent['host_key']}
        # Tidy up the payload
        delete_host_payload = json.dumps(delete_host_payload)
        delete_host_payload=delete_host_payload.replace("'",'"')
        # Delete the host
        hosts_delete_request = requests.put(agents_delete_url, delete_host_payload, headers=headers)

print('Comparing Host records with Agent records and deciding what to delete.')
get_agents_list()
print('Deleting Agents and Hosts.')
delete_agents_from_list()
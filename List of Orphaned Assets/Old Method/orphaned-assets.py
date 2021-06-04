#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Required Libraries
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

assets_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets'
sources_query_url = f'{sources_url}/sources/{alert_logic_cid}/hosts'

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

# Import the JSON file of all clyde messages. Commenting this out because we will use CSVs from the AL Console, but still useful tooling:
'''
host_uuid_list = []

def import_json():
    with open(json_file) as js:
        js = json.load(js)

    for entry in js:
        message = entry['message']
        pattern = r'\"(.+?)\"'
        result = re.findall(r'\"(.+?)\"', message)

        for entry in result:
            host_uuid_list.append(entry)
        #break

import_json()
'''
# Import the CSV file of all clyde messages. This can be exported from Expert Mode Search with a query like the following for the last hour:
'''
SELECT time_recv, message
FROM logmsgs
WHERE program = 'al-clyde' AND message CONTAINS 'Cannot reprovision host' AND message CONTAINS '52147'
ORDER BY time_recv DESC
LIMIT 100000
'''
host_uuid_list = []

def import_csv():
    with open(csv_import_file) as csv_file:
        csv_reader = csv.reader(csv_file)
        try:
            for entry in csv_reader:
                #print(entry)
                message = entry[1]
                pattern = r'\"[A-Z0-9]{8}\-[A-Z0-9]{4}\-[A-Z0-9]{4}\-[A-Z0-9]{4}\-[A-Z0-9]{12}\"'
                result = re.findall(r'\"(.+?)\"', message)
                #print(result)
                for entry in result:
                    host_uuid_list.append(entry)
                #break
        except Exception as e:
            print(f'This is my error attempting to import: {e}')
            #continue

import_csv()

#print(len(host_uuid_list))
host_uuid_list = list (dict.fromkeys(host_uuid_list))
print(f'This is the count of unique UUIDs from the imported csv: {len(host_uuid_list)}')

# Find a count of host that exist in assets for each Host UUID from above
def get_host_info():
    agents_query_url = f'{assets_query_url}?asset_types=agent'
    agents_query_request = requests.get(agents_query_url, headers=headers)
    agents_query_response = json.loads(agents_query_request.text)
    agents_query_response = agents_query_response['assets']

    hosts_query_url = f'{assets_query_url}?asset_types=host'
    hosts_query_request = requests.get(hosts_query_url, headers=headers)
    hosts_query_response = json.loads(hosts_query_request.text)
    hosts_query_response = hosts_query_response['assets']

    list_count = []
    # Continue here: find Host/Agent info where Host UUID in list of Host UUID from the function above
    for agent in agents_query_response:
        agent = agent[0]
        host_uuid = agent['host_uuid']
        host_key_value = f'/dc/host/{host_uuid}'
        agent_name_value = agent['agent_name']
        agent_key_value = agent['key']

        for host in hosts_query_response:
            host = host[0]
            ### Left off here because the entries don't actually exist for the orphaned agents for CEC Entertainment. But to finish from here, I need to export the desired rows into a csv file. ###
            if host['key'] == host_key_value and host_uuid in host_uuid_list:
                list_count.append('entry')
    print(f'This is the count of orphaned hosts/appliances that show in assets: {len(list_count)}')

get_host_info()

# Check to see if the hosts exist in the old sources API
source_list = []
failed_source_uuids = []
def get_source_info():
    for host_uuid in host_uuid_list:
        source_dict = {}
        try:
            sources_api_query_url = f'{sources_query_url}/{host_uuid}'
            sources_api_query_request = requests.get(sources_api_query_url)
            sources_api_query_response = json.loads(sources_api_query_request.text)
            sources_api_query_response = sources_api_query_response['host']

            source_host_name = sources_api_query_response['name']
            source_local_host_name = sources_api_query_response['metadata']['local_hostname']
            source_local_ip = sources_api_query_response['metadata']['local_ipv4'][0]

        except:
            failed_source_uuids.append(host_uuid)
            continue

        source_dict = {'host_name': source_host_name, 'local_host_name': source_local_host_name, 'private_ip': source_local_ip}
        source_list.append(source_dict)

get_source_info()

#print(f'This is my list of orphaned sources: {source_list}')
print(f'This is my count of orphaned sources: {len(source_list)}')
'''
# See if there are any orphaned appliances
def check_orphaned_appliances():
    appliance_query_url = f'{assets_query_url}?asset_types=appliance,host&return_count=true'
    appliance_query_request = requests.get(appliance_query_url, headers=headers)
    appliance_query_response = json.loads(appliance_query_request.text)
    appliance_query_response = appliance_query_response['assets']

    appliance_no_topo_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=host'
    appliance_no_topo_query_request = requests.get(appliance_no_topo_query_url, headers=headers)
    appliance_no_topo_query_response = json.loads(appliance_no_topo_query_request.text)
    appliance_no_topo_query_response = appliance_no_topo_query_response['assets']
'''

def export_sources_csv():
    source_list_keys = source_list[0].keys()
    with open(csv_file_name, 'w', encoding='utf8', newline='') as csv_output:
        dict_writer = csv.DictWriter(csv_output, fieldnames=source_list_keys)
        dict_writer.writeheader()
        dict_writer.writerows(source_list)

    print(' Creating the CSV file complete with list of orphaned hosts')
    
    with open(failed_sources_csv, 'w', encoding='utf8', newline='') as failed_output:
        write_rows = csv.writer(failed_output)
        write_rows.writerow(failed_source_uuids)

    print(' Creating the CSV file complete with list of UUIDs trying to claim without host records')

export_sources_csv()

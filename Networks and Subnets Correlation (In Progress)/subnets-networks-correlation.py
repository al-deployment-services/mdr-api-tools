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
#from variables import *
from testvariables import *

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
networks_dict_list = []
subnets_list = []
subnets_dict_list = []
modified_network_list = []

def network_list_func():
    # Loop through networks and assets output to find assets that fit the criteria to be presented in a csv file
    for network in networks_query_response:
        network = network[0]
        network_name = network['network_name']
        network_key = network['key']
        network_cidr_ranges = network['cidr_ranges']

        network_dict = {}
        network_dict = {'network_name': network_name, 'network_key': network_key, 'network_cidr_ranges': network_cidr_ranges}
        networks_dict_list.append(network_dict)
        for cidr_range in network_cidr_ranges:
            networks_list.append(cidr_range)

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

        for network_dict_entry in networks_dict_list:
            if network_key == network_dict_entry['network_key']:
                network_name = network_dict_entry['network_name']


        subnet_dict = {'subnet_name': subnet_name, 'cidr_range': cidr, 'network_name': network_name}
        subnets_dict_list.append(subnet_dict)
        subnets_list.append(cidr)

    print(f'The length of the list of subnets was: {len(subnets_list)}')
    #print(f'The list of subnets were: {subnets_list}')

subnet_list_func()

class IPAddress_Networks_List:
    def __init__(self, networks_list, modified_network_list):
        self.networks_list = networks_list
        self.modified_network_list = modified_network_list

    def network_ippaddress_list(self):
        modified_network_list = []
        for network in self.networks_list:
            self.modified_network_list.append(ipaddress.ip_network(network))
        #print(f'This is my network inside of the class: {self.modified_network_list}')

modified_list = IPAddress_Networks_List(networks_list, modified_network_list)
modified_list.network_ippaddress_list()

def compare_subnets_networks(networks_list, modified_network_list):
    smaller_prefix_network_cidrs_list = []
    for subnet_entry in subnets_dict_list:
        prefix_modified_network_list = []
        subnet_cidr_range = subnet_entry['cidr_range']
        subnet_cidr_prefix = subnet_cidr_range.split('/')
        try:
            subnet_cidr_prefix = subnet_cidr_prefix[1]
        except:
            #print(f'Waaaa! I\'m a default subnet')
            subnet_entry['state'] = 'default subnet'
            continue 
        #print(f'  This is my cidr prefix: {subnet_cidr_prefix}')
        #print(networks_list)
        for network in networks_list:
            #print(f'This is my current entry in the network list: {network}')
            try:
                modified_network = list(ipaddress.ip_network(network).subnets(new_prefix=int(subnet_cidr_prefix)))
                #print(f'This is my current entry in the modified network: {modified_network}')
                #print('I am in the inner circle so break my prefix!')
                for mod_network in modified_network:
                    prefix_modified_network_list.append(mod_network)
            except:
                #print('I am in the outer circle, keep my prefix.')
                smaller_prefix_network_cidrs_list.append(network)
                continue
        smaller_cidrs_list = list(dict.fromkeys(smaller_prefix_network_cidrs_list))
        #print(f'The list of networks to be modified by prefix is: {prefix_modified_network_list}')
        #print(f'The list of networks too small to be modified by prefix is: {smaller_cidrs_list}')
        if ipaddress.ip_network(subnet_cidr_range) in modified_network_list:
            #print(f'Yay Me! My cidr range is in a configured network\'s cidr range')
            subnet_entry['state'] = 'included'
        elif ipaddress.ip_network(subnet_cidr_range) in prefix_modified_network_list:
            #print(f'Yay Me! My cidr range is in a configured network\'s cidr range') 
            subnet_entry['state'] = 'included'
        else:
            print('Well Fuck!')
            subnet_entry['state'] = 'excluded'
    
    #print(subnets_dict_list)
    modified_network_cidr_list = []
    new_subnet_list = []
    subnet_cidr_list = []
    for network_entry in networks_dict_list:
        network_cidr_list = []
        network_cidr_ranges = network_entry['network_cidr_ranges']
        for cidr in network_cidr_ranges:
            network_cidr_list.append(cidr)

        for subnet_entry in subnets_dict_list:
            '''
            res = 0
            for key in subnet_entry:
                if subnet_entry['network_name'] == network_entry['network_name']:
                    res = res + 1
                    
            if res <= 1:
                print(f'I am less than or equal to one, value is: {res}')
            '''
            network_name = subnet_entry['network_name']
            cidr_range = subnet_entry['cidr_range']
            if network_name == network_entry['network_name'] and cidr_range != 'Default Subnet':
                subnet_cidr_list.append(cidr_range)
                new_subnet_list.append(subnet_entry)
                #print(f'My subnet cidr is: {cidr_range}')
                cidr_prefix = cidr_range.split('/')
                cidr_prefix = cidr_prefix[1]
                for network_cidr in network_cidr_list:
                    #if network_cidr == 
                    modified_network = list(ipaddress.ip_network(network_cidr).subnets(new_prefix=int(cidr_prefix)))
                    #print(f'My modified_network list entry per item in network_cidr_list: {modified_network}')
                    for mod_network in modified_network:
                        modified_network_cidr_list.append(mod_network)
                        modified_network_cidr_list = list(dict.fromkeys(modified_network_cidr_list))
                        #print(f'This is my list of modified networks: {modified_network_cidr_list}')
        '''
        print(network_cidr_list)    
        for network in network_cidr_list:
            print(f'My subnet cidr list: {subnet_cidr_list}')
            if network not in subnet_cidr_list:
                print(f'This is my network cidr not in the subnets list {network}')
                for subnet in subnet_cidr_list:

                    modified_subnet = 
        '''
    # The below creates the list of network CIDRs where a subnet does not exist. However it is built on a list of subnets. It does not consider 
    # any Networks CIDRs where the Network only has a Default Subnet.
    for subnet in new_subnet_list:
        #print(f'This is my value in my subnet list: {subnet}')
        cidr_range = subnet['cidr_range']        
        if ipaddress.ip_network(cidr_range) in modified_network_cidr_list:
            modified_network_cidr_list.remove(ipaddress.ip_network(cidr_range))
            #network_cidr_list.remove(network_cidr)
        print(f'This is the modified networks list after removing subnet: {modified_network_cidr_list}')
        # The desired output for here should be the subnet cidr that should be created, and what network it belongs to

                
'''
    # Remove duplicate entries and find where networks cidrs only partially exist for subnet cidrs
    
    for network in smaller_cidrs_list:
        modified_subnet = list(ipaddress.ip_network(network).subnets(new_prefix=int(subnet_cidr_prefix)))
'''
compare_subnets_networks(networks_list, modified_network_list)

def export_subnet_csv():
    subnets_dict_list_keys = subnets_dict_list[0].keys()
    with open(subnets_csv_file_name, 'w', encoding='utf8', newline='') as csv_output:
        dict_writer = csv.DictWriter(csv_output, fieldnames=subnets_dict_list_keys)
        dict_writer.writeheader()
        dict_writer.writerows(subnets_dict_list)

    print(f'  Created the CSV file with a list of subnet correlations to networks')

export_subnet_csv()
#!/usr/bin/python3
#Collaberation from Andre Holder and Rob VanOrman

#Required Libraries
from colorama import Fore, Back, Style
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
    # Ask the user for their MFA codels -la
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
        print(Fore.RED + ' Error: Could not generate / validate AIMS Token. Please check credentials and try again\n' + Style.RESET_ALL)
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

#Get CID that the token exists in (CID the authenticated user was in). Then check if that CID is authorised to view
users_CID = validate_info['user']['account_id']

#Print out authenticated user information
print('Authenticated Users Info:\n')
user_name = validate_info['user']['name']
user_email = validate_info['user']['email']
user_role = validate_info['roles'][0]['name']
user_lastlogin_unix = validate_info['user']['user_credential']['last_login']
user_lastlogin_hr = datetime.utcfromtimestamp(user_lastlogin_unix ).strftime('%d/%m/%Y %H:%M:%S %Z')
print('    Name: ' + user_name)
print('    Email: ' + user_email)
print('    User Role: ' + user_role)
print('    CID: ' + users_CID)
#print('    Last authentication: ' + user_lastlogin_hr) #Don't think this is needed, last time user logged into the UI
print()


#If the CID the user has authenticated from, is not equal to the target CID
if alert_logic_cid != users_CID:
	#This is checking whether there is a managed relationship (ensuring a parent-child relationship) between the 2 CID's.
	managed_CID_check_url = f'{global_url}/aims/v1/{users_CID}/accounts/managed/{alert_logic_cid}'
	managed_CID_check_response = requests.get(managed_CID_check_url, headers=headers)
	managed_CID_check_statuscode = managed_CID_check_response.status_code

	#1 - Make sure the CID's have a managed relationship (Status Code 204 is a success response)
	if managed_CID_check_statuscode != 204:
		print(' Error: Authenticated user does not have authorisation to perform actions in CID ' + alert_logic_cid + ' Please try another user.\n')
		exit()

	#2 - If yes to step 1, make sure authenticated user has permissions to create stuff in target CID
	if user_role == 'Read Only' or user_role == 'Support/Care' or user_role == 'Power User' :
		print ('Error: Authenticated user does not have the required permission to create in CID ' + alert_logic_cid)
		print ('\n    - User must be Administrator or Owner\n')
		exit()

#If the CID the user has authenticated from, is equal to the target CID
elif alert_logic_cid == users_CID:
	# Make sure the autenticated user has permission to create in target CID
	if user_role == 'Read Only' or user_role == 'Support/Care' :
		print ('Error: Authenticated user does not have the required permission to create in CID ' + alert_logic_cid)
		print ('\n    - User must be Administrator, Owner or Power user\n')
		exit()

#Get some account information from the CID
print('Target CID Info:\n')
account_info_url = f'{global_url}/aims/v1/{alert_logic_cid}/account'
account_info_response = requests.get(account_info_url, headers=headers)
account_info = json.loads(account_info_response.text)
account_name = account_info['name']
account_CID = alert_logic_cid
account_defaultloc = account_info['default_location']
print('    Account Name: ' + account_name)
print('    Accound CID: ' + account_CID)
print('    Default Location: ' + account_defaultloc)
print('    Base URL: ' + global_url)
print()

# Create the networks in the portal
def create_networks ():
	global network_keys
	global protected_networks
	global list_networks
	global networks_scope_dict
	global network_keys_dict
	network_keys_dict = {}
	networks_scope_dict = {}
	network_keys = []
	protected_networks = []
	list_networks = []

	#Get the policy ID's for the scope of protection levels.
	policies_info_url = f'{global_url}/policies/v1/{alert_logic_cid}/policies'
	policies_info_response = requests.get(policies_info_url, headers=headers)
	policies_info = json.loads(policies_info_response.text)

	if not network_csv_file:
		print("    No networks detected in a csv file. Please provide the file path to the list of networks in a .csv in the properties file.\n")
		protected_networks.append("\t\t\t\tNo networks defined")
	else: 
		#Read from networks csv file
		with open(network_csv_file, newline='') as csv_file:
			reader = csv.reader(csv_file)
			networks = list(reader)

		for network in networks: 
			#Pull out network name and scope of protection as the first and second value in list
			network_name=network[0]
			network_scope=network[1]

			#The following code identifies the entitlement ID for the scope of protection for the network
			entitlement=network_scope.capitalize()
			policy_id = [x for x in policies_info if x['name'] == entitlement]
			entitlement_id=policy_id[0]['id']
			networks_scope_dict[network_name] = [network_scope,entitlement_id]
			
			cidr_list = []
			#For every value other than the first, append to new list
			for cidr in network[2:]: 
				cidr_list.append(cidr)
		
			#Format the cidr list ready for the POST payload
			json_cidr_list=str(cidr_list)[2:-1]
			
			#Network creation payload
			network_payload = {
					"network_name": network_name,
					"cidr_ranges": [(json_cidr_list)],
					"span_port_enabled": true
				}
			
			#Convert the payload (including the cidr list) into json
			create_network_payload=json.dumps(network_payload)
			#Inside the scope, replace the [" "] so it's just [ ] 
			#create_network_payload=create_network_payload.replace('["','[')
			create_network_payload=create_network_payload.replace('"]',']')
			#Change the objects inside the cidr list to be surrounded by double quotes instead of single
			create_network_payload=create_network_payload.replace("'",'"')
			#Create networks and store the network keys into a new list, network_keys (so that we can add to scope later)
			create_network_url = f'{global_url}/assets_manager/v1/{alert_logic_cid}/deployments/{deployment_id}/networks'
			create_network_response = requests.post(create_network_url, create_network_payload, headers=headers)

			if create_network_response.status_code !=200: 
				print('    Error: Network with name '+network_name+ ' creation failed. Got the following response: '+ str(create_network_response.status_code))
			else: 
				print('    Network with name '+network_name+ ' created successfully, with CIDR ranges ' + json_cidr_list)
				protected_networks.append("\t\t\t\tNetwork: "+network_name+"\tCIDR's: "+str(cidr_list)[1:-1].replace("'", "")+"\n")
			
			create_network_info = json.loads(create_network_response.text)
			global network_key
			global claim_key
			network_key=create_network_info['key']
			network_keys.append(network_key)
			network_keys_dict[network_name] = network_key
			claim_key=create_network_info['claim_key']
			list_networks.append("    Network Name: " +network_name+"\t\tUnique Key: "+claim_key+"\n")
			
			#Find the network UUID for creating subnets later
			global network_id
			#Giving the network time create, was failing going straight into this
			time.sleep(1)
			# Query assets_query for full network info
			network_id_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=v:vpc&v.key={network_key}'
			network_uuid_response = requests.get(network_id_url, headers=headers)
			# Pull network_uuid value out
			network_uuid_info = json.loads(network_uuid_response.text)
			network_uuid_info=network_uuid_info['assets'][0]
			network_id=network_uuid_info[0]['network_uuid']

			# Subnet creation for each network
			for each_cidr in cidr_list:
				list_subnets = [] 
				
				# Subnet creation payload
				subnet_name = network_name+ ' (' +each_cidr+ ')'
				subnet_payload = {
						"subnet_name": subnet_name,
						"cidr_block": (each_cidr)
					}

				# Convert the payload into json
				create_subnet_payload=json.dumps(subnet_payload)
				# Inside the scope, replace the [" "] so it's just [ ] 
				create_subnet_payload=create_subnet_payload.replace('["','[')
				create_subnet_payload=create_subnet_payload.replace('"]',']')
				# Change the objects inside the cidr list to be surrounded by double quotes instead of single
				create_subnet_payload=create_subnet_payload.replace("'",'"')
				
				# Create networks and store the network keys into a new list, network_keys (so that we can add to scope later)
				create_subnet_url = f'{global_url}/assets_manager/v1/{alert_logic_cid}/deployments/{deployment_id}/networks/{network_id}/subnets'
				create_subnet_response = requests.post(create_subnet_url, create_subnet_payload, headers=headers)
				
				if create_subnet_response.status_code !=200: 
					print('    Error: Subnet with name '+subnet_name+ ' creation failed. Got the following response: '+ str(create_subnet_response.status_code))
				else: 
					print('    Subnet with name '+subnet_name+ ' created successfully, with CIDR block ' + each_cidr)
					#protected_subnets.append("\t\t\t\tNetwork: "+network_name+"\tCIDR's: "+str(cidr_list)[1:-1].replace("'", "")+"\n")

				list_subnets.append("    Subnet Name: " +subnet_name+ "\n")
			
	print()
	
	# Print created networks and the associated claim key
	list_networks=''.join(list_networks)
	print("The networks just created, and their associated unique registration keys: ")
	print(str(list_networks))	
	# For logging purposes
	protected_networks=''.join(protected_networks)

def set_scope_protection (): 
	scope_list = []
	#scope_list_two = []
	
	if not network_keys: 
		print("    No networks were created. Skipping.")
	else: 
		# Create a list of scope of protection entries for each network
		for network_name in networks_scope_dict:
			networks_scope_dict[network_name].append(network_keys_dict[network_name])
			scope_list.append("{\"key\":\""+networks_scope_dict[network_name][2]+"\",\"type\":\"vpc\",\"policy\":{\"id\":\""+networks_scope_dict[network_name][1]+"\"}}")
		
		# Convert python list to string
		scope=str(scope_list)[1:-1]
		
		# Find Deployment details
		deployment_url = f'{global_url}/deployments/v1/{alert_logic_cid}/deployments/{deployment_id}'
		get_deployment_response = requests.get(deployment_url, headers=headers)
		if get_deployment_response.status_code !=200:
			print('    Error: Could not get the details of the deployment. Got the following response code: '+str(update_scope_response.status_code))
			exit()
		else:
			deployment_info = json.loads(get_deployment_response.text)
			deployment_version = deployment_info['version']
			deployment_current_scope = []
			deployment_current_scope = deployment_info['scope']['include']
	
		# Remove single quotes between each json object, dump into json then remove any extra slashes
		scope_json=scope.replace("'","")
		scope_json=json.dumps(scope_json)
		scope_json=scope_json.replace("\\", "")
		deployment_new_scope = deployment_current_scope
		deployment_new_scope.append(scope_json)

		update_scope_payload={
			"version": deployment_version,
			"scope": {
				"include": deployment_new_scope,
				}
			}
		
		update_scope_payload=json.dumps(update_scope_payload)
		update_scope_payload=update_scope_payload.replace("\\", "")
		update_scope_payload=update_scope_payload.replace('""', "")
		#print(update_scope_payload)
		#update_scope_url = f'{global_url}/deployments/v1/{alert_logic_cid}/deployments/{deployment_id}'
		update_scope_response = requests.put(deployment_url, update_scope_payload, headers=headers)
	
		if update_scope_response.status_code !=200:
			print(f'    Error: Protection levels not added to deployment. Got the following response code: {str(update_scope_response.status_code)}\n And got the following message: {str(update_scope_response.text)}')
		else:
			print('    Protection levels successfully added to deployment')
	print()

print("Creating Networks:\n")
create_networks()
print("Setting Protection Level on Networks:\n")
set_scope_protection()
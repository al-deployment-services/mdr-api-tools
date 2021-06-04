#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Imported Modules
from modules.shared_content import *
from modules.authentication import Authenticate_User
from modules.deployments import Deployments

#print(f'this is my auth header: {auth_header}')

### Validate Authentication to Alert Logic API
auth_attempt = Authenticate_User(global_url, username, password, auth_header)
auth_attempt.authentication_header()

#print(f'This is my main scripts auth header: {query_auth_header}')

######################################################################################################
### Start here to pull list of deployments, then iterate through them with queries to assets below ###
######################################################################################################
### Use dictionaries to store the names of assets with keys and UUIDs                              ###
### Use a modules to be able to parameterize each item to print, export etc                        ###
######################################################################################################

### Deploymnents ###
# LEFT OFF HERE - USE argparse or getopt MODULE TO CREATE PARAMETERS #
# Get a list of deployments for the specified CID in variables.py

# Likely will take out this as an option and just make it mandatory as part of the list-of-assets-mdr.py script. This is a must for almost anything further in this script.
# Possibly use a parameter to print out the deployment info to screen or not.

@click.command()
@click.option(
    '--print_deployments/--no_print_deployments',
    default=False,
    help='Prints all deployments for the given CID in variables.py to screen'
    )

# Figure out how to get the value of query_auth_header above into the instantiated class of deployments.py
def deployments_query(print_deployments):
    query_auth_header = auth_attempt.auth_header
    deployments_attempt = Deployments(global_url, alert_logic_cid, print_deployments, deployments_list, query_auth_header)
    #deployments_attempt.click_options()
    deployments_attempt.deployments_data()
    

'''
#@click.option(
#    '--networks/--no-networks',
#    default=False,
#    help='Runs a check for all networks for deployments above'
#)

# Set this up so that all of the click options above are called in call_all_the_things() function and then that function calls each subsequent function if true or false #


### Appliances ###

### Agents ###
# Agent/Host Assets  Starting Point
# Request a list of agents and hosts
agents_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=agent'
agents_query_request = requests.get(agents_query_url, headers=auth_attempt.auth_header)

agents_query_response = json.loads(agents_query_request.text)
agents_query_response = agents_query_response['assets']

try:
    print(agents_query_response[0])
except:
    print(f'No agents for deployment: {deployment_name}')
print(f'\n')

hosts_query_url = f'{global_url}/assets_query/v1/{alert_logic_cid}/deployments/{deployment_id}/assets?asset_types=host'
hosts_query_request = requests.get(hosts_query_url, headers=auth_attempt.auth_header)

hosts_query_response = json.loads(hosts_query_request.text)
hosts_query_response = hosts_query_response['assets']

try:
    print(hosts_query_response[0])
except:
    print(f'No hosts for deployment: {deployment_name}')
print(f'\n')

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
'''
if __name__ == '__main__':
    deployments_query()

#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Import Shared Content
from modules.shared_content import *
from modules.authentication import Authenticate_User

class Deployments(Authenticate_User):
    def __init__(self, global_url, alert_logic_cid, print_deployments, deployments_list, query_auth_header):
        self.global_url = global_url
        self.query_auth_header = query_auth_header
        self.alert_logic_cid = alert_logic_cid
        self.print_deployments = print_deployments
        self.deployments_list = deployments_list

    def deployments_data(self):
        deployments_query_url = f'{global_url}/deployments/v1/{alert_logic_cid}/deployments'
        deployments_query_request = requests.get(deployments_query_url, headers=self.query_auth_header)
        deployments_query_response = json.loads(deployments_query_request.text)
        deployment_dict = {}
        self.deployments_list = []
        for deployment in deployments_query_response:
            deployment_id = deployment['id']
            deployment_name = deployment['name']
            deployment_status = deployment['status']['status']
            deployment_type = deployment['platform']['type']
            deployment_scan_status = str(deployment['scan'])
            deployment_mode = deployment['mode']
            deployment_enabled = str(deployment['enabled'])
            deployment_discovery_enabled = str(deployment['discover'])
            # Try to find the Credentials ID if it is Azure or AWS, otherwise print an empty list
            try: 
                deployment_credentials = deployment['credentials'][0]['id']
            except:
                # Possibly change this to print a string saying this is data center type
                deployment_credentials = str(deployment['credentials'])

            deployment_dict = {'name': deployment_name, 'deployment_id': deployment_id, 'status': deployment_status, 'type': deployment_type, 'scan_status': deployment_scan_status, 'mode': deployment_mode, 'enabled': deployment_enabled, 'discovery': deployment_discovery_enabled, 'credentials_id': deployment_credentials}

            self.deployments_list.append(deployment_dict)

            if self.print_deployments:
                for key, value in deployment_dict.items():
                    print(Fore.CYAN + key + ': ' + Fore.MAGENTA + value )
                print(Style.RESET_ALL)
                print(f'\n')
            
    print(f'Running the query for deployments under {alert_logic_cid} now.')

'''

'''
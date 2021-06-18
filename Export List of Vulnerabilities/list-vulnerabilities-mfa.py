'''
Author: Malcolm Palmer/Jesper Jurcenoks
Last Updated By: Robert VanOrman
Created on 5/4/20
Last Updated: 5/8/20 
Commandline: python3 list-vulnerabilities.py

Use Tacoma endpoint to pull a list of vulnerabilities and export it as a CSV report and save it to local disk.
'''

# Required Libraries
import json
import requests
import time
import gzip
import io

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
        'Accept-encoding': 'gzip'
    } 
else:
    print ('\nError: No credentials stored in the configuration file, to allow authentication against the API.\n')
    exit()

'''
# Parse response to get alert_logic_cid and AIMS token
response = token_response.json()
tacoma_headers = {
    'x-aims-auth-token': auth_token,
    'Accept-encoding': 'gzip'
}
alert_logic_cid = response['authentication']['account']['id']
'''
# Use token to request a list of available workbooks from Tacoma
get_workbooks_url = f'{global_url}/tacoma/v1/{alert_logic_cid}/workbooks'
workbooks_request = requests.get(get_workbooks_url, headers=headers)

# Pick a view by name from the list of available workbooks
report_params = {
#    'endpoint': global_url,
#    'alert_logic_cid': str(alert_logic_cid),
    'site_id': '',
    'workbook_id': '',
    'view_id': '',
}
workbooks_response = json.loads(workbooks_request.text)
for site in workbooks_response['sites']:
    for workbook in site['workbooks']:
        for view in workbook['views']:
            if view['name'] == target_view:
                report_params['site_id'] = site['id']
                global site_id
                site_id = report_params['site_id']
                print(f'site_id: {site_id}')
                report_params['workbook_id'] = workbook['id']
                global workbook_id
                workbook_id = report_params['workbook_id']
                print(f'workbook_id: {workbook_id}')
                report_params['view_id'] = view['id']
                global view_id
                view_id = report_params['view_id']
                print(f'view_id: {view_id}')

# Request the report as a CSV export
get_export_url = f'{global_url}/tacoma/v1/{alert_logic_cid}/sites/{site_id}/workbooks/{workbook_id}/views/{view_id}/export'
get_export_url = get_export_url.format(**report_params)
export_request = requests.get(get_export_url, headers=headers, stream=True)

# Deflate gzip-encoded response
uncompressed_data = gzip.GzipFile(fileobj=io.BytesIO(export_request.content))
'''
uncompressed_data = uncompressed_data.read()
uncompressed_data = uncompressed_data.decode('utf-8')
uncompressed_data = uncompressed_data.replace('\n', '\r\n')
print('The string starts here \n' + uncompressed_data[20000:25000])
'''
# Save the CSV file to disk
with open(csv_file_name, 'wb') as save_file:
    save_file.write(uncompressed_data.read())
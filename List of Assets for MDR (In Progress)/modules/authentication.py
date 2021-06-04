#!/usr/bin/python3 -u

#Wriiten for python 3.7.3

#Import Shared Content
from modules.shared_content import *

class Authenticate_User:
    def __init__(self, global_url, username, password, auth_header):
        self.global_url = global_url
        self.username = username
        self.password = password
        self.auth_header = auth_header


    # Function to get AIMS Token with the provided username and password
    def get_api_token(self):
        token_url = f'{self.global_url}aims/v1/authenticate'
        global auth_token
        #global auth_token_response
        # User credentials
        aims_user = self.username
        aims_pass = self.password
        # Ask the user for their MFA code and tidy JSON
        mfa_code = input('Please provide your MFA code: ')
        mfa_payload = {"mfa_code": mfa_code}
        mfa_payload = json.dumps(mfa_payload)
        mfa_payload=mfa_payload.replace("'",'"')

        # POST request to the URL using credentials. Load the response into auth_info then parse out the token
        auth_token_response = requests.post(token_url, mfa_payload, auth=(aims_user, aims_pass))

        if auth_token_response.status_code != 200:
            print(f'Error: Could not authenticate. Got the following response: {auth_token_response}\n')
            exit()

        auth_info = json.loads(auth_token_response.text)
        auth_token = auth_info['authentication']['token']

    # Function to validate the AIMS token was successfully generated, and that it has not expired
    def validate_token(self):
        validate_url = f'{self.global_url}aims/v1/token_info'
        headers = {'x-aims-auth-token': f'{auth_token}'}
        #global validate_info
        validate_response = requests.get(validate_url, headers=headers)
        validate_info = json.loads(validate_response.text)

        # Get current unix timestamp,make global for later
        #global current_time
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
    def authentication_header(self):
        if self.username != '' and self.password != '':
            self.get_api_token()
            self.validate_token()
            # Set header for all future API calls
            self.auth_header = {
                "x-aims-auth-token": f"{auth_token}",
                "content-type" : "application/json"
            }
            return self.auth_header

        else:
            print ('\nError: No credentials stored in the configuration file, to allow authentication against the API.\n')
            exit()
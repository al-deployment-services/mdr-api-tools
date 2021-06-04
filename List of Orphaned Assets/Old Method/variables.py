# Variables File

# URL for API interaction:
global_url = 'https://api.cloudinsight.alertlogic.com/'
sources_url = 'http://svc-lm3-api.denver.alertlogic.net:8080/'
'''
sources_url can be one of the following:
http://svc-lm3-api.denver.alertlogic.net:8080
http://svc-dc4a-uno-sources.dc4.alertlogic.net:8080
http://svc-npt-uno-sources.newport.alertlogic.net:8080
'''
# Login Credentials (username and password - be sure to escape characters as needed i.e. \' or \"):
username = ''
password = ''

# Account ID:
alert_logic_cid = ''

# Deployment ID:
deployment_id = ''

# Imported CSV File Name:
csv_import_file = 'search-results.csv'

# Exported CSV File Name:
csv_file_name = 'orphaned-assets.csv'
failed_sources_csv = 'failed-sources.csv'
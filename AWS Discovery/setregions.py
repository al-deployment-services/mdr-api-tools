#!python

# This script will update the discovery regions for all AWS
# deployments on the specified Alert Logic CID that are currently
# in error.

import sys
import almdrlib
import time

def usage():
    print(f'''
{sys.argv[0]} usage:
{sys.argv[0]} -c CID -r us-east-1,us-east-2 [other options]

Options:
    -c [CID]:  Alert Logic customer ID - https://console.account.alertlogic.com/#/support/home
    -r [list]:  Comma separated list of AWS regions
    -i:  Only include specified regions in discovery
    -x:  Exclude specified regions from discovery
    -e:  Apply Discovery regions to all AWS deployments in error
    -a:  Apply Discovery regions to all AWS deployments
    -d [AWSID]:  Apply Discovery regions to all AWS deployments
    -h:  This usage page

CID and Region list are required.    If no other options are specified,
this script will default to AWS deployments in error and 'include' mode.
''')

    sys.exit()

def getOptions():
    opts = {}

    # Default filter and type
    opts['filter'] = 'error'
    opts['type'] = 'include'
    
    # Loop through options
    i=1
    while i < len(sys.argv):
        if sys.argv[i] == '-h':
            usage()
        elif sys.argv[i] == '-c':
            i += 1
            opts['cid'] = sys.argv[i]
        elif sys.argv[i] == '-i':
            opts['type'] = 'include'
        elif sys.argv[i] == '-x':
            opts['type'] = 'exclude'
        elif sys.argv[i] == '-r':
            i += 1
            opts['regions'] = sys.argv[i]
        elif sys.argv[i] == '-a':
            opts['filter'] = 'all'
        elif sys.argv[i] == '-e':
            opts['filter'] = 'error'
        elif sys.argv[i] == '-d':
            i += 1
            opts['filter'] = sys.argv[i]
        else:
            usage()
        i += 1
    # Check to make sure we got a CID and regions
    if not opts['cid'] or not opts['regions']:
        print("Both CID and region list are required")
        usage()
    # print (f"{opts=}")
    return opts

# Create object w/ discovery scope feature for use in updating deployments
def scopeFeature(regions, inc="include"):
    feature = {}
    reg = []
    rlist = regions.split(',')
    for r in rlist:
        robj = {"type": "region", "name": r}
        reg.append(robj)
    feature['discovery'] = [{'scope': {inc: reg}}]
    #print(f"{feature}")
    return feature

# Get AWS deployments according to filter
#  Filter can be 'all', 'error', or a specific AWS account number
def getDeployments(cid, client, filter):
    res = client.list_deployments(account_id=cid)
    deps = []
    for d in res.json():
        #print("Deployment")
        #print(f"{d}")
        #print("")
        if d['platform']['type'] == 'aws':
            if filter == 'all':
                deps.append(d)
            elif filter == 'error' and d['status']['status'] == 'error':
                deps.append(d)
            elif d['platform']['id'] == filter:
                deps.append(d)
    return deps

# Update the given deployment with the selected discovery scope feature
def updateDeployment(cid, dep, feature, client):
    res = client.update_deployment(account_id=cid,
        deployment_id=dep['id'],
        version=dep['version'], features=feature)
    if res.status_code == 200:
        print(f"Deployment: {d['name']}")
        print(f"  - Result: Success")
    else:
        print(f"Deployment: {d['name']}")
        print(f"  - Result: Error:  {res.text}")
    exit

# Main logic
opts = getOptions()

# Build feature object based on command line
feature = scopeFeature(opts['regions'], opts['type'])

# Get an API client for deployments service
depClient = almdrlib.client("deployments")

# Get all AWS deployments in error
deps = getDeployments(opts['cid'], depClient, opts['filter'])

print(f"AWS deployments to update {len(deps)}")

# Loop through the deployments in error and update them with the discovery scope
for d in deps:
    updateDeployment(opts['cid'], d, feature, depClient)
    time.sleep(1)
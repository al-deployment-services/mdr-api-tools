#!python

# This script will update the discovery regions for all AWS
# deployments on the specified Alert Logic CID that are currently
# in error.

import sys
import almdrlib
import time

def usage():
    print(f"{sys.argv[0]} usage:")
    print(f"{sys.argv[0]} CID [-x|-i] us-east-1,us-east-2")
    print(f"")
    print(f"One of:")
    print(f" -x - Exclude listed regions from discovery")
    print(f" -i - Only include listed regions in discovery")
    print(f"")
    print(f"List of regions is comma separated")

    sys.exit()

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

# Get all AWS deployments currently in error
def getDeployments(cid, client):
    res = client.list_deployments(account_id=cid)
    errors = []
    for d in res.json():
        if d['platform']['type'] == 'aws':
            if d['status']['status'] == 'error':
                errors.append(d)
                #print("Deployment")
                #print(f"{d}")
                #print("")
    return errors

# Update the given deployment with the selected discovery scope feature
def updateDeployment(cid, dep, feature, client):
    res = client.update_deployment(account_id=cid,
        deployment_id=dep['id'],
        version=dep['version'], features=feature)
    print(f"Deployment: {d['name']} - Result = {res}")
    exit

# Main logic
# Check for correct number of arguments
if len(sys.argv) != 4:
    usage()

cid = sys.argv[1]

# Get the mode we will be using or print usage
if sys.argv[2] == '-x':
    mode='exclude'
elif sys.argv[2] == '-i':
    mode='include'
else:
    usage()

# Build feature object based on command line
feature = scopeFeature(sys.argv[3], mode)

# Get an API client for deployments service
depClient = almdrlib.client("deployments")

# Get all AWS deployments in error
errDep = getDeployments(cid, depClient)

print(f"AWS deployments in error {len(errDep)}")

# Loop through the deployments in error and update them with the discovery scope
for d in errDep:
    updateDeployment(cid, d, feature, depClient)
    time.sleep(1)
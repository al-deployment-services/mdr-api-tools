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

def getDeployments(cid):
    depClient = almdrlib.client("deployments")
    res = depClient.list_deployments(account_id=cid)
    errors = []
    for d in res.json():
        if d['platform']['type'] == 'aws':
            if d['status']['status'] == 'error':
                errors.append(d)
                #print("Deployment")
                #print(f"{d}")
                #print("")
    return errors

def updateDeployment(cid, dep, feature):
    print(f"{dep['id']=}")
    depClient = almdrlib.client("deployments")
    res = depClient.update_deployment(account_id=cid,
        deployment_id=dep['id'],
        version=dep['version'], features=feature)
    print(f"{res=}")
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

feature = scopeFeature(sys.argv[3], mode)

errDep = getDeployments(cid)

print(f"AWS deployments in error {len(errDep)}")

for d in errDep:
    updateDeployment(cid, d, feature)
    time.sleep(1)
This script is used to update AWS deployments to restrict regions used in the Alert Logic discovery process.   This is needed in cases where there are Service Control Policies in place to restrict which AWS regions are accessible, which is common in environments using Control Tower.

This script gives the option to either configure regions to be excluded from discovery or limit discovery to a specific set of included regions.
* Use the exclude option if single regions are being explictly blocked in AWS.   This ensures that when AWS adds new regions, they are automatically discovered.
* Use the include option where the available regions are being specified, like the Control Tower case, where additional regions being made available is done explicitly.   Include mode is selected by default

By default, only AWS deployments that are in error will be updated.

Once the allowed regions have been updated successfully, it may take up to 12 hours for the discovery process to complete.

Requirements:
-----
- Python 3.8+
- alertlogic-sdk-python

Setup:
-----
- Configure api keys for the cli usage:  <https://developer.alertlogic.com/cli/first-use.htm>
- Get Alert Logic customer ID from the support page in the console: <https://console.account.alertlogic.com/#/support/home>

Usage:  
-----
setregions.py -c [CID] -r [region1,region2]  
Options:  
-   -c [CID]:  Alert Logic customer ID - <https://console.account.alertlogic.com/#/support/home>
-   -r [list]:  Comma separated list of AWS regions
-   -i:  Only include specified regions in discovery
-   -x:  Exclude specified regions from discovery
-   -e:  Apply Discovery regions to all AWS deployments in error
-   -a:  Apply Discovery regions to all AWS deployments
-   -d [AWSID]:  Apply Discovery regions to all AWS deployments
-   -h:  This usage page

CID and Region list are required.    If no other options are specified, this script will default to AWS deployments in error and 'include' mode.

Example:  
`setregions.py -c 12345 -r us-east-1,us-east-2,us-west-3 -a -i`  
    - Set discovery on all AWS deployments in Alert Logic account 12345 to only discover resources in us-east-1, us-east-2, and us-west-3
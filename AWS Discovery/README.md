This script is used to update AWS deployments to restrict regions used in the Alert Logic discovery process.   This is needed in cases where there are Service Control Policies in place to restrict which AWS regions are accessible, which is common in environments using Control Tower.

This script gives the option to either configure regions to be excluded from discovery or limit discovery to a specific set of included regions.
* Use the exclude option if single regions are being explictly blocked in AWS.   This ensures that when AWS adds new regions, they are automatically discovered.
* Use the include option where the available regions are being specified, like the Control Tower case, where additional regions being made available is done explicitly.


Requirements:
Python 3.8+
alertlogic-sdk-python

Setup:
Configure api keys for the cli usage:  [https://developer.alertlogic.com/cli/first-use.htm]
Get Alert Logic customer ID from the support page in the console: [https://console.account.alertlogic.com/#/support/home]

Usage:
setregions.py [CustomerID] [-i|-x] region1,region2,region3
* -i  Include the specified regions
* -x  Exclude the specified regions from discovery
* Regions is a comma separated list

The current version of this script will update the discovery scope on all AWS deployments currently in error.

Example:
setregions.py 12345 -i us-east-1,us-east-2,us-west-3
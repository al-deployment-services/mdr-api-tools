# Automation Tools for Alert Logic MDR Platform using Python
This is a collection of python scripts that will allow you to automate tasks in the Alert Logic Console.

## Usage
### Bulk Agent Removal
This tool was desinged to integrate with the Alert Logic MDR API platform to clean out all agents in a Data Center Type deployment that have been uninstalled, though still show in the portal.

### Export List of Vulnerabilties 
This tool was designed to allow you to export the List of Vulnerabilities report from Alert Logic on a time interval, say, using a cron job.

### Import External IPs and FQDNs 
This tool was designed to allow you to mass import external IP addresses in single IP or up to /24 CIDR notation, as well as nass import Fully Qualified Domain Names to be scanned externally. There are also options to remove all external IPs or remove all external FQDNs. See options details below:

usage: external-assets-import.py [-h] [-add] [--delete_all_ips] [--delete_all_fqdns]

optional arguments:
  -h, --help            show this help message and exit
  -add, --add_ips_or_fqdns
                        upload the desired external IPs and FQDNs that are specified in the external-fqdns.csv and external-ips.csv files
  --delete_all_ips      delete all existing external IPs for the CID in the provided variables.py file
  --delete_all_fqdns    delete all existing external IPs for the CID in the provided variables.py file

Please do not upload the examples in the csv files.

### List of Assets for MDR (In Progress)
This tool was designed to export a list of all assets for a customer's account per deployment.

### List of Orphaned Assets
This too was designed to export a list of hosts that have agents on them and are calling back to Clyde to register, but their CIDR range does not exist in subnets or networks assets for the customer.

### List of Subnets per Network
This was designed to capture all of the subnet CIDR details that exist for each network in a customer's environment.

### List of Threat Agents in MDR
This tool was designed to export a list of Agents in the portal for a given Deployment ID. You can specify a network key from the Investigate > Topology page if you want to narrow the search further.

### Networks and Subnets Correlation (In Progress)
This was designed to figure out if all CIDR ranges are equal among Subnets and Networks for a customer. (i.e. are there CIDR ranges attached to the network that do not have a subnet specified for them, so the hosts will show up under default subnet?)
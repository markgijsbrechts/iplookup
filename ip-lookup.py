import os
import sys
import ipaddress
import requests
from pprint import pprint as pp

INFOBLOX_API_URL = os.environ.get('INFOBLOX_API_URL')
INFOBLOX_API_USER = os.environ.get('INFOBLOX_API_USER')
INFOBLOX_API_PASSWORD = os.environ.get('INFOBLOX_API_PASSWORD')
USAGE_MSG = """
 Usage:
    \t ip-lookup.py 192.168.1.1
    \t ip-lookup.py 192.168.0.0/16
    \t ip-lookup.py 192.168.0.0 255.255.0.0
    \t ip-lookup.py 192.168.0.0/255.255.0.0    
    """
CONFIG_MISSING_LINUX_MSG = """
 ### Error ###
    \t Please set the required environment variables first. 
    \t export INFOBLOX_API_URL=https://<URL>/wapi/v<version>/
    \t export INFOBLOX_API_USER=<api username>
    \t export INFOBLOX_API_PASSWORD=<api password>
    """

CONFIG_MISSING_WINDOWS_MSG = """
 ### Error ###
    \t Please set the required environment variables first. 
    \t set INFOBLOX_API_URL=https://<URL>/wapi/v<version>/
    \t set INFOBLOX_API_USER=<api username>
    \t set INFOBLOX_API_PASSWORD=<api password>
    """

def get_ip_info(ipv4address):
    urlparams = 'ipv4address?ip_address='
    url = INFOBLOX_API_URL + urlparams + str(ipv4address)
    r = requests.get(url, auth=(INFOBLOX_API_USER, INFOBLOX_API_PASSWORD))
    if (r.status_code == 200):
        pp(r.json())
    else:
        print('Status code {} - IP lookup failed'.format(r.status_code))
        return None

def get_network_info(ipv4network):
    urlparams = 'network?network='
    url = INFOBLOX_API_URL + urlparams + str(ipv4network)
    r = requests.get(url, auth=(INFOBLOX_API_USER, INFOBLOX_API_PASSWORD))
    if (r.status_code == 200):
        if (len(r.json()) > 0): # If result list not empty, network found in Infoblox
            pp(r.json())
        else:
            if ipv4network.prefixlen > 7: # Do not lookup prefixes smaller than /8, avoids infinite loop on 0.0.0.0/0
                get_network_info(ipv4network.supernet()) # If result list empty, recursively retrieve the supernet
    else:
        print('Status code {} - IP lookup failed'.format(r.status_code))
        return None

def get_network_from_ip(ipv4address):
    urlparams = 'ipv4address?ip_address='
    url = INFOBLOX_API_URL + urlparams + str(ipv4address)
    r = requests.get(url, auth=(INFOBLOX_API_USER, INFOBLOX_API_PASSWORD))
    if (r.status_code == 200):
        return r.json()[0]['network']
    else:
        print('Status code {} - Network lookup for IP {} failed'.format(r.status_code, ipv4address))
        return None


def main():
    # Check required config variables are set
    if None in (INFOBLOX_API_URL, INFOBLOX_API_USER, INFOBLOX_API_PASSWORD):
        if os.name == 'nt':
            print(CONFIG_MISSING_WINDOWS_MSG)
        else:
            print(CONFIG_MISSING_LINUX_MSG)
        sys.exit()

    # Initialize values, they will be set depending on the arguments given
    ip = None
    prefix = None

    # Parse command-line arguments
    if (len(sys.argv) < 2):
        print('\n ### Please specify an IP address or subnet as arguments. ###')
        print(USAGE_MSG)
    elif (len(sys.argv) == 2 and '/' in sys.argv[1]): # x.x.x.x/xx
            try:
                prefix = ipaddress.IPv4Network(sys.argv[1])
            except:
                print('### Error: not a valid network address ###')
    elif (len(sys.argv) == 2 and '/' not in sys.argv[1]): # x.x.x.x
            try:
                ip = ipaddress.IPv4Address(sys.argv[1])
            except:
                print('### Error: not a valid IP address ###')
    elif (len(sys.argv) == 3): # x.x.x.x x.x.x.x
        if(sys.argv[2].startswith('255.')):
            try:
                prefix = ipaddress.IPv4Network(sys.argv[1] + '/' + sys.argv[2])
            except:
                print('### Error: not a valid network address ###')        
    else:
        print('\n ### Error: too many arguments given. ###')
        print(USAGE_MSG)

    # Retrieve info about IP or network depending on user provided command-line argument
    if(ip):
        print('\n### IP info ###\n')
        get_ip_info(ip)
        network = get_network_from_ip(ip)
        print('\n\n### Network info ###\n')
        get_network_info(network)
    elif(prefix):
        print('\n\n### Network info ###\n')
        get_network_info(prefix) 

if __name__ == "__main__":
    main()

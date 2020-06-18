#!/usr/bin/python

# Simple script to import Loxone UDP logs into InfluxDB

# hostname and port of InfluxDB http API
host = '127.0.0.1'
port = 8086
# InfluxDB database name
dbname = 'loxone'
# InfluxDB login credentials (optional, specify if you enabled authentication)
dbuser = 'some_user'
dbuser_code = 'some_password'
# local IP and port where the script is listening for UDP packets from Loxone
localIP = '192.168.1.22'
localPort = 2222


import socket
import json
import argparse
import re
from influxdb import InfluxDBClient
from datetime import datetime
from dateutil import tz

# Parse received message
# Example string: "'2017-10-19 11:01:38;Temperatuur Eetruimte;21.7\\xc2\\xb0\\r\\n'"
# ** TO DO ** Need to add checks in case something goes wrong
#
def ParseLogData (data, from_zone, to_zone, debug=False):
	if debug == True:
		print ('-------------------------------------------------')
		print (data)
	EndTimestamp  = data.find(b';')
	EndName       = data.find(b';', EndTimestamp+1)
	EndCustName = data.find(b':', EndName+1)
	if EndCustName < 0:		# -1 means not found
		EndCustName = EndName
        EndValue      = data.find(b';', EndCustName+1)
        if EndValue > 0:
                EndTag1 = data.find(b';', EndValue+1)
        else:
		EndTag1 = 0
        if EndTag1 > 0:
		EndTag2 = data.find(b';', EndTag1+1)
	else:
		EndTag2 = 0
        if EndTag2 > 0:
                EndTag3 = data.find(b';', EndTag2+1)
	else:
                EndTag3 = 0
	numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
	rx = re.compile(numeric_const_pattern, re.VERBOSE)
	ParsedData = {}
	
	# Timestamp Extraction
	ParsedData['TimeStamp']=data[0:EndTimestamp]
	ParsedData['TimeStamp']=ParsedData['TimeStamp'].replace(b' ',b'T')+b'Z'
	# Timezone conversion to UTC
	local = datetime.strptime(ParsedData['TimeStamp'].decode('utf-8'), b'%Y-%m-%dT%H:%M:%SZ'.decode('utf-8'))
	local = local.replace(tzinfo=from_zone)
	UTC = local.astimezone(to_zone)
	ParsedData['TimeStamp'] = UTC.strftime('%Y-%m-%dT%H:%M:%SZ')
	
	# Name Extraction
	ParsedData['Name']=data[EndTimestamp+1:EndName]
	
        # Custom Name Extraction
        if EndCustName != EndName:
		ParsedData['Name']=data[EndName+1:EndCustName]

	# Value Extraction
	ParsedData['Value']=rx.findall(data[EndCustName+1:EndValue].decode('utf-8'))[0]
	
        #Tag_1 Extraction
        ParsedData['Tag_1']=data[EndValue+1:EndTag1].rstrip()

        #Tag_2 Extraction
	ParsedData['Tag_2']=data[EndTag1+1:EndTag2].rstrip()

        #Tag_3 Extraction
	ParsedData['Tag_3']=data[EndTag2+1:EndTag3].rstrip()

	#Create Json body for Influx
	json_body = [
		{
			"measurement": ParsedData['Name'].decode('utf-8'),
			"tags": {
				"Tag_1": ParsedData['Tag_1'].decode('utf-8'),
                                "Tag_2": ParsedData['Tag_2'].decode('utf-8'),
                                "Tag_3": ParsedData['Tag_3'].decode('utf-8'),
				"Source": "Loxone",
			},
			"time": ParsedData['TimeStamp'],   #  "2009-11-10T23:00:00Z",
			"fields": {
				"value": float(ParsedData['Value'])
			}
		}
]                                    
	if debug == True:
		print (json.dumps(json_body, indent=4))
		
	return json_body;

def main(host, port, debug=False):
    ## """Instantiate a connection to the InfluxDB."""
    client = InfluxDBClient(host, port, dbuser, dbuser_code, dbname)
	
    # get TZ info
    to_zone = tz.tzutc()
    from_zone = tz.tzlocal()
    
    # A UDP server
    # Set up a UDP server
    UDPSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    # Listen on port 21567
    # (to all IP addresses on this system)
    listen_addr = (localIP,localPort)
    UDPSock.bind(listen_addr)

    # Report on all data packets received and
    # where they came from in each case (as this is
    # UDP, each may be from a different source and it's
    # up to the server to sort this out!)
    while True:
        data,addr = UDPSock.recvfrom(1024)
        json_body_log=ParseLogData(data,from_zone, to_zone,debug)
		# Write to influx DB
        client.write_points(json_body_log)

def parse_args():
    """Parse the args."""
    parser = argparse.ArgumentParser(
        add_help=False, description='Simple Loxone to InfluxDB script')
    parser.add_argument('-h', '--host', type=str, required=False,
                        default=host,
                        help='hostname of InfluxDB http API')
    parser.add_argument('-p', '--port', type=int, required=False, default=port,
                        help='port of InfluxDB http API')
    parser.add_argument('-d', '--debug', action="store_true",
                        help='debug code')
    parser.add_argument('-?', '--help', action='help',
    			help='show this help message and exit')
    return parser.parse_args()



if __name__ == '__main__':
    args = parse_args()
    main(host=args.host, port=args.port, debug=args.debug)


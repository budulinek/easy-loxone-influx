# simple-loxone-influx
Simple Loxone to InfluxDB script

## What?

This scripts listens for Loxone statistics sent via UDP log and inserts the data into InfluxDB. Once in InflixDB, these statistics can be visualized by Grafana.

It is very easy to setup and use. While the script requires manual installation, the subsequent configuration of individual measurements and statistics is done through Loxone Config.

All credits go to Jan De Bock. This is just a polished version of his original script: https://groups.google.com/forum/#!topic/loxone-english/ijOUU8FHMKA

## How?

### 1. Make sure you have Python and other required packages
```
apt update
apt install python python-influxdb libfile-slurp-perl libfile-touch-perl libjson-perl libhttp-tiny-perl
```
### 2. Download and configure the script
Configuration at the beginning of the script:
```
# hostname and port of InfluxDB http API
host = '127.0.0.1'
port = 8086
# InfluxDB database name
dbname = 'loxone'
# InfluxDB login credentials (optional, specify if you enabled authentication)
dbuser = 'some_user'
dbuser_code = 'some_password'
# local IP and port where the script is listening for UDP packets from Loxone
localIP = '192.168.1.222'
localPort = 2222
```
### 3. Run the script
```
usage: Loxone2InfluxDB.py [-h HOST] [-p PORT] [-d] [-?]

Simple Loxone to InfluxDB script

optional arguments:
  -h HOST, --host HOST  hostname of InfluxDB http API
  -p PORT, --port PORT  port of InfluxDB http API
  -d, --debug           debug code
  -?, --help            show this help message and exit
```
* Use debug for testing.
* If everything works as expected, create a systemd service  following this tutorial: https://github.com/torfsen/python-systemd-tutorial
* Remember - the script is not failsafe. It will simply crash if it receives data in wrong format. So you need systemd service with both autostart and restart after failure.

### 4. Configure UDP Logger in Loxone
Loxone Config > Miniserver > Messages > Create new Logger
`Address of logger /dev/udp/192.168.1.222/2222`
(insert IP and port where the script is listening for UDP packets) 

![01](/pics/01.png)

### 5. Assign logger to a perifery or block in Loxone
All periferies (inputs and outputs) and most block allow you to assign a logger to them. Just search for `Logging/Mail/Call/Track` in the properties tab. Also set the `Message when ON/analogue changes` and `Message when OFF`

![02](/pics/02.png)

That's it! There is no need to mess with UUIDs, logins, users and permissions. If you need to log more data, simply repeat step 5 for other inputs,, outputs or blocks. Your measurements will appear in InfluxDB / Grafana under the same `Name` (or `Description`) you gave them iin Loxone Config.

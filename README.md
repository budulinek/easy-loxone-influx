# easy-loxone-influx



## What?

This scripts listens for Loxone statistics sent via UDP log and inserts the data into InfluxDB. Once stored InfluxDB, these statistics can be visualized by Grafana.

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
* Remember - the script is not failsafe. It will simply crash if it receives data in wrong format. So you really need systemd service with both autostart and restart after failure.

### 4. Configure UDP Logger in Loxone
Loxone Config > Miniserver > Messages > Create new Logger
`Address of logger /dev/udp/192.168.1.222/2222`
(insert IP and port where the script is listening for UDP packets) 

![01](/pics/01.png)

### 5. Assign logger to a perifery or block in Loxone
All periferies (inputs and outputs) and most block allow you to assign a logger to them. Just look for `Logging/Mail/Call/Track` in the properties tab and assign your newly created logger here. Also set the value in `Message when ON/analogue changes` and `Message when OFF`.

![02](/pics/02.png)

That's it! There is no need to mess with UUIDs, logins, users and permissions. If you need to log more data, simply repeat step 5 for other inputs, outputs or blocks. Within Loxone, under the perifery tree you will have a nice overview of all items sent via your InfluxDB logger. Within InfluxDB / Grafana, you will find your measurements under the `Name` (or `Description`) specified in Loxone Config.

### 6. Custom measurement name (optional)
If you want to give your measurement in InfluxDB/Grafana some custom name (different from `Name` you use in Loxone), just edit `Message when ON/analogue changes` and `Message when OFF`. Add your custom name, followed by colon before value, for example

![03](/pics/03.png)

### 7. Custom tags (optional)
You can also add up to three custom tags to your measurements which will be shown in InfluxDB/Grafana as Tag_1, Tag_2 and Tag_3. Since Loxone UDP logger does not record Room or Category, you can use custom tags to add them manually. Again, edit `Message when ON/analogue changes` and `Message when OFF`. Add your tags after value, separated by semicolon. You can for example set Tag_1 and Tag_2:

`<v.1>;Lights;Kitchen`

or just Tag_3:

`<v.1>;;;My house`

### 8. Periodic logging
UDP logs are sent whenever the perifery (input or output) or block change their value. This is fine for analog values which change frequently. However, for some critical digital values (or analog values with infrequent changes) we need periodic checks in order to make our readings more reliable. Loxone does not offer periodic logging, but we can use a workaround with `Analogue Memory` and `Pulse Generator`. Grab your InfluxDB logger and build the following schema. Set the period in pulse generator and the attached logger will send the UDP log periodically, even if the digital or analog value attached to the memory does not change.
However, there is one problem with this solution: Loxone will use the name of the logger (in our case "InfluxDB") as a measurement name in the UDP log message. Therefore, you MUST use custom measurement name (see step 6):

![04](/pics/04.png)

If your pulse generator is really fast, you will need to decrease `Minimum time interval`. Since we are configuring everything inside Loxone Config, you can even change the logging period dynamically, simply by attaching some program to `TL` input (parameter) of the pulse generator.

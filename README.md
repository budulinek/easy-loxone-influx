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

### 5. Assign logger to a periphery or block in Loxone
All peripheries (inputs and outputs) and most block allow you to assign a logger to them. Just look for `Logging/Mail/Call/Track` in the properties tab and assign your newly created logger here. Also set the value in `Message when ON/analogue changes` and `Message when OFF`.

![02](/pics/02.png)

That's it! There is no need to mess with UUIDs, users and permissions. Within InfluxDB / Grafana, you will find your measurements under the `Name` (or `Description`) specified in Loxone Config.

Now go ahead and add few more measurements! There are actually 2 ways how to do that:
1. Edit the `Logging/Mail/Call/Track` section in the properties tab of your periphery (input/output) or a block. This is a prefered solution which we use here in step 5.
2. Drag and drop the logger into your program (see step 8). 

If you have a lot of measurements assigned to a logger, it is a good idea to double check the names, aliases and tags of your measurements. Find your InfluxDB logger under the periphery tree, highlight all items attached to the logger and then hit `Edit shared properties...` in the properties tab.  

![06](/pics/06.png)

Here you will get a nice overview of all names (see columns `Name` and `Description`), aliases and tags (see columns `Message when ON/analogue changes` and `Message when Off`) of all measurements sent to InfluxDB. You can edit them. Make sure that each measurement is uniquely identified. Usually this is done through unique `Name` or `Description`, but if you "Drag and drop" the logger into your program, you must set custom alias.

### 6. Custom alias (optional)
If you want to give your measurement in InfluxDB/Grafana some custom name (different from `Name` or `Description` you use in Loxone), just edit `Message when ON/analogue changes` and `Message when OFF`. Add your alias (followed by colon) before value, for example

![03](/pics/03.png)

### 7. Custom tags (optional)
You can also add up to three custom tags to your measurements which will be shown in InfluxDB/Grafana as Tag_1, Tag_2 and Tag_3. Since Loxone UDP logger does not record Room or Category, you can use custom tags to add them manually. Again, edit `Message when ON/analogue changes` and `Message when OFF`. Add your tags after value, separated by semicolon. You can for example set Tag_1 and Tag_2:

`<v.1>;Lights;Kitchen`

or just Tag_3:

`<v.1>;;;My house`

### 8. Periodic logging
UDP logs are sent whenever the perifery (input or output) or block change their value. This is fine for analog values which change frequently. However, for some critical digital values (or analog values with infrequent changes) we need periodic checks in order to make our readings more reliable. Loxone does not offer periodic logging, but we can use a workaround with `Analogue Memory` and `Pulse Generator`. Grab your InfluxDB logger and build the following schema. Set the period in pulse generator and the attached logger will send the UDP log periodically, even if the digital or analog value attached to the memory does not change.
However, there is one problem with this solution: Loxone will use the name of the logger (in our case "InfluxDB") as a measurement name in the UDP log message. Therefore, you MUST use alias in order to assign a unique name to your measurement (see step 6):

![04](/pics/04a.png)

If your pulse generator is really fast, you will need to decrease `Minimum time interval`. 

Since we are configuring everything inside Loxone Config, you can even change the logging period dynamically. In the example above, we can for example set the loging period down to 10s and disable the pulse generator when the front door is closed. Or we can attach a more sofisticated program to the `TL` input (parameter) of the pulse generator: set the pulse period to 1 hour when the front door is closed and 10s when the door is open. With this setup, you will of course receive not only the scheduled UDP message, but also the UDP message on value change (door closed or open).

### 9. ... and some more advanced stuff for the brave ones ...
The syntax of the UDP log message parsed by my python script looks like this:

`<timestamp>;<measurement_name>;<alias(optional)>:<value>;<tag_1(optional)>;<tag_2(optional)>;<tag_3(optional)>`

Timestamp is always set by Loxone. Measurement name is determined by Loxone, based on `Name` or `Description` in the properties of your periphery. Then we can manually set an alias, overriding the original measurement name (see step 6). Value is set dynamically, using the built-in syntax of the Loxone Config (for example `<v.1>` - see step 5). Then we can manually set tags (see step 7). 

But Loxone Config actually allows you to build the whole UDP log message dynamically (with the sole exception of the timestamp), through the `Status` block. Each `Status` block has 4 inputs (AI1 - AI4) which accept digital, analog but also text data. Have a look at this configuration of the `Status` block (be careful about colons and semicolons):

![05](/pics/05.png)

The config means that AI1 will be used as "original" measurement name, AI2 is an alias  (overriding original name), AI3 is parsed as value and anything sent via AI4 (digital/analog/textual data) is parsed as Tag_1. Wondering how you set Tag_2 and Tag_3? No problem, `Status` block has a text output (`TQ`), so you can chain them. Link as many `Status` block as you want. Then assign an InfluxDB logger to the last `Status` block in the chain. 

In addition, you can set different `Status-text` for different combinations of conditions. So the composition of the UDP message will depend in the value of the inputs A1-A4 (you can use this feature to compose your own error messages).

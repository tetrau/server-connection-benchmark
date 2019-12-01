# server-connection-benchmark
![screenshot](https://raw.githubusercontent.com/tetrau/server-connection-benchmark/master/doc/img/screenshot.png)

server-connection-benchmark or `scb` is a server connection benchmark tool
written in python.

Have a 24/7 running server is supper useful to run daemon tasks, sync and backup
your files and many other jobs. A VPS is a very balanced and economical choice
for a server. But with so many VPS vendors and for each vendor there are so many
datacenters in different regions. If you choose the wrong vendor and datacenter,
especially if you have a bad network like me, you will have a very unpleasant
experience. Like `Enter ~ .` every five minutes to kill the unresponsive ssh
session. Or wait for a loooong time for scb to complete.

scb comes to rescue! scb can generate an easy-to-understand interactive
visualized report of the network connection condition between you and the
datacenters, distribution over time-of-day, which will help you choose wisely.

## Before You Use
When you run scb and see some bad results from certain VPS servers, in most
cases, that does not mean the vendor provides a poor quality server or
something. It's most likely to be your local ISP's fault or the distance between
the datacenter and your computer. The purpose of this project is to find the
best server that suits your network condition, not to find "the best" server. It
only tests the network connection between the server and your computer. It's
incapable of evaluating the server's general network performance.

## Quick Start
0. You need python3 [installed](https://www.python.org/downloads/) in your
system.
1. Download the latest version of [scb](https://github.com/tetrau/server-connection-benchmark/releases/latest/download/scb).
2. Choose and download a target server list file
[here](https://github.com/tetrau/server-connection-benchmark/tree/master/servers), 
it ends with a `.json` extension.
3. Open a terminal and go to where you save your `scb` and server list file.
4. Type command: 
For macOS/Linux:
`python3 scb -s servers.xxx.json -o report.html` 
For Windows:
 `python scb -s servers.xxx.json -o report.html`
5. The test will keep running and a `report.html` will be created after the
first batch finished, which will also be continuingly updated when the following
test batches completed, you can open it with any modern web browser (Firefox,
Chrome, Safari, Edge, etc.).

## Advance Usage
### Create your own target server list file
A target server list file is a simple JSON file contains an array of server
object. A server object is something like this.
```JOSN
{
    "vendor": "vendor name",
    "location": "physical location of the server",
    "ping": "host name or ip address for ping test",
    "download": "HTTP/HTTPS url for download test, it should refer to a large enough file"
}
```
If you are writing a server list file for your own, vendor and location values
can be anything, just make sure the (vendor, location) pair is unique. It will
be used as the unique identifier for server.

You can find some examples [here](https://github.com/tetrau/server-connection-benchmark/tree/master/servers)

### Command line arguments and the Duration of Each Benchmark Test Batch
Command Line argument `--ping-chunk PING_CHUNK` (default value: 8) decides how
many ping tests run in parallel. `-pc/--ping-count PING_COUNT` (default value:
100) decides how many ICMP packets should be sent in a single ping test to one
server. Reduce `PING_COUNT` will shorten the duration of each ping test, but it
will also decrease the accuracy of ping test. `-dt/--download-timeout
DOWNLOAD_TIMEOUT` (default value: 45 seconds) set a limit on the duration of
each bandwidth test, when bandwidth test exceeds `DOWNLOAD_TIMEOUT`, the
bandwidth test will be terminated, and calculate the bandwidth using what's
already received. Reduce `DOWNLOAD_TIMEOUT` will also decrease the accuracy of
the bandwidth test.

Below is how one benchmark test batch is organized.

```
+------------------------------------+-----------------------------------------------+
|                                    |  number of ping test running at the same time |
|              Duration              |  is decided by PING_CHUNK. In this case, 3.   |          
+------------------------------------+---------------+---------------+---------------+
|  <= max(ping_test.[0-2].duration)  |  ping_test.0  |  ping_test.1  |  ping_test.2  |
+------------------------------------+---------------+---------------+---------------+
|  <= max(ping_test.[3-4].duration)  |  ping_test.3  |  ping_test.4  |               |
+------------------------------------+---------------+---------------+---------------+ +
|         <= DOWNLOAD_TIMEOUT        |               bandwidth_test.0                | |
+------------------------------------+-----------------------------------------------+ Bandwidth
|         <= DOWNLOAD_TIMEOUT        |               bandwidth_test.1                | tests
+------------------------------------+-----------------------------------------------+ are
|         <= DOWNLOAD_TIMEOUT        |               bandwidth_test.3                | executed
+------------------------------------+-----------------------------------------------+ in
|         <= DOWNLOAD_TIMEOUT        |               bandwidth_test.4                | serial
+------------------------------------+-----------------------------------------------+ |
|         <= DOWNLOAD_TIMEOUT        |               bandwidth_test.5                | |
+------------------------------------+-----------------------------------------------+ +
```
The estimated duration of each benchmark test batch can be calculated by the
following formula.
```
duration <= ceil(N / PING_CHUNK) * max_ping_test_duration + N * DOWNLOAD_TIMEOUT
```
`N` is the number of target servers. Based on my test, ping test with 100 ICMP
packets, in most cases, should take no more than 2 minutes. With all this, you
can estimate the duration of each batch with your configuration.

**Why is this important** If one batch could not finish before the next batch's
time window, the next batch will be canceled. So, configure the arguments and
number of servers carefully, and make sure the duration of each batch less than
the interval between each batch (`-e/--every EVERY`, the default value is 30
minutes).

## Command Line Interface
```
usage: scb [-h] [-o OUTPUT] [-s SERVERS] [-r RESUME_FROM]
           [--render | --extract | --peek] [-i INPUT] [-e EVERY]
           [-pc PING_COUNT] [--ping-chunk PING_CHUNK] [-dt DOWNLOAD_TIMEOUT]
           [--json] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -s SERVERS, --servers SERVERS
                        A JSON file contains the target servers. The JSONfile
                        should contain a array of server objects. A server
                        object must have four fields. "vendor": the vendor of
                        the server, "location": the location of the server,
                        vendorand location combined should be unique pair.
                        "ping": the host name of the server used for ping
                        test."download": the download url (HTTP/HTTPSS) for
                        bandwidth test.
  -r RESUME_FROM, --resume-from RESUME_FROM
                        Resume from the specify report file, in another world,
                        append this run's result to the old report.
  --render              Render report data in json format to html file.
  --extract             Extract report data from html file to json format.
  --peek                Start a single test for each individual server
                        immediately, create a report and exit.
  -i INPUT, --input INPUT
                        Set the input file path, use a single hyphen for
                        stdin. Used with --render and --extract
  -e EVERY, --every EVERY
                        Set the minimal interval in seconds between two
                        benchmark batch, highly recommend use a divisor of 24
                        hours (5min, 10min, 15min, 30min, 1h, 1.5h, etc.)
                        (default: 1800)
  -pc PING_COUNT, --ping-count PING_COUNT
                        How many ping packet should be send in one ping test
                        to a server. (default: 100)
  --ping-chunk PING_CHUNK
                        The maximum number of concurrent ping test. (default:
                        8)
  -dt DOWNLOAD_TIMEOUT, --download-timeout DOWNLOAD_TIMEOUT
                        Specify a timeout in seconds for bandwidth test. If
                        the download does not finished in timeout seconds, it
                        will be terminated and use what's already received to
                        calculate the bandwidth. (default: 45)
  --json                Change the report output format to JSON.
  -v, --version         Show the version number

required arguments:
  -o OUTPUT, --output OUTPUT
                        Output file path, use a single hyphen for stdout.
```

## Build Guide
scb requires npm and python3 to build.

To build scb:
```
git clone https://github.com/tetrau/server-connection-benchmark.git
cd ./server-connection-benchmark/scb_js
npm install
cd ..
python3 ./build.py
```

And you can find your brand new `scb` in `./dist`.
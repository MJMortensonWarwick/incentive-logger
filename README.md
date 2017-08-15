# Incentive Logger

## What is This?
Automation. I bike to work and we have a lovely incentive program at OHSU...but I sometimes forget to log my incentive.  

## Overview

This tool is used to log your bike commute to OHSU each day. Tool features include:

* Commute trip customization
* Automatic background authentication / login with OSX Keychain (no hardcoded passwords)
* Wifi network detection with OSX Airport – only log trips when on an OHSU network
* Customizable delay mechanism to limit requests to once per day
* Only logs trips on weekdays
* User agent string randomization
* Logging of tool behavior
* Scheduling is managed through CRON

## Setup

To set up this utility, first install the Python requests library:
    > pip3 install requests

Next, log into the bike incentive web portal with Safari and click remember password when you log in 
(www.ohsu.edu/parking/bikesite/index.cfm).

Initially, Mac OSX will prompt you to grant the built-in OS X Security commandline tool access to OS X
Keychain. Click 'Always Allow' so you don't have to click 'Allow' each time the script runs. 

Security Note: Doing the above allows this script to load your password into memory without having to
hardcode it anywhere. It also sends all request using the https protocol by default. It can be set to 
http, but this is not recommended, and is likely disallowed by OHSU servers anyway. 

To configure the tool, see config variables in config/config.json. Below are the variable definitions:

    VARIABLE             DESCRIPTION
    username             String. Your username to login
    hours_delay          Integer. The number of hours to prevent requests after a successful trip log
    url                  String. The incentive log url
    override             Boolean. Force the tool to attempt a trip log
    valid_ssids          Array. A list of valid wifi network SSID's (e.g. HideYoKidsHideYoWiFi)
    airport_path         String. The Mac OSX system path to airport
    log_filepath         String. Log filepath
    log_level            String. Log verbosity, acceptable values include "INFO", "DEBUG", "WARNING", "CRITICAL", "ERROR" and "NOTSET"
    default_useragent    String. Default browser useragent, only used if randomize_useragent is set to false
    randomize_useragent  Boolean. Randomize user agent with config/useragent.json (this may prevent the server ignoring requests)
    othermodes           Array. Form field – a list of other modes of transportation that are used on your commute
    destinations         Array. Form field – a list to select a detination that is biked to

    INTERNAL VARIABLE    DESCRIPTION
    last_success         Float. Timestamp representation of last successful trip log (do not change this)

To setup the details of your commute, scroll down to line 158 in `src/main.py` (see comment).
 
To ensure the tool is working as expected, it's recommended that your first run is not scheduled via
CRON, to run it:

    > python3 /path/to/repo/src/main.py

## Scheduling

To setup and manage scheduling of this script, here are some helpful terminal commands:

    # Allow crontab to execute this script (required for this to work)
    chmod u+x path/to/this/repo/src/main.py

    # Open crontab in editing view using your terminals default editor
    > crontab -e 

    # Edit the file to call this script (here, every 30 minutes, see this nice explanation for 
    # scheduling: https://stackoverflow.com/a/11775112/2206251)
    > */30 * * * * /usr/local/bin/python3 path/to/this/repo/src/main.py

    # To check saved cron jobs
    > crontab -l

    # To check crontab history (use whatever editor you prefer):
    vim /var/mail/$USER

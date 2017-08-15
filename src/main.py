#!/usr/bin/env python3

"""
-------------------------------------------------------------------------------------------------------
Automagically Log Your Bike Trip When You're Logged Onto the Secure Network - Never Miss the Incentive.
-------------------------------------------------------------------------------------------------------

=======================================================================================================

The MIT License (MIT)

Copyright (c) Greenstick <benacordier@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

=======================================================================================================

SETUP

To set up this utility, first install the Python requests library:

	> pip3 install requests

Next, log into the bike incentive web portal with Safari and click remember password when you log in 
(www.ohsu.edu/parking/bikesite/index.cfm).

Initially, Mac OSX will prompt you to grant the built-in OS X Security commandline tool access to OS X
Keychain. Click 'Always Allow' so you don't have to click 'Allow' each time the script runs. 

Security Note: Doing the above allows this script to load your password into memory without having to
hardcode it anywhere. It also sends all request using the https protocol by default. It can be set to 
http, but this is not recommended, any is likely disallowed by our servers. 

To configure the tool, see config variables in config/config.json. Below are the variable definitions:

VARIABLE 			TYPE		DESCRIPTION
username 			string 		– Your username to login
hours_delay 		integer 	– The number of hours to prevent requests after a successful trip log
url 				string 		– The incentive log url
override 			boolean 	– Force the tool to attempt a trip log
valid_ssids  		array		– A list of valid wifi network SSID's (e.g. HideYoKidsHideYoWiFi)
airport_path 		string		– The Mac OSX system path to airport
log_filepath 		string 		- Log filepath
log_level 			string		– Log verbosity, acceptable values include "INFO", "DEBUG", "WARNING", "CRITICAL", "ERROR" and "NOTSET"
default_useragent	string 		– Default browser useragent, only used if randomize_useragent is set to false
randomize_useragent boolean 	– Randomize user agent with config/useragent.json (this may prevent the server ignoring requests)
othermodes 			array 		– Form field – a list of other modes of transportation that are used on your commute
destinations 		array 		– Form field – a list to select a detination that is biked to
last_success 		float 		– Timestamp representation of last successful trip log (do not change this)

To setup the details of your commute, scroll down in this file to line 158 (see comment)

SCHEDULING

To setup and manage scheduling of this script, here are some helpful terminal commands:

	# Allow crontab to execute this script (required for this to work)
	chmod u+x path/to/this/repo/incentive-logger/main.py

	# Open crontab in editing view using your terminals default editor
	> crontab -e 

	# Edit the file to call this script (here, every 30 minutes, see this nice explanation for 
	# scheduling: https://stackoverflow.com/a/11775112/2206251)
	> */30 * * * * /usr/local/bin/python3 path/to/this/repo/incentive-logger/main.py

	# To check saved cron jobs
	> crontab -l

	# To check crontab history (use whatever editor you prefer):
	vim /var/mail/$USER

##### DEVELOPMENT #####
*/1 * * * * /usr/local/bin/python3 /Users/Benjamin/Sites/tools/incentive-logger/main.py

=======================================================================================================

"""

#
# Imports
#

from collections 	import OrderedDict
from urllib.parse 	import urlencode
from lxml 			import html
import json 		as JSON
import subprocess 	as Subprocess
import os 			as OS
import sys 			as Sys
import datetime 	as Datetime
import logging 		as Logging
import requests 	as Requests
import random 		as Random
import re 			as Rgx

if __name__ == "__main__":

	# If It's The Weekend, Exit
	if Datetime.datetime.today().weekday() > 4:
		exit()

	# 
	# Load Config & Setup
	# 

	# Load Config File
	with open("../config/config.json") as file:
		config = JSON.load(file)

	# User Settings
	username 		= config["username"]
	override 		= config["override"]
	# Delay Between Attempts (14 Hours After Last Successful Log)
	delay 			= 60 * 60 * config["hours_delay"]
	# Network Settings
	airportPath 	= config["airport_path"]
	validSSIDs		= config["valid_ssids"]
	# Website Settings
	url 			= config["url"]
	protocol 		= config["protocol"]
	# Logging
	logDir 			= config["log_filepath"]
	logLevel 		= config["log_level"]
	# Trip Data – Destination Options
	destinations 	= config["destinations"]
	# Trip Data – Modes of Transportation Used Options
	othermodes 		= config["othermodes"]
	# User Agent Settings
	defUserAgent 	= config["default_useragent"]
	randUserAgent 	= config["randomize_useragent"]
	# Datetime – Time of Last Successful Trip Log - Default to None if Unavailable
	lastSuccess 	= config["last_success"] if int(config["last_success"]) > 0 else None
	# Datetime – Current Datetime
	currentDatetime = Datetime.datetime.now()

	# 
	# Customize Trip Details Below
	# 

	# Populate Post Data
	tripDetails 				= OrderedDict()
	tripDetails["trip-log"] 	= 1 				# Hidden Form Parameter – Leave Value as 1
	tripDetails["mileage"] 		= 6.0				# Distance Biked in Miles
	tripDetails["destination"]  = destinations[0] 	# Select 'Marquam Hill' (index 0)
	tripDetails["othermode"] 	= othermodes[0] 	# Select 'Tram' (index 0)

	# Set Useragent
	if randUserAgent:
		# Open Useragent Names File
		with open("../config/useragent.json") as file:
			useragent 		= JSON.load(file)
		agentElements 	= useragent["elements"]
		agentVerbs 		= useragent["verbs"]
		agentNouns 		= useragent["nouns"]
		element 		= Random.choice(agentElements)
		userAgent 		= Random.choice(agentVerbs[element]) + "-" + Random.choice(agentNouns[element]) + "_" + str(Random.randint(0, 3)) + "." + str(Random.randint(1, 17))
	else:
		userAgent 		= defUserAgent

	# Set Logging
	Logging.basicConfig(filename = logDir, level = getattr(Logging, logLevel))
	logger 			= Logging.getLogger()
	handler 		= Logging.StreamHandler()
	formatter 		= Logging.Formatter('%(levelname)-8s %(name)-12s %(asctime)-28s %(message)-48s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	# Output
	logger.info("- Initialized -------------------------------")
	logger.info("Loaded on %s" % currentDatetime.strftime("%x at %H:%M:%S"))
	if lastSuccess is not None:
		logger.info("Last Successful Log on %s" % Datetime.datetime.fromtimestamp(lastSuccess).strftime("%x at %H:%M:%S"))

	# If Override Set or First Attempt or Last Success Was Greater Than n Hours Ago
	if override or lastSuccess is None or (currentDatetime - Datetime.datetime.fromtimestamp(lastSuccess)) >= Datetime.timedelta(seconds = delay):

		# 
		# Core Logic
		# 

		# Get Network SSID
		process = Subprocess.Popen([airportPath, "-I"], stdout = Subprocess.PIPE, stderr = Subprocess.PIPE)
		stdout, stderr = process.communicate()
		network = {line.split(":")[0].strip() : line.split(":")[1].strip() for line in stdout.decode('utf-8').split("\n") if ":" in line }

		# Are We On A Valid Network?
		if len(network) > 1 and network["SSID"] in validSSIDs:

			# Log Network Found
			logger.info("Valid network found - %s" % network["SSID"])

			# Get Password From OS X Key Chain
			process = Subprocess.Popen(["security", "find-internet-password", "-s", "o2.ohsu.edu", "-w"], stdout = Subprocess.PIPE, stderr = Subprocess.PIPE)
			stdout, stderr = process.communicate()
			password = stdout.rstrip().decode('utf-8') # Strip Newline Character & Convert Bytecode to UTF-8

			# Log User Agent
			logger.info("Useragent set – %s" % userAgent)

			# Log Posting Data to API
			logger.info("Posting data to API")

			# Initialize Secure Web Session & Login to Incentive Website
			with Requests.session() as session:

				# Set Request Headers
				headers = {
					"User-Agent" : userAgent
				}

				# Initial Login – Set Session Cookies
				response = session.get(protocol + "://" + username + ":" + password + "@" + url, headers = headers)
				logger.info("Login HTTP Status – %d" % response.status_code)
				# Submit Trip Data & Capture Response (Session Cookies Handled Internally by Requests.session) 
				response = session.post(protocol + "://" + username + ":" + password + "@" + url, data = tripDetails)
				logger.info("Form Submit HTTP Status – %d" % response.status_code)

			logger.info("DOM size = %0.2fKB" % (len(response.content) // 1024))

			# Get DOM From Response
			htmlDOM = html.fromstring(response.content)

			# Get Notification
			notification = htmlDOM.xpath('//p[@class="notification"]/text()')
			notificationDetails = [Rgx.sub(r"[\:\-]", "", string).strip() for string in notification if len(string.strip()) > 0]
			for detail in notificationDetails:
				logger.info("%s" % detail)

			# Get Success
			success = htmlDOM.xpath('//span[@class="success"]/text()')
			successDetails = [Rgx.sub(r"[\:\-]", "", string).strip() for string in success if len(string.strip()) > 0]
			for detail in successDetails:
				logger.info("%s" % detail)

			# If Successfully Logged
			if len(successDetails) > 0:

				# Write Timestamp of Last Successful Log Attempt to Config & Reset Override to False
				with open("../config/config.json", "w") as file:
					config["last_success"] = currentDatetime.timestamp()
					config["override"] = False
					JSON.dump(config, file, indent = "\t")

			else:
				# Reset Override to False – Enforces User Override on Each Override Attempt
				with open("../config/config.json", "w") as file:
					config["override"] = False
					JSON.dump(config, file, indent = "\t")

			logger.info("- Exiting -----------------------------------")
			exit()

		else:

			# Log No Network Connection & Exit
			if len(network) == 1 or len(network["SSID"]) == 0:

				logger.warning("No network connection")
				logger.info("- Exiting -----------------------------------")
				exit()

			# Log Invalid Network & Exit
			else:
				logger.warning("Invalid network - %s" % network["SSID"])
				logger.info("- Exiting -----------------------------------")
				exit()

	# Pass – Tool Already Ran Within Delay Period
	else: 

		logger.warning("%d hour Delay Period Active" % (delay / 3600))
		logger.info("Delay Period Ends in %s" % str((Datetime.datetime.fromtimestamp(lastSuccess) + Datetime.timedelta(hours = config["hours_delay"])) - currentDatetime).split(".")[0])
		logger.info("- Exiting -----------------------------------")
		exit()

		pass
else:
	pass

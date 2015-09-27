#!/usr/bin/env python
# FFXIV ARR Python Launcher - Python 2
# Author: Jordan Henderson
# This is a fairly quick and nasty implementation of a functional launcher for FFXIV.
# TODO: ffxivupdate support.
# refactoring and changes: Matthew Clark

# Configuration
region = "3" #Region for authentication checking.
user = "user"
path = "/" #Path containing boot and game
wine = True #Prefix execution with 'wine' (for Linux/Mac)
one_time_password = ''

import urllib2
import urllib
import re
import os
import hashlib
import sys
import ssl
from getpass import getpass

passwd = getpass()

context = ssl._create_unverified_context()

def gen_hash(file):
	return str(os.stat(file).st_size) + "/" + hashlib.sha1(open(file, "rb").read()).hexdigest()

if len(sys.argv) > 1:
	one_time_password = sys.argv[1]
if len(sys.argv) > 2:
	user = sys.argv[2]
	passwd = sys.argv[3]

def gen_launcher_string(username,password,otpw,gamepath):
	os.chdir(gamepath + "/game")

	version = ""
	with open('ffxivgame.ver', 'r') as f:
		version = f.readline()
	
	headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)"}
	login_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/top?lng=en&rgn="+region
	login_info_req = urllib2.Request(login_url,
				 None, headers)
	
	login_info = urllib2.urlopen(login_info_req)
	cookies = login_info.headers.get('Set-Cookie')
	response = login_info.read()

	m = re.search('<input type="hidden" name="_STORED_" value="(.*)"', response)
	headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)", "Cookie": cookies,
		   "Referer": login_url, "Content-Type": "application/x-www-form-urlencoded"}
	print("user:"+username+" pass:"+password+" otpw:"+otpw)
	login_data = urllib.urlencode({'_STORED_':m.group(1), 'sqexid':username, 'password':password, 'otppw':otpw})
	login_req = urllib2.Request("https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/login.send",
				    login_data, headers)
	
	login_result = urllib2.urlopen(login_req)
	response = login_result.read()
	m = re.search('login=auth,ok,sid,(.+?),', response)
	if not m:
            #Login failed. Abort
		print("Login failed. Please try again.")
		quit()
	
	sid = m.group(1)

#gamever headers
	headers = {"X-Hash-Check":"enabled"}
#Use the patch gamever service to retrieve our *actual* sid.
	gamever_url = "https://patch-gamever.ffxiv.com/http/win32/ffxivneo_release_game/"+version+"/"+sid

#calculate hashes...
	hash_str = "ffxivboot.exe/" + gen_hash("../boot/ffxivboot.exe") + "," + "ffxivlauncher.exe/" + gen_hash("../boot/ffxivlauncher.exe") + "," + "ffxivupdater.exe/" + gen_hash("../boot/ffxivupdater.exe")

	gamever_req = urllib2.Request(gamever_url, hash_str, headers)
	
	gamever_result = urllib2.urlopen(gamever_req, context=context)
	actual_sid = gamever_result.info().getheader("X-Patch-Unique-Id")
	return (('wine' if wine else '') + ' ffxiv.exe "DEV.TestSID='+ actual_sid + '" "DEV.UseSqPack=1" "DEV.DataPathType=1" "DEV.LobbyHost01=neolobby01.ffxiv.com" "DEV.LobbyPort01=54994" "DEV.LobbyHost02=neolobby02.ffxiv.com" "DEV.LobbyPort02=54994" "SYS.Region=3" "language=1" "ver='+version+'"')

launch = gen_launcher_string(user,passwd,one_time_password,path)
print(launch)
os.system(launch)

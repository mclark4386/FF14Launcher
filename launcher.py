#!/usr/bin/env python3
# FFXIV ARR Python Launcher - Python 2 or 3
# Author: Jordan Henderson
# This is a fairly quick and nasty implementation of a functional launcher for FFXIV.
# TODO: ffxivupdate support.
# refactoring and changes: Matthew Clark, Arthur Moore, Stian E. Syvertsen

# Configuration
USEGUI = True           # Use a gui to ask for username, password, and one time password
expansionId='0'         # Set this to 1 if you have Heavensward expansion installed.
region = "3"            # Region for authentication checking.
path = "/"              # Path containing boot and game (eg. "C:/Program Files (x86)/SquareEnix/FINAL FANTASY XIV - A Realm Reborn")
wine_command = 'wine'   # Prefix execution with 'wine' (for Linux/Mac)
#wine_command = ''      # For Windows
user = ''
password = ''
one_time_password = ''

import re
import os
import hashlib
import sys
import ssl
from getpass import getpass
if (sys.version_info >= (3,0)):
    from urllib.request import Request,urlopen
    from urllib.parse import urlencode
else:
    from urllib2 import  Request,urlopen
    from urllib  import urlencode

def open_url(url,data,headers,context=None):
    req = Request(url, data, headers)
    return urlopen(req,context=context)

def gen_hash(file):
	return str(os.stat(file).st_size) + "/" + hashlib.sha1(open(file, "rb").read()).hexdigest()

#Performs login routine to get sid
def login(region,username,password,one_time_password):
	#Get the login page for the region
	headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)"}
	login_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/top?lng=en&rgn="+region
	login_info = open_url(login_url, None, headers)
	cookies = login_info.headers.get('Set-Cookie')
	if (cookies == None):
		cookies = ""
	response = login_info.read().decode('utf-8')
	m = re.search('<input type="hidden" name="_STORED_" value="(.*)"', response)
	if not m:
		raise Exception("Unable to access login page. Please try again.")

	#Authenticate with the server, and get the sid
	headers = {
		"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)",
		"Cookie": cookies,
		"Referer": login_url,
		"Content-Type": "application/x-www-form-urlencoded"
	}
	login_data = urlencode({'_STORED_':m.group(1), 'sqexid':username, 'password':password, 'otppw':one_time_password}).encode('utf-8')
	login_url_2 = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/login.send"
	response = open_url(login_url_2, login_data, headers).read().decode('utf-8')
	m = re.search('login=auth,ok,sid,(.+?),', response)
	if not m:
		raise Exception("Login failed. Please try again.")

	return m.group(1)

#Use the patch gamever service to retrieve our *actual* sid.
#Also return's the game's version
def get_actual_sid(sid,gamepath):
	version = ""
	with open(gamepath+'/game/ffxivgame.ver', 'r') as f:
		version = f.readline()
	headers = {"X-Hash-Check":"enabled"}
	gamever_url = "https://patch-gamever.ffxiv.com/http/win32/ffxivneo_release_game/"+version+"/"+sid
	#calculate hashes...
	hash_str = "ffxivboot.exe/"     + gen_hash(gamepath+"/boot/ffxivboot.exe") \
		+ ","+ "ffxivlauncher.exe/" + gen_hash(gamepath+"/boot/ffxivlauncher.exe") \
		+ ","+ "ffxivupdater.exe/"  + gen_hash(gamepath+"/boot/ffxivupdater.exe")

	gamever_result = open_url(gamever_url, hash_str.encode('utf-8'), headers, ssl._create_unverified_context()).info()
	if (gamever_result.get("X-Latest-Version") != version):
		raise Exception("Game out of date.  Please run the official launcher to update it.")
	actual_sid = gamever_result.get("X-Patch-Unique-Id")
	return (actual_sid,version)

def gen_launcher_string(actual_sid,version):
	launcher_str = '{wine_command}' \
		+' \'{gamepath}/game/ffxiv.exe\'' \
		+' "language=1"' \
		+' "DEV.UseSqPack=1" "DEV.DataPathType=1"' \
		+' "DEV.LobbyHost01=neolobby01.ffxiv.com" "DEV.LobbyPort01=54994"' \
		+' "DEV.LobbyHost02=neolobby02.ffxiv.com" "DEV.LobbyPort02=54994"' \
		+' "DEV.TestSID={actual_sid}"' \
		+' "DEV.MaxEntitledExpansionID={expansionId}"' \
		+' "SYS.Region={region}"' \
		+' "ver={version}"'
	return launcher_str.format(wine_command=wine_command,gamepath=path,actual_sid=actual_sid,expansionId=expansionId,region=region,version=version)

def run(username,password,one_time_password):
	sid=login(region,username,password,one_time_password)
	(actual_sid,version) = get_actual_sid(sid,path)
	launch = gen_launcher_string(actual_sid,version)
	print(launch)
	os.system(launch)

def run_gui(root,username,password,one_time_password):
	#Disable the GUI
	root.quit()
	root.destroy()
	#Run the Program
	try:
		run(username,password,one_time_password)
	except Exception as err:
		if (sys.version_info >= (3,0)):
			import tkinter
			from tkinter.messagebox import showwarning
		else:
			import Tkinter as tkinter
			from tkMessageBox import showwarning
		top = tkinter.Tk()
		top.wm_withdraw()
		showwarning("Error", str(err), parent=top)

def gui_prompt(user="",password="",one_time_password=""):
	if (sys.version_info >= (3,0)):
		import tkinter
	else:
		import Tkinter as tkinter
	top = tkinter.Tk()
	L1 = tkinter.Label(top, text="User Name")
	L1.grid(row = 0, column = 0)
	E1 = tkinter.Entry(top, textvariable=tkinter.StringVar(value=user))
	E1.grid(row = 0, column = 1)
	L2 = tkinter.Label(top, text="Password")
	L2.grid(row = 1, column = 0)
	E2 = tkinter.Entry(top, show="*", textvariable=tkinter.StringVar(value=password))
	E2.grid(row = 1, column = 1)
	L3 = tkinter.Label(top, text="One Time Password")
	L3.grid(row = 2, column = 0)
	E3 = tkinter.Entry(top, textvariable=tkinter.StringVar(value=one_time_password))
	E3.grid(row = 2, column = 1)

	OK = tkinter.Button(top, text ="Connect", command = lambda: run_gui(top,E1.get(),E2.get(),E3.get()))
	OK.grid(row = 3, column = 1)
	top.bind('<Return>', lambda _: OK.invoke())
	top.bind('<KP_Enter>', lambda _: OK.invoke())

	#Place window in center of screen
	top.eval('tk::PlaceWindow %s center' % top.winfo_pathname(top.winfo_id()))
	#Focus on the one time password box at start
	E3.focus()
	top.title("FFXIV Launcher")
	top.mainloop()



if len(sys.argv) > 1:
	one_time_password = sys.argv[1]
if len(sys.argv) > 2:
	user = sys.argv[2]
	password = sys.argv[3]

if (USEGUI == True):
    gui_prompt(user,password,one_time_password)
else:
	if (user == ''):
		user = raw_input("User Name:  ")
	if (password == ''):
		password = getpass()
	try:
		run(user,password,one_time_password)
	except Exception as err:
		print("Error:  " + str(err))

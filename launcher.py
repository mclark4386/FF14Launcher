#!/usr/bin/env python
# FFXIV ARR Python Launcher - Python 2
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


import urllib2
import urllib
import re
import os
import hashlib
import sys
import ssl
from getpass import getpass

def gen_hash(file):
	return str(os.stat(file).st_size) + "/" + hashlib.sha1(open(file, "rb").read()).hexdigest()

def gen_launcher_string(region,username,password,otpw,gamepath):
	context = ssl._create_unverified_context()

	os.chdir(gamepath + "/game")

	version = ""
	with open('ffxivgame.ver', 'r') as f:
		version = f.readline()

	headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)"}
	login_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/top?lng=en&rgn="+region
	login_info_req = urllib2.Request(login_url, None, headers)

	login_info = urllib2.urlopen(login_info_req)
	cookies = login_info.headers.get('Set-Cookie')
	response = login_info.read()

	m = re.search('<input type="hidden" name="_STORED_" value="(.*)"', response)
	headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)", "Cookie": cookies,
		   "Referer": login_url, "Content-Type": "application/x-www-form-urlencoded"}

	login_data = urllib.urlencode({'_STORED_':m.group(1), 'sqexid':username, 'password':password, 'otppw':otpw})
	login_req = urllib2.Request("https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/login.send",
				    login_data, headers)

	login_result = urllib2.urlopen(login_req)
	response = login_result.read()
	m = re.search('login=auth,ok,sid,(.+?),', response)
	if not m:
		raise Exception("Login failed. Please try again.")

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
	return ('ffxiv.exe "DEV.TestSID='+ actual_sid + '" "DEV.UseSqPack=1" "DEV.DataPathType=1" "DEV.LobbyHost01=neolobby01.ffxiv.com" "DEV.LobbyPort01=54994" "DEV.LobbyHost02=neolobby02.ffxiv.com" "DEV.LobbyPort02=54994" "DEV.MaxEntitledExpansionID='+ expansionId +'" "SYS.Region=3" "language=1" "ver='+version+'"')

def run(user,password,one_time_password):
	#global root
	#global path
	try:
		launch = wine_command + ' ' + gen_launcher_string(region,user,password,one_time_password,path)
		print(launch)
		os.system(launch)
	except Exception, err:
		print("Error:  " + str(err))

def run_gui(root,user,password,one_time_password):
	#global root
	#global path
	#Disable the GUI
	root.quit()
	root.destroy()
	#Run the Program
	try:
		launch = wine_command + ' ' + gen_launcher_string(region,user,password,one_time_password,path)
		print(launch)
		os.system(launch)
	except Exception, err:
		import Tkinter
		top = Tkinter.Tk()
		top.wm_withdraw()
		from tkMessageBox import showwarning
		showwarning("Error", str(err), parent=top)

def gui_prompt(user="",password="",one_time_password=""):
	import Tkinter
	top = Tkinter.Tk()
	L1 = Tkinter.Label(top, text="User Name")
	L1.grid(row = 0, column = 0)
	E1 = Tkinter.Entry(top, textvariable=Tkinter.StringVar(value=user))
	E1.grid(row = 0, column = 1)
	L2 = Tkinter.Label(top, text="Password")
	L2.grid(row = 1, column = 0)
	E2 = Tkinter.Entry(top, show="*", textvariable=Tkinter.StringVar(value=password))
	E2.grid(row = 1, column = 1)
	L3 = Tkinter.Label(top, text="One Time Password")
	L3.grid(row = 2, column = 0)
	E3 = Tkinter.Entry(top, textvariable=Tkinter.StringVar(value=one_time_password))
	E3.grid(row = 2, column = 1)

	OK = Tkinter.Button(top, text ="Connect", command = lambda: run_gui(top,E1.get(),E2.get(),E3.get()))
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
	run(user,password,one_time_password)

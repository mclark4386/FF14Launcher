#!/usr/bin/env python3
# FFXIV ARR Launcher Login library
#Copyright: Arthur Moore BSD 3 clause
#This is a near rewrite based on the work of Matthew Clark and Jordan Henderson

import pprint
#pprint.pprint(gamever_result.as_string())
import re
import os
import hashlib
import sys
import ssl
if (sys.version_info >= (3,0)):
    from urllib.request import Request,urlopen
    from urllib.parse import urlencode
else:
    from urllib2 import  Request,urlopen
    from urllib  import urlencode

#Constants and magic values used throughout
login_headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)"}
login_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/top?lng={lng}&rgn={rgn}"

authentication_headers = {
    "User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)",
    "Cookie": "",
    "Referer": "Put_Login_url_here",
    "Content-Type": "application/x-www-form-urlencoded"
}
authentication_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/login.send"

version_headers = {"X-Hash-Check":"enabled"}
version_url = "https://patch-gamever.ffxiv.com/http/win32/ffxivneo_release_game/{version}/{sid}"

def open_url(url,data,headers,context=None):
    req = Request(url, data, headers)
    return urlopen(req,context=context)

def gen_hash(file):
    return os.path.basename(file) + "/" + str(os.stat(file).st_size) + "/" + hashlib.sha1(open(file, "rb").read()).hexdigest()

#Performs login routine to get sid
def login(region,username,password,one_time_password):
    #Get the login page for the region
    login_info = open_url(login_url.format(lng='en',rgn=region), None, login_headers)
    cookies = login_info.headers.get('Set-Cookie')
    if (cookies != None):
        raise Exception("Login page has changed!  Please update to a newer version of this program.")
    response = login_info.read().decode('utf-8')
    m = re.search('<input type="hidden" name="_STORED_" value="(.*)"', response)
    if not m:
        raise Exception("Unable to access login page. Please try again.")

    #Authenticate with the server, and get the sid
    authentication_headers["Referer"]=login_url.format(lng='en',rgn=region)
    login_data = urlencode({'_STORED_':m.group(1), 'sqexid':username, 'password':password, 'otppw':one_time_password}).encode('utf-8')
    response = open_url(authentication_url, login_data, authentication_headers).read().decode('utf-8')
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

    version_hash = gen_hash(gamepath+"/boot/ffxivboot.exe")+"," \
              +gen_hash(gamepath+"/boot/ffxivlauncher.exe")+"," \
              +gen_hash(gamepath+"/boot/ffxivupdater.exe")

    gamever_result = open_url(version_url.format(version=version,sid=sid), version_hash.encode('utf-8'), version_headers, ssl._create_unverified_context()).info()
    if (gamever_result.get("X-Latest-Version") != version):
        raise Exception("Game out of date.  Please run the official launcher to update it.")
    actual_sid = gamever_result.get("X-Patch-Unique-Id")
    return (actual_sid,version)


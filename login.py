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
import datetime
if (sys.version_info >= (3,0)):
    from urllib.request import Request,urlopen
    from urllib.parse import urlencode
else:
    from urllib2 import  Request,urlopen
    from urllib  import urlencode

#Constants and magic values used throughout
login_headers = {"User-Agent":"SQEXAuthor/2.0.0(Windows XP; ja-jp; 3aed65f87c)"}
login_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/top?lng={lng}&rgn={rgn}&isft=0&issteam=0"

authentication_headers = {
    "User-Agent":"SQEXAuthor/2.0.0(Windows 6.2; ja-jp; ecf4a84335)",
    "Cookie": "",
    "Referer": "Put_Login_url_here",
    "Content-Type": "application/x-www-form-urlencoded"
}
authentication_url = "https://ffxiv-login.square-enix.com/oauth/ffxivarr/login/login.send"

version_headers = {"X-Hash-Check":"enabled"}
version_url = "https://patch-gamever.ffxiv.com/http/win32/ffxivneo_release_game/{version}/{sid}"

bootver_headers = {"User-Agent": "FFXIV PATCH CLIENT"}
bootver_url="http://patch-bootver.ffxiv.com/http/win32/ffxivneo_release_boot/{version}/?time={time}"


def open_url(url,data,headers,context=None):
    req = Request(url, data, headers)
    return urlopen(req,context=context)

def gen_hash(file):
    return os.path.basename(file) + "/" + str(os.stat(file).st_size) + "/" + hashlib.sha1(open(file, "rb").read()).hexdigest()

#Parse the update data to determine what to download when the launcher/client is out of date
def parse_update_data(what_is_updating,update_info):
    search_results = re.search('http://(.*)/boot/(.*)/(.*)\.patch', update_info)
    if not search_results:
        raise Exception(what_is_updating+" is out of date! Unable to find patch file location.")
    patch_url = search_results.group(0).strip()
    raise Exception(what_is_updating+" is out of date!  Please download the latest patch file from:  "+patch_url)

#Performs login routine to get sid
def login(region,username,password,one_time_password):
    #Get the login page for the region
    login_info = open_url(login_url.format(lng='en',rgn=region), None, login_headers)
    cookies = login_info.headers.get('Set-Cookie')
    if (cookies != None):
        raise Exception("Login page has changed!  Please update to a newer version of this program.")
    response_data = login_info.read().decode('utf-8')
    search_results = re.search('<input type="hidden" name="_STORED_" value="(.*)"', response_data)
    if not search_results:
        raise Exception("Unable to access login page. Please try again.")

    #Authenticate with the server, and get the sid
    authentication_headers["Referer"]=login_url.format(lng='en',rgn=region)
    login_data = urlencode({'_STORED_':search_results.group(1), 'sqexid':username, 'password':password, 'otppw':one_time_password}).encode('utf-8')
    response_data = open_url(authentication_url, login_data, authentication_headers).read().decode('utf-8')
    search_results = re.search('login=auth,ok,sid,(.+?),', response_data)
    if not search_results:
        raise Exception("Login failed. Please try again.")

    return search_results.group(1)

#Use the patch gamever service to retrieve our *actual* sid.
#Also return's the game's version
def get_actual_sid(sid,gamepath):
    version = ""
    with open(gamepath+'/game/ffxivgame.ver', 'r') as f:
        version = f.readline()

    version_hash = gen_hash(gamepath+"/boot/ffxivboot.exe")+"," \
              +gen_hash(gamepath+"/boot/ffxivlauncher.exe")+"," \
              +gen_hash(gamepath+"/boot/ffxivupdater.exe")

    response = open_url(version_url.format(version=version,sid=sid), version_hash.encode('utf-8'), version_headers, ssl._create_unverified_context())
    response_data = response.read().decode('utf-8')
    actual_sid = response.headers.get("X-Patch-Unique-Id")

    if (response.headers.get("X-Latest-Version") != version or response_data != ''):
        print(response.headers.as_string())
        print(response_data)
        raise Exception("Game out of date.  Please run the official launcher to update it.")

    return (actual_sid,version)

#Make sure the launcher is up to date
def get_boot_version(gamepath):
    version = ""
    with open(gamepath+'/boot/ffxivboot.ver', 'r') as f:
        version = f.readline()

    time     = datetime.datetime.utcnow()
    time_str = time.strftime("%Y-%m-%d-%H-%M")
    #The server always expects the end minute to be zero, so have to fixup the time
    time_str = time_str[:-1] + '0'

    response = open_url(bootver_url.format(version=version,time=time_str), None, bootver_headers, ssl._create_unverified_context())
    response_data = response.read().decode('utf-8')
    if (response.headers.get("X-Latest-Version") == version and response_data == ''):
        return 0
    parse_update_data("Launcher",response_data)

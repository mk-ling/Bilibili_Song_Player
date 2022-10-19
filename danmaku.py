import requests
import time
import os
import sys

fpath = os.path.dirname(sys.executable)
session = requests.Session()
session.trust_env = False

class Danmaku:
    def __init__(self, text, uid, nickname, timeline, isadmin):
        self.text = text
        self.uid = uid
        self.nickname = nickname
        self.timeline = timeline
        self.isadmin = int(isadmin)
    def toString(self):
        print(self.nickname + ', ' + str(self.text) + ', ' + str(self.uid) + ', ' + str(self.timeline) + ', ' + str(self.isadmin))

def parse_danmu(url):
    host_id = url.replace('https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory?roomid=', '')
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
    try:
        danmu = session.get(url, headers=headers, proxies=None).text
    except Exception as e:
        time.sleep(20)
        parse_danmu(url)
    empty_danmu = '{"code":0,"data":{"admin":[],"room":[]},"message":"","msg":""}'
    while danmu == empty_danmu:
        danmu = session.get(url, headers=headers, proxies=None).text
        print('No danmaku for now, waiting....')
        time.sleep(20)
    danmu = danmu[28:len(danmu) - 1]
    danmu = danmu.split('},{')
    danmaku_list = list()
    for d in danmu:
        d = d.split(',\"')
        text = replace_all(d[0])
        uid = replace_all(d[1])
        nickname = replace_all(d[2])
        timeline = replace_all(d[4])
        isadmin = replace_all(d[5])
        if is_host(uid): isadmin = 1
        danmaku = Danmaku(text, uid, nickname, timeline, isadmin)
        danmaku_list.append(danmaku)
    return danmaku_list

def is_host(uid):
    host_id = open(os.path.join(fpath, 'host_id.txt'), 'r', encoding='utf-8').read()
    if host_id == uid:
        return True
    else:
        return False

def replace_all(string):
    list = ['"', ':','text', 'nickname', 'timeline', 'isadmin']
    for l in list:
        string = string.replace(l, '')
    return string



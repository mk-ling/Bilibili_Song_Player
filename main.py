import threading
import sys
import os
from selenium import webdriver
from danmaku import *
from obs import *
import tkinter as tk

global play_list, last_timeline, switch, threadLock, fpath




class Song:
    def __init__(self, name, uid , nickname, timeline):
        self.name = name
        self.uid = uid
        self.nickname = nickname
        self.timeline = timeline

class Playlist:
    def __init__(self):
        self.list = []
        self.switch = 0
    def add_song(self, song):
        self.song = song
        self.list.append(song)
    def remove_song(self, index):
        self.list.remove(index)
    def pop(self):
        if len(self.list) > 0:
            print('POPING')
            self.list.pop(0)
    def get_song(self, index):
        return self.list[index]
    def get_song_by_name(self, song_name):
        for song in self.list:
            if song_name == song.name:
                return song
    def get_index(self, song):
        return  self.list.index(song)
    def is_empty(self):
        if len(self.list) < 1:
            return True
        else:
            return False
    def to_string(self):
        string = ''
        for song in self.list:
            string +=  song.name + '---' +song.nickname + '\n'
        return string


class Switch:
    def __init__(self):
        self.state = 0
        self.timeline = time.strftime('%Y-%m-%d %H%M%S')
        self.lookup_timeline = time.strftime('%Y-%m-%d %H%M%S')
        self.list_change = 0
    def switch_on(self):
        self.state = 1
    def switch_off(self):
        self.state = 0

def show_text(string):
    path = os.path.join(fpath, 'monitor.txt')
    if not play_list.is_empty():
        first_song = play_list.get_song(0)
        text = '正在播放： ' + str(first_song.name) + ' by ' + first_song.nickname + '\n'
        text += '列表曲目数： ' + str(len(play_list.list)) + '\n'
        text += string
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    elif play_list.is_empty():
        with open(path, 'w', encoding='utf-8') as f:
            text = '目前列表里没有歌曲'
            f.write(text)

class updateThread(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.url = url
    def run(self):
        last_timeline = time.strftime('%Y-%m-%d %H%M%S')
        while True:
            danmaku_list = parse_danmu(url)
            for danmaku in danmaku_list:
                if '点歌，' in danmaku.text or '点歌,' in danmaku.text or '点歌 ' in danmaku.text or '点歌：' in danmaku.text:
                    song_name = danmaku.text[3 : len(danmaku.text)]
                    song = Song(song_name, danmaku.uid, danmaku.nickname, danmaku.timeline)
                    new_song = compare(song.timeline, last_timeline)
                    if song in play_list.list or new_song == False:
                        pass
                    elif new_song == True and not in_blacklist(song_name):
                        play_list.add_song(song)
                        switch.list_change = 1
                        threadLock.acquire()
                        last_timeline = song.timeline
                        threadLock.release()
                        print('添加歌曲: ' + song_name + '----' + song.nickname)
                        show_text('添加歌曲: ' + song_name + '----' + song.nickname)
                        print('目前播放列表：')
                        print(play_list.to_string())
                    elif new_song == True and in_blacklist(song_name):
                        last_timeline = song.timeline
                        print('歌曲在黑名单内，无法点播')
                        show_text('歌曲在黑名单内，无法点播')
                elif '切歌' == danmaku.text and compare(danmaku.timeline, switch.timeline) and danmaku.isadmin == 1:
                    switch.timeline = danmaku.timeline
                    skip()
                elif '查询' in danmaku.text and compare(danmaku.timeline, switch.lookup_timeline):
                    result = look_up(danmaku.text, play_list)
                    switch.lookup_timeline = danmaku.timeline
                    if result == False:
                        print('查询歌曲不存在')
                        show_text('查询歌曲不存在')
            time.sleep(3)

class browserThread(threading.Thread):
    def __init__(self, web):
        threading.Thread.__init__(self)
        self.web = web
    def run(self):
        while True:
            if play_list.is_empty() == False:
                song = play_list.get_song(0)
                song_name = song.name
                print('正在播放: ' + song_name + song.nickname)
                search_url = search_song(song_name)
                song_exist = play_song(web, search_url, 0)
                if song_exist == 0:
                    print('播放失败，歌曲可能不存在')
                    show_text('播放失败，歌曲可能不存在')
                    play_list.pop()
                    continue
                else:
                    pass
                duration = 0
                retry = 0
                while duration == 0:
                    if retry >= 3: break
                    time.sleep(2)
                    duration = turn_seconds(web.find_element_by_id('time').text)
                    retry += 1
                if duration == 0:
                    print('播放失败，歌曲可能不支持')
                    show_text('播放失败，歌曲可能不支持')
                    play_list.pop()
                    continue
                print('duration: ' + str(duration))
                for x in range(0, duration, 2):
                    if switch.state == 1:
                        play_list.pop()
                        switch.switch_off()
                        if play_list.is_empty() == True: web.get('https://www.baidu.com')
                        print('切歌ing')
                        print(play_list.to_string())
                        break
                    else:
                        time.sleep(2)
                else:
                    show_text('')
                    play_list.pop() 
                    web.get('https://www.baidu.com')
            else:
                time.sleep(5)

def look_up(command, playlist):
    if '查询 ' in command or '查询，' in command or '查询, ' in command or '查询：' in command:
        song_name = command[3 : len(command)]
        for song in playlist.list:
            if song_name == song.name:
                index = playlist.get_index(song) + 1
                print(song_name + '在列表第' + str(index) + '首')
                show_text(song_name + '在列表第' + str(index) + '首')
                return index
        else: return False
    if '查询用户 ' in command or '查询用户,' in command or '查询用户，' in command or '查询用户：' in command:
        nickname = command[5 : len(command)]
        song_number = 0
        for song in playlist.list:
            if nickname == song.nickname: song_number += 1
        else:
            print(nickname + ' 目前有' + str(song_number) + '首歌在列表')
            show_text(nickname + ' 目前有' + str(song_number) + '首歌在列表')
            return song_number
    return False

def play_song(web, search_url, retry):
    if retry >= 3:
        print('播放失败，歌曲可能不存在')
        show_text('播放失败，歌曲可能不存在')
        return 0
    web.get(search_url)
    song_url = ''
    time.sleep(3)
    try:
        web.switch_to_frame('g_iframe')  # switch the focus to the frame that we want to get source from
        frame_source = web.page_source
        song_url = gen_song_url(frame_source)
    except Exception:
        print('frame source not found, RELOADING x ' + str(retry))
        retry += 1
        play_song(web, search_url, retry)
    try:
        web.get(song_url)
        web.find_element_by_id('play').click()
    except Exception as e:
        return 0

def skip():
    threadLock.acquire()
    switch.switch_on()
    threadLock.release()
    switch.list_change = 1
    show_text('')

def top():
    global selected
    song_name = selected
    print('top: ' + song_name)
    if len(play_list.list) > 2:
        song = play_list.get_song_by_name(song_name)
        index = play_list.get_index(song)
        threadLock.acquire()
        play_list.list.remove(song)
        play_list.list.insert(1, song)
        threadLock.release()
        switch.list_change = 1
    else:
        print('歌曲已在最上面')
        show_text('歌曲已在最上面')

def remove():
    global selected
    song_name = selected
    threadLock.acquire()
    song = play_list.get_song_by_name(song_name)
    play_list.list.remove(song)
    threadLock.release()
    switch.list_change = 1

def black_list():
    global selected
    song_name = selected
    path = os.path.join(fpath, 'blacklist.txt')
    read = open(path, 'r').read()
    blacklist = read.strip().split(',')
    blacklist.append('，\n' + song_name)
    output = ''
    for song in blacklist:
        output += song
    with open(path, 'w') as f:
        f.write(output)

def in_blacklist(song_name):
    path = os.path.join(fpath, 'blacklist.txt')
    try:
        read = open(path, 'r').read()
        blacklist = read.strip().split(',')
        for song in blacklist:
            if song_name in song:
                return True
        else:
            return False
    except Exception as e:
        print(e)
        print('Error, but carry on')
        return False

def refresh():
    global selected
    selected = str(list_box.get(tk.ACTIVE))
    if switch.list_change == 1:
        time.sleep(2)
        count = 1
        list_box.delete(0, tk.END)
        for song in play_list.list:
            list_box.insert(count, song.name)
            count += 1
        else:switch.list_change = 0
    window.after(1000, refresh)

fpath = os.path.dirname(sys.executable)
play_list = Playlist()

url = open(os.path.join(fpath, 'url.txt'), 'r', encoding='utf-8').read()
driver_path = os.path.join(fpath, 'chrome_driver')
web = webdriver.Chrome(driver_path)
switch = Switch()
threadLock = threading.Lock()
thread1 = browserThread(web)
thread2 = updateThread(url)
thread1.start()
thread2.start()
window = tk.Tk()
window.title = 'bilibili点歌插件'
window.geometry('500x500')
list_box = tk.Listbox(window, selectmode=tk.SINGLE)
list_box.xview()
list_box.pack()
selected = ''
button1 = tk.Button(window, width=10, height=2, text='切歌', command=skip)
button2 = tk.Button(window, width=10, height=2, text='置顶', command=top)
button3 = tk.Button(window, width=10, height=2, text='移除', command=remove)
button4 = tk.Button(window, width=10, height=2, text='拉黑', command=black_list)
button1.pack()
button2.pack()
button3.pack()
button4.pack()
window.after(1000, refresh())
window.mainloop()


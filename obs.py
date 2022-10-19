
import re
import time


def YMD_to_INT(YMD):
    temp = YMD.replace('-', '')
    return str(temp)

def compare(new_timeline, last_timeline):
    temp = last_timeline.split(' ')
    YMD_last = YMD_to_INT(temp[0])
    time_last = int(temp[1])
    temp2 = new_timeline.split(' ')
    YMD_new = YMD_to_INT(temp2[0])
    time_new = int(temp2[1])
    if YMD_new == YMD_last and time_new > time_last:
        return True
    elif YMD_new > YMD_last:
        return True
    else:
        return False


def search_song(song_name):  # generate a url for song searching
    url_head = 'https://music.163.com/#/search/m/?s='  # part1 of url
    url_tail = '&type=1'  # part3 of url
    song_name = str(song_name).replace(" ", '%20')  # get user input
    url = url_head + song_name + url_tail  # generate the url
    return url

def gen_song_url(frame_source):  # generate the url of the first song from the search result
    song = re.search('song.id=[0-9]*"?', frame_source.__str__()).group()  # find out the first song's id
    song_id = str(song).replace(r'song?id=', '')
    song_id = song_id.replace('"', '')
    song_url = 'https://music.163.com/outchain/player?type=2&id=' + song_id
    return song_url



def turn_seconds(time):
    time = time.replace('- ', '')
    time = time.split(':')
    minutes = int(time[0])
    seconds = int(time[1])
    return 60 * minutes + seconds



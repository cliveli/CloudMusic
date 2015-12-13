#! /usr/bin/env python
# -*- coding:utf-8 -*-  

'''
Created on 2013-06-07 19:28

@author: Yang Junyong <yanunon@gmail.com>
'''

import md5
import base64
import urllib2
import urllib
import json
import random
import os
import sys
import re
import time
import socket

#输入输出字符编码
stdin_encode=sys.stdin.encoding
stdout_encode=sys.stdout.encoding
#下载最大重试次数
max_retry = int(5)
#专辑查询最大条数
max_album_num=int(100)
#歌曲查询最大条数
max_song_num=int(100)
#进度条长度
process_length = int(50)
#socket超时时间
socket.setdefaulttimeout(10)

#set cookie
cookie_opener = urllib2.build_opener()
cookie_opener.addheaders.append(('Cookie', 'appver=2.0.2'))
cookie_opener.addheaders.append(('Referer', 'http://music.163.com'))
urllib2.install_opener(cookie_opener)

def encrypted_id(id):
    byte1 = bytearray('Some key for example 3go8&$8*3*3h0k(2)2')
    byte2 = bytearray(id)
    byte1_len = len(byte1)
    for i in xrange(len(byte2)):
        byte2[i] = byte2[i]^byte1[i%byte1_len]
    m = md5.new()
    m.update(byte2)
    result = m.digest().encode('base64')[:-1]
    result = result.replace('/', '_')
    result = result.replace('+', '-')
    return result

# 根据歌曲ID获取歌曲
# Full request URI: http://music.163.com/api/song/detail/?id=28377211&ids=%5B28377211%5D
# URL：GET http://music.163.com/api/song/detail/
# 必要参数：
# id：歌曲ID
# ids：不知道干什么用的，用[]括起来的歌曲ID
def get_song_by_id(id):
    url = 'http://music.163.com/api/song/detail?id=%s&ids=[%s]' % (id,id)
    resp = urllib2.urlopen(url)
    json_resp = json.loads(resp.read())
    return json_resp['songs'][0]

# Full request URI: http://music.163.com/api/album/2457012?ext=true&id=2457012&offset=0&total=true&limit=10
# URL：GET http://music.163.com/api/album/专辑ID
def get_album_by_id(id):
    url = 'http://music.163.com/api/album/%d/' % id
    resp = urllib2.urlopen(url)
    json_resp = json.loads(resp.read())
    return json_resp['album']

#def get_playlist_by_id(id):
    # URL：GET http://music.163.com/api/playlist/detail
    # 必要参数：
    # id：歌单ID
#def get_artist_by_id(id):

#def get_lyric_by_id(id):
    # Full request URI: http://music.163.com/api/song/lyric?os=pc&id=93920&lv=-1&kv=-1&tv=-1
    # URL：GET http://music.163.com/api/song/lyric
    # 必要参数：
    # id：歌曲ID
    # lv：值为-1，我猜测应该是判断是否搜索lyric格式
    # kv：值为-1，这个值貌似并不影响结果，意义不明
    # tv：值为-1，是否搜索tlyric格式
#def get_mv_by_id(id):
    # Full request URI: http://music.163.com/api/mv/detail?id=319104&type=mp4
    # URL：GET http://music.163.com/api/mv/detail
    # 必要参数：
    # id：mvid
    # type：值为mp4，视频格式，不清楚还有没有别的格式


# Full request URI: http://music.163.com/api/artist/albums/166009?id=166009&offset=0&total=true&limit=5
# URL：GET http://music.163.com/api/artist/albums/歌手ID
# 必要参数：
# limit：获取的数量(不知道为什么这个必须加上）
def get_artist_albums(id):
    albums = []
    offset = 0
    while True:
        url = 'http://music.163.com/api/artist/albums/%d?offset=%d&limit=50' % (id, offset)
        resp = urllib2.urlopen(url)
        tmp_albums = json.loads(resp.read())
        albums.extend(tmp_albums['hotAlbums'])
        if tmp_albums['more'] == True:
            offset += 50
        else:
            break
    return albums

def search_playlist_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    # type：搜索的类型 歌曲 1 专辑 10 歌手 100 歌单 1000 用户 1002 mv 1004 歌词 1006 主播电台 1009
    params = {
            's': name.encode('utf-8','ignore'),
            'type': 1000,
            'offset': 0,
            'sub': 'false',
            'limit': 10
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_js = json.loads(resp.read())
    if resp_js['code'] == 200 and artists['result']['playlistCount'] > 0:
        return resp_js['result']['playlists']
    else:
        return None

def search_artists_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name.encode('utf-8','ignore'),
            'type': 100,
            'offset': 0,
            'sub': 'false',
            'limit': 10
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_json = json.loads(resp.read())
    if resp_json['code'] == 200 and resp_json['result']['artistCount'] > 0:
        return resp_json['result']['artists']
    else:
        return None

def search_albums_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name.encode('utf-8','ignore'),
            'type': 10,
            'offset': 0,
            'sub': 'false',
            'limit': max_album_num
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_json = json.loads(resp.read())
    #print str(resp_js)
    if resp_json['code'] == 200 and resp_json['result']['albumCount'] > 0:
        result = resp_json['result']
        return result['albums']
    else:
        return None

#根据歌曲名查找歌曲
def search_songs_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name.encode('utf-8','ignore'),
            'type': 1,
            'offset': 0,
            'sub': 'false',
            'limit': max_song_num,
            'id' : '28167342'
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_json = json.loads(resp.read())
    if resp_json['code'] == 200 and resp_json['result']['songCount'] > 0:
        result = resp_json['result']
        return result['songs']
    else:
        return None


def download_album(album, folder='.'):
    #print album
    print '[Start] artist:%s\talbum:%s' % (to_str(album['artist']['name']), to_str(album['name']))
    #根据album_id获取album详情
    album = get_album_by_id(album['id'])
    songs = album['songs']
    for song in songs:
        #album详情内含有完整的song
        download_song(song, folder)

#根据歌曲id下载歌曲
def download_song_by_id(id, folder='.'):
    song = get_song_by_id(id)
    download_song(song, folder)

#下载歌曲到指定目录
def download_song(song, folder='.'):
    #print str(song)
    #首先创建专辑目录
    song_album = to_valid_path(song['album']['name'].strip())
    folder = os.path.join(folder, song_album)
    if not os.path.exists(folder):
        os.makedirs(folder)
    #生成文件路径
    name = song['name'].strip()
    artist = song['artists'][0]['name'].strip()
    fname = to_valid_path(artist +'-' +name+'.mp3')
    fpath = os.path.join(folder, fname)
    if os.path.exists(fpath):
        print 'WARN: %s already exists, continue next' % to_str(fpath)
        return
    #overwrite id if higher bitrate exists
    flag = ''
    song_dfsId = None
    if 'bMusic' in song.keys() and song['bMusic'] is not None and 'dfsId' in song['bMusic'].keys():
        #for 96Kbps Use this
        song_dfsId = str(song['bMusic']['dfsId'])
        flag = flag + 'B'
    else:
        flag = flag + '-'
    if 'lMusic' in song.keys() and song['lMusic'] is not None and 'dfsId' in song['lMusic'].keys():
        #for 96Kbps Use this
        song_dfsId = str(song['lMusic']['dfsId'])
        flag = flag + 'L'
    else:
        flag = flag + '-'
    if 'mMusic' in song.keys() and song['mMusic'] is not None and 'dfsId' in song['mMusic'].keys():
        #for 160kbps Use this
        song_dfsId = str(song['mMusic']['dfsId'])
        flag = flag + 'M'
    else:
        flag = flag + '-'
    if 'hMusic' in song.keys() and song['hMusic'] is not None and 'dfsId' in song['hMusic'].keys():
        #for 320Kbps Use this
        song_dfsId = str(song['hMusic']['dfsId'])
        flag = flag + 'H'
    else:
        flag = flag + '-'
    #find none music
    if not song_dfsId:
        print 'ERROR: can not find music of song %s, continue next' % to_str(name)
        return
    url = 'http://m%d.music.126.net/%s/%s.mp3' % (random.randrange(1, 3), encrypted_id(song_dfsId), song_dfsId)

    for times in range(max_retry):
        print '%s\t%s\t%s' % (flag, url, to_str(name))
        resp = urllib2.urlopen(url)
        if retrieve_response(resp,fpath,show_process) == True:
            break
        else:
            time.sleep(1);
        resp.close();

def retrieve_response(response, filepath, report_hook = None, block_size = 1024 * 32, ):
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    blocks_so_far = 0
    try:
        f = open(filepath, 'wb')
        while 1:
            block = response.read(block_size)        
            if not block:
                break
            f.write(block)
            bytes_so_far += len(block)
            blocks_so_far += 1
            #回调函数
            if report_hook:
                report_hook(blocks_so_far, block_size, total_size)
    except Exception, e:
        print '\nERROR: retrieve file %s exception.\r\n %s' % (to_str(filepath), e)
    finally:
        if 'f' in locals():
            f.close()
    #检查文件
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        if file_size != total_size:
            os.remove(filepath)
            print 'ERROR: file %s size mismatch, file_size=%d, supposed=%d. File removed' % (to_str(filepath), file_size, total_size)
            return False
    else:
        return False
    return True 

def show_process(downloaded_blocks, block_size, file_size):
    per = 100.0 * downloaded_blocks * block_size / file_size
    n = process_length
    num_of_n = int(per / (100 / n))
    process_bar = generate_process_bar(num_of_n, n)
    if per >= 100 :
        per = 100
        print '[ %s ]  %.2f%%' % (process_bar, per)
    else:
        print '[ %s ]  %.2f%%\r' % (process_bar, per),

def generate_process_bar(num_of_n, n):
    s=''
    i = 0;    
    while i < num_of_n-1:
        s = s + '#'
        i += 1
    while i < n-1:
        s = s + ' '
        i += 1
    return s

#根据歌曲名查找并下载
def download_song_by_search(name, folder='.'):
    #查找
    songs = search_songs_by_name(name)
    if not songs:
        print 'ERROR: Not found ' + to_str(name)
        return

    if not os.path.exists(folder):
        os.makedirs(folder)

    for i in range(len(songs)):
        song = songs[i]
        #print str(song);
        song_name= song['name']
        song_album = song['album']['name']
        song_artist = song['artists'][0]['name']
        print '[%2d]song:%s\tartist:%s\talbum:%s' % (i+1, to_str(song_name), to_str(song_artist), to_str(song_album))
    #输入所选项
    select = str(raw_input('Select One(Empty for all):')).strip();
    if select == '':
        for i in range(len(songs)):
            # search到的歌曲里面没有详细内容
            download_song_by_id(songs[i]['id'], folder)
    else:
        song_id = 0
        select_i = int(select)
        if select_i < 1 or select_i > len(songs):
            print 'ERROR: error select'
            return None
        else:
            download_song_by_id(songs[select_i-1]['id'], folder)

def download_album_by_search(name, folder='.'):
    albums = search_albums_by_name(name)
    if not albums:
        print 'Not found ' + to_str(name)
        return

    for i in range(len(albums)):
        album = albums[i]
        album_artist = album['artist']['name'].strip();
        album_name = album['name'].strip();
        print '[%2d]artist:%s\talbum:%s' % (i+1, to_str(album_artist), to_str(album_name))

    #输入所选项
    select = str(raw_input('Select One(Empty for all):')).strip();
    if select == '':
        for i in range(len(albums)):
            download_album(albums[i],folder)
    else:
        album_id = 0
        select_i = int(select)
        if select_i < 1 or select_i > len(albums):
            print 'error select'
            return None
        else:
            download_album(albums[select_i-1],folder)

def to_valid_path(string):
    #return string.replace('/','-')
    dic={
        '/'  : '',
        '\\' : '',
        '*'  : '',
        '?'  : '',
        '<'  : '',
        '>'  : '',
        '|'  : '',
        '"'  : ''
    }
    return multiple_replace(string,dic)

def multiple_replace(string, rep_dict):
    pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)

def to_str(unicode):
    return unicode.encode(stdout_encode,'replace')

if __name__ == '__main__':
    if len(sys.argv) != 4:
	    #print 'usage : python %s keyword savepath' % (sys.argv[0])
        stype = raw_input('Input type(song or album):').decode(stdin_encode).strip()        
        keyword = raw_input('Input keyword:').decode(stdin_encode).strip()
        savepath = raw_input('Input savepath:').decode(stdin_encode).strip()
        if savepath == '':
            savepath = '.'
    else:
        stype = sys.argv[1].decode(stdin_encode)
        keyword = sys.argv[2].decode(stdin_encode)
        savepath = sys.argv[3].decode(stdin_encode)
        if savepath == '':
            savepath = '.'
    if stype == 'song':
        download_song_by_search(keyword, savepath)
    elif stype == 'album':
        download_album_by_search(keyword, savepath)
    else:
        print "ERROR: type error"
    raw_input('Finished, press any key to exit')

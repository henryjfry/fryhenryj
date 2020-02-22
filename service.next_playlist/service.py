import time
import xbmc
import xbmcaddon
import json
import re
import urllib

import sys
import ntpath
import os.path

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')

db_path = str(xbmc.translatePath('special://database')) + 'MyVideos116.db'
update_playlist_path = str(xbmc.translatePath('special://userdata').replace('userdata','addons'))+str(__addonid__)

if ':' in update_playlist_path:
    update_playlist_path = update_playlist_path +'\emptywidget.xsp'
else:
    update_playlist_path = update_playlist_path +'/emptywidget.xsp'

#check whether or not playlist file exists create it if not (dummy playlist used to trigger widget updates)
if os.path.exists(update_playlist_path) == False:
    xml_playlist = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + "\n" + '<smartplaylist type="episodes">'
    xml_playlist = xml_playlist + "\n" + '<name>workaround for empty widget used for refreshes</name>' + "\n" + '<match>all</match>'
    xml_playlist = xml_playlist + "\n" + '<rule field="year" operator="greaterthan">' + "\n" + '<value>2200</value>' + "\n" + '</rule>'
    xml_playlist = xml_playlist + "\n" + '<limit>1</limit>' + "\n" +  '</smartplaylist>'
    f = open(update_playlist_path, "w")
    f.write(xml_playlist)
    f.close()

def movietitle_to_id(title):
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetMovies",
            "params": {
                "properties": ["title"]
            },
            "id": "libMovies"
        }
        try:
            jsonrpccommand=json.dumps(query, encoding='utf-8')	
            rpc_result = xbmc.executeJSONRPC(jsonrpccommand)
            json_result = json.loads(rpc_result)
            if 'result' in json_result and 'movies' in json_result['result']:
                json_result = json_result['result']['movies']
                for movie in json_result:
                    # Switch to ascii/lowercase and remove special chars and spaces
                    # to make sure best possible compare is possible
                    titledb = movie['title'].encode('ascii', 'ignore')
                    titledb = re.sub(r'[?|$|!|:|#|\.|\,|\'| ]', r'', titledb).lower().replace('-', '')
                    if '(' in titledb:
                        titledb = titledb.split('(')[0]
                    titlegiven = title.encode('ascii','ignore')
                    titlegiven = re.sub(r'[?|$|!|:|#|\.|\,|\'| ]', r'', titlegiven).lower().replace('-', '')
                    if '(' in titlegiven:
                        titlegiven = titlegiven.split('(')[0]
                    if titledb == titlegiven:
                        return movie['movieid']
            return '-1'
        except Exception:
            return '-1' 

class XBMCPlayer( xbmc.Player ):

    def __init__( self, *args ):
        pass

    def onPlayBackStarted( self ):

	for i in range(30):
		if xbmc.getCondVisibility('Player.HasVideo'):
			xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
			break
		xbmc.sleep(1000)

#        json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params": {"labels": ["ListItem.DBID" ]}, "id":1}')
        json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params": {"labels":["VideoPlayer.Title", "Player.Filenameandpath", "VideoPlayer.MovieTitle", "VideoPlayer.TVShowTitle", "VideoPlayer.DBID", "VideoPlayer.Duration", "VideoPlayer.Season", "VideoPlayer.Episode", "VideoPlayer.DBID", "VideoPlayer.Year", "VideoPlayer.Rating", "VideoPlayer.mpaa", "VideoPlayer.Studio", "VideoPlayer.VideoAspect", "VideoPlayer.Plot", "VideoPlayer.RatingAndVotes", "VideoPlayer.Genre", "VideoPlayer.LastPlayed", "VideoPlayer.IMDBNumber", "ListItem.DBID", "Container.FolderPath", "Container.FolderName", "Container.PluginName", "ListItem.TVShowTitle", "ListItem.FileNameAndPath"]}, "id":1}')
	json_object  = json.loads(json_result)
	title = ''
	imdb_id = json_object['result']['VideoPlayer.IMDBNumber']
	if imdb_id == '':
		try: 
#			imdb_id = re.search('imdb=(.+?)&mode', json_object['result']['Player.Filenameandpath']).group(1)
			imdb_id = re.search('imdb=(.+?)&', json_object['result']['Player.Filenameandpath']).group(1)
		except:
			imdb_id = '' 
	if imdb_id == '':
		try:
			imdb_url = str(json_object['result']['Player.Filenameandpath'])
			m = re.findall('=tt'+r'\d{6,7}', imdb_url)
			imdb = m[0].replace('=','')
			if 'tt' in imdb and len(imdb) == 9:
				imdb = imdb
			else:
				imdb_id = ''	
		except:
			imdb_id = '' 

        xbmc.log(str(json_object)+'===>service.next_playlist1', level=xbmc.LOGNOTICE)
	if json_object['result']['VideoPlayer.TVShowTitle'] <> '':
		title = json_object['result']['VideoPlayer.TVShowTitle'] + ' - S'+str(json_object['result']['VideoPlayer.Season']).zfill(2) +'E'+str(json_object['result']['VideoPlayer.Episode']).zfill(2) +' - ' +  json_object['result']['VideoPlayer.Title']
#	url = "plugin://plugin.video.openmeta/tv/play_by_name/" + urllib.quote_plus(json_object['result']['VideoPlayer.TVShowTitle']) +"/" + str(json_object['result']['VideoPlayer.Season']) + "/" + str(json_object['result']['VideoPlayer.Episode']) + "/" +  urllib.quote_plus(json_object['result']['VideoPlayer.Title'])
#	url = "plugin://plugin.video.themoviedb.helper?info=play2&amp;query=" + urllib.quote_plus(json_object['result']['VideoPlayer.TVShowTitle']) + "&amp;type=episode&amp;season=" + str(json_object['result']['VideoPlayer.Season']) + "&amp;episode=" + str(json_object['result']['VideoPlayer.Episode']) 
#	url = "plugin://plugin.video.openmeta/play_stream/info?type=episode&amp;query=" + urllib.quote_plus(json_object['result']['VideoPlayer.TVShowTitle']) + "&amp;season=" + str(json_object['result']['VideoPlayer.Season']) + "&amp;episode=" + str(json_object['result']['VideoPlayer.Episode']) 
	url = "plugin://plugin.video.themoviedb.helper?info=play4&amp;type=episode&amp;query=" + urllib.quote_plus(json_object['result']['VideoPlayer.TVShowTitle']) + "&amp;season=" + str(json_object['result']['VideoPlayer.Season']) + "&amp;episode=" + str(json_object['result']['VideoPlayer.Episode']) 
#	url = "plugin://plugin.video.themoviedb.helper?info=play&amp;type=episode&amp;query=" + urllib.quote_plus(json_object['result']['VideoPlayer.TVShowTitle']) + "&amp;season=" + str(json_object['result']['VideoPlayer.Season']) + "&amp;episode=" + str(json_object['result']['VideoPlayer.Episode'])  + "&amp;islocal=true" 

        if json_object['result']['VideoPlayer.MovieTitle'] <> '':
		title = json_object['result']['VideoPlayer.MovieTitle']
		if imdb_id == '':
#			url = str(json_object['result']['Player.Filenameandpath']).replace("action=getSources&", "action=smartPlay&getSources=True&")
			url = u' '.join((json_object['result']['Player.Filenameandpath'])).encode('utf-8').replace("action=getSources&", "action=smartPlay&getSources=True&")
		else:
#			url = "plugin://plugin.video.openmeta/movies/play/tmdb/" + imdb_id
#			url = "plugin://plugin.video.themoviedb.helper?info=play2&amp;imdb_id=" + imdb_id + "&amp;type=movie"
#			url = "plugin://plugin.video.openmeta/play_stream/info?type=movie&amp;imdb_id=" + imdb_id
			url = "plugin://plugin.video.themoviedb.helper?info=play4&amp;type=movie&amp;imdb_id=" + imdb_id
#			url = "plugin://plugin.video.themoviedb.helper?info=play&amp;type=movie&amp;imdb_id=" + imdb_id + "&amp;islocal=true"

	if json_object['result']['VideoPlayer.Title'] <> '' and title == '':
		title = json_object['result']['VideoPlayer.Title'] + ' (' + json_object['result']['VideoPlayer.Year'] + ')'

		if imdb_id == '':
			try: 
#				imdb_id = re.search('imdb=(.+?)&mode', json_object['result']['Player.Filenameandpath']).group(1)
				imdb_id = re.search('imdb=(.+?)&', json_object['result']['Player.Filenameandpath']).group(1)
			except:
				imdb_id = '' 
		if imdb_id == '':
			try:
				imdb_url = str(json_object['result']['Player.Filenameandpath'])
				m = re.findall('=tt'+r'\d{6,7}', imdb_url)
				imdb = m[0].replace('=','')
				if 'tt' in imdb and len(imdb) == 9:
					imdb = imdb
				else:
					imdb_id = ''	
			except:
				imdb_id = '' 

		if imdb_id == '':
			url = str(json_object['result']['Player.Filenameandpath']).replace("action=getSources&", "action=smartPlay&getSources=True&")
		else:
#			url = "plugin://plugin.video.openmeta/movies/play/tmdb/" + imdb_id
#			url = "plugin://plugin.video.themoviedb.helper?info=play2&amp;imdb_id=" + imdb_id + "&amp;type=movie&amp;year=" + json_object['result']['VideoPlayer.Year']
#			url = "plugin://plugin.video.openmeta/play_stream/info?type=movie&amp;imdb_id=" + imdb_id + "&amp;year=" + json_object['result']['VideoPlayer.Year']
			url = "plugin://plugin.video.themoviedb.helper?info=play4&amp;type=movie&amp;imdb_id=" + imdb_id + "&amp;year=" + json_object['result']['VideoPlayer.Year']
#			url = "plugin://plugin.video.themoviedb.helper?info=play&amp;type=movie&amp;imdb_id=" + imdb_id + "&amp;year=" + json_object['result']['VideoPlayer.Year'] + "&amp;islocal=true"
	try:
		xml_str = "\n" + '#EXTINF:,'+title + "\n" + url  + "\n"
		xbmc.log(str(title)+', '+str(url)+'===>OPENMETA1', level=xbmc.LOGNOTICE)
	except:
		xml_str = "\n" + '#EXTINF:,'+ json_object['result']['VideoPlayer.Title'] + '' + "\n" + url  + "\n"
		xbmc.log(str(json_object['result']['VideoPlayer.Title'])+', '+str(url)+'===>OPENMETA1', level=xbmc.LOGNOTICE)
	
#	FileNameAndPath = json_object['result']['ListItem.FileNameAndPath']
#	if '.strm' in FileNameAndPath:
#		is_local = True
#	else:
#		is_local = False

#	f = open("/mnt/Torrent/Movies/playlist.m3u", "a")
#	f.write(xml_str)
#	f.close()

	if str(title) == '' or str(json_object['result']['VideoPlayer.Title']) == '':
		xbmc.log(str('DONT_WRITE_PLAYLIST')+'===>service.next_playlist2', level=xbmc.LOGNOTICE)
	else:
		xbmc.log(str('WRITE_PLAYLIST')+'===>service.next_playlist2', level=xbmc.LOGNOTICE)
		f = open("/mnt/Torrent/Movies/playlist.m3u", "a")
		f.write(xml_str)
		f.close()
        
#	dbID = (json_object['result']['ListItem.DBID'])
#        Will be called when xbmc starts playing a file
        watched = 0
        while player.isPlaying()==1:
            xbmc.sleep(10000)
            if player.isPlayingVideo()==1 and watched == 0:
                json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params": {"labels":["VideoPlayer.Title", "Player.Filenameandpath", "VideoPlayer.MovieTitle", "VideoPlayer.TVShowTitle", "VideoPlayer.DBID", "VideoPlayer.Duration", "VideoPlayer.Season", "VideoPlayer.Episode", "VideoPlayer.DBID"]}, "id":1}')
                json_object  = json.loads(json_result)
                timestamp = json_object['result']['VideoPlayer.Duration']
                duration = reduce(lambda x, y: x*60+y, [int(i) for i in (timestamp.replace(':',',')).split(',')])
                dbID = json_object['result']['VideoPlayer.DBID']
                title = json_object['result']['VideoPlayer.Title']
                movie_title = json_object['result']['VideoPlayer.MovieTitle']
                tv_show_name = json_object['result']['VideoPlayer.TVShowTitle']
                season_num = json_object['result']['VideoPlayer.Season']
                ep_num = json_object['result']['VideoPlayer.Episode']
                movie_id = movietitle_to_id(title)
                try:
                    prev_ep_num = int(json_object['result']['VideoPlayer.Episode'])-1
                except:
                    prev_ep_num = ""
                    wacthed = 1
                xbmc.log("PLAYBACK STARTED %s" % time.time() + '  ,'+str(dbID)+'=dbID, '+str(duration)+'=duration, '+str(tv_show_name)+'=tv_show_name, '+str(season_num)+'=season_num, '+str(ep_num)+'=ep_num, '+str(title)+', '+str(movie_title)+ '  ,'+str(movie_id)+'=movie_ID'+', '+str(prev_ep_num)+'=prev_ep_num', level=xbmc.LOGNOTICE)

#		xbmc.log(str(wacthed)+'=watched status, '+str(movie_id)+'=dbID', level=xbmc.LOGNOTICE)

                if str(movie_id) != str(-1):
                    wacthed = 1   
                    json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"VideoLibrary.GetMovieDetails","params":{"movieid":'+str(movie_id)+', "properties": ["playcount"]}}')
                    json_object  = json.loads(json_result)
	            play_count = int(json_object['result']['moviedetails']['playcount'])+1

	            while player.isPlayingVideo()==1 and watched == 0:
        	        xbmc.sleep(10000)
                        try:
                            percentage = (player.getTime() / duration) * 100
                        except:
                            watched = 1
                            break
                        if (percentage > 85) and player.isPlayingVideo()==1:
                            xbmc.log(str(percentage)+'pc, '+str(movie_id)+'=dbID', level=xbmc.LOGNOTICE)
                            json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"VideoLibrary.SetMovieDetails","params":{"movieid":'+str(movie_id)+',"playcount": '+str(play_count)+'},"id":"1"}')
                            json_object  = json.loads(json_result)
        	            xbmc.log(str(json_object)+'=episode marked watched, '+str(movie_id)+'=dbID', level=xbmc.LOGNOTICE)
                            watched = 1
#                           break

                if dbID == "" and watched == 0:               
                    json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "params": {"sort": {"order": "ascending", "method": "title"}, "filter": {"operator": "is", "field": "title", "value": "'+tv_show_name+'"}, "properties": []}, "method": "VideoLibrary.GetTVShows", "id": 1}')
                    json_object  = json.loads(json_result)
                    try:
                        tv_show_num = json_object['result']['tvshows'][0]['tvshowid']
                    except:
                        watched = 1
                        return
                    json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1 , "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": '+str(tv_show_num)+', "season": '+str(season_num)+', "properties": [], "limits": {"start": '+str(prev_ep_num)+', "end": '+str(ep_num)+'}}}')
                    json_object  = json.loads(json_result)

                    try:
                        dbID = json_object['result']['episodes'][0]['episodeid']
                    except:
                        watched = 1
                        return

                if dbID != "":   
                    json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"VideoLibrary.GetEpisodeDetails","params":{"episodeid":'+str(dbID)+', "properties": ["playcount"]}}')
                    json_object  = json.loads(json_result)
	            play_count = int(json_object['result']['episodedetails']['playcount'])+1

                    while player.isPlayingVideo()==1 and watched == 0:
                        xbmc.sleep(10000)
                        try:
                            percentage = (player.getTime() / duration) * 100
                        except:
                            watched = 1
                            break
                        if (percentage > 85) and player.isPlayingVideo()==1:
                            xbmc.log(str(percentage)+'pc, '+str(dbID)+'=dbID', level=xbmc.LOGNOTICE)
                            json_result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"VideoLibrary.SetEpisodeDetails","params":{"episodeid":'+str(dbID)+',"playcount": '+str(play_count)+'},"id":"1"}')
                            json_object  = json.loads(json_result)
                            xbmc.log(str(json_object)+'=episode marked watched, '+str(dbID)+'=dbID', level=xbmc.LOGNOTICE)
                            watched = 1
#                            break

#            tag = xbmc.Player().getVideoInfoTag()
#            dbID = tag.getDbId()
#            xbmc.log(str(xbmc.Player().getTime()), level=xbmc.LOGNOTICE)
#            xbmc.log(str(file), level=xbmc.LOGNOTICE)
#            percentage = (player.getTime() / player.getVideoInfoTag().getDuration()) * 100
#            xbmc.log(str(player.getTime() / player.getVideoInfoTag().getDuration())+'pc', level=xbmc.LOGNOTICE)
#            xbmc.log(str(percentage)+'pc', level=xbmc.LOGNOTICE)
#            xbmc.log(str(xbmc.getInfoLabel('VideoPlayer.episodeid'))+'=dbID', level=xbmc.LOGNOTICE)
#            xbmc.log(str(xbmc.getInfoLabel('VideoPlayer.Season'))+'=seasoin', level=xbmc.LOGNOTICE)
#            json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "album", "artist", "season", "episode", "duration", "showtitle", "tvshowid", "thumbnail", "file", "fanart", "streamdetails"], "playerid": 1 }, "id": "VideoGetItem"}')
#            xbmc.log(str(json_data)+'=dbID ', level=xbmc.LOGNOTICE)

    def onPlayBackEnded( self ):
#        Will be called when xbmc stops playing a file
#        xbmc.log(str(player.isPlayingVideo()==True)+"%s" % time.time(), level=xbmc.LOGNOTICE)
#        xbmc.log("PLAYBACK ENDED %s" % time.time(), level=xbmc.LOGNOTICE)
        kodi_playlist_generate()

    def onPlayBackStopped( self ):
#        Will be called when user stops xbmc playing a file
#        xbmc.log("PLAYBACK STOPPED %s" % time.time(), level=xbmc.LOGNOTICE)
        kodi_playlist_generate()

class KodiMonitor(xbmc.Monitor):

    def __init__(self, **kwargs):
        xbmc.Monitor.__init__(self)

    def onDatabaseUpdated(self, database):
        if database == "video":
	    kodi_playlist_generate()
#            xbmc.log("LIBRARY SCAN! %s" % time.time(), level=xbmc.LOGNOTICE)

    def onNotification(self, sender, method, data):
        if (method == 'VideoLibrary.OnUpdate'):
            kodi_playlist_generate()
#            xbmc.log("WATCHED/UNWATCHED %s" % time.time(), level=xbmc.LOGNOTICE)
#            response = json.loads(data)          
#            if (response.has_key('item') and response['item'].has_key('type') and response.get('item').get('type') == 'episode'): # Episode means it is a TV show
#                episodeid = response.get('item').get('id')
#                playcount = response.get('playcount')
#                if (playcount > 0): # If it has been watched 
#                    xbmc.log("WATCHED! %s" % time.time(), level=xbmc.LOGNOTICE)


def kodi_playlist_generate():

	mysql_enabled = __addon__.getSetting('mysql_enabled')

	if mysql_enabled == 'false':
		import sqlite3
		#con = sqlite3.connect('/home/osmc/.kodi/userdata/Database/MyVideos116.db')
		con = sqlite3.connect(db_path)

	if mysql_enabled == 'true':
		import mysql.connector
		sql_username = __addon__.getSetting('username')
		sql_password = __addon__.getSetting('password')
		sql_host = __addon__.getSetting('host')
		sql_port = __addon__.getSetting('port')
		sql_db_name = __addon__.getSetting('db_name')
		con = mysql.connector.connect(host=sql_host, user=sql_username, passwd=sql_password, port=sql_port, db=sql_db_name)

	cur = con.cursor()
#	playlist_path = 'special://profile/playlists/video'
	playlist_path = str(xbmc.translatePath('special://profile/playlists/video')) + '/'

	sql_method = int(__addon__.getSetting('sql_method'))+1

	if sql_method == 1:
	#next up tv shows (in progress only) ordered by airdate
		cur.execute("select idepisode, c18, c13, tvshow1, genre, idshow, idseason, episode1 from (select idseason, files.idfile, episode.c00 as episode1, episode.c18, episode.c12, episode.c13, episode.c05, tvshow.c08 as genre, idepisode, tvshow.c00 as tvshow1, episode.idShow, playcount, lastplayed from episode, files, tvshow where (episode.idfile = files.idfile) and (episode.idshow = tvshow.idshow) and files.idfile in (select idfile from (select min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 from episode, files, tvshow where (episode.idfile = files.idfile) and (episode.idshow = tvshow.idshow) and playcount is null group by tvshow.c00) as a)) as b where (idshow in (select idshow from (select files.idfile, episode.c00 as episode1, episode.c05, idepisode, tvshow.c00 as tvshow1, episode.idShow, playcount, lastplayed from episode, files, tvshow where (episode.idfile = files.idfile) and (episode.idshow = tvshow.idshow) and files.idfile in (select idfile from (select max(files.idfile) as idfile, max(episode.c05) as firstaired, tvshow.c00 from episode, files, tvshow where (episode.idfile = files.idfile) and (episode.idshow = tvshow.idshow) and playcount > 0 group by tvshow.c00) as c))as d)) and c05 < current_date order by c05 desc;")
		sql_result = cur.fetchall()

	if sql_method == 2:
	#next up all tv shows ordered by airdate
		cur.execute("select idepisode, c18, c13, tvshow1, genre, idshow, idseason from (SELECT idseason, files.idfile, episode.c00 as episode1, episode.c18, episode.c12, episode.c13, episode.c05, tvshow.c08 as genre, idepisode, tvshow.c00 as tvshow1, episode.idShow, playcount, lastplayed from episode, files, tvshow where (episode.idfile = files.idfile) and (episode.idshow = tvshow.idshow) and files.idfile in (select idfile from (SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM episode, files, tvshow where (episode.idfile = files.idfile) and (episode.idshow = tvshow.idshow) and playcount is null GROUP BY tvshow.c00) as a)) as b where c05 < current_date order by c05 desc;")
		sql_result = cur.fetchall()


	big_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + "\n" + '<smartplaylist type="episodes">'  + "\n" 
	big_xml = big_xml + '    <name>NEXT EPISODES PLAYLIST</name>' + "\n" + '    <match>one</match>'

	for k in sql_result:
		path_str = k[1]
		base_name = ntpath.basename(path_str)
		big_xml = big_xml + "\n" + '    <rule field=\"filename\" operator=\"is\"><value>'+ base_name +'</value></rule>'

        sort_order_str = str(__addon__.getSetting('sort_order_str'))
        sort_order_direction = str(__addon__.getSetting('sort_order_direction'))
	big_xml = big_xml + "\n"+'    <order direction=\"'+sort_order_direction+'ending\">'+sort_order_str+'</order><virtualfolder>true</virtualfolder></smartplaylist>'

	f = open(playlist_path + "NEXT_EPISODES_PLAYLIST.xsp", "w")
	f.write(big_xml)
	f.close()

	cur.close()
#        xbmc.log(sort_order_direction+sort_order_str+"PLAYLIST!!!!! %s" % time.time(), level=xbmc.LOGNOTICE)
	pass

player = XBMCPlayer()
monitor = KodiMonitor()

while(not xbmc.abortRequested):
    xbmc.sleep(500)
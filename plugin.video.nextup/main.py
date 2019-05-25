# -*- coding: utf-8 -*-
# Module: default
# Author: fryhenryj
# Created on: 24.05.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import xbmc
import xbmcgui
import xbmcplugin
import json

import sqlite3
con = sqlite3.connect('/home/osmc/.kodi/userdata/Database/MyVideos116.db')
cur = con.cursor()

addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'episodes')

#next up tv shows (in progress only) ordered by airdate
sql_result = (cur.execute(" select idepisode,c18,c13,show,genre from (SELECT files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, lastplayed from episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where idshow in (select idshow from(SELECT files.idfile, episode.c00, episode.c05, idepisode, tvshow.c00, episode.idShow, playcount, lastplayed from episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and files.idfile in (select idfile from(SELECT max(files.idfile) as idfile, max(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount>0   GROUP BY tvshow.c00) ) )) and c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by c05 desc").fetchall())

#next up all tv shows ordered by airdate
#sql_result = (cur.execute(" select idepisode,c18,c13,show,genre from (SELECT files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, lastplayed from episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by c05 desc").fetchall())

#next up all tv shows sorted by last played then date aired for unwatched shows.
#sql_result = (cur.execute("select idepisode,c18,c13,show,genre,case when tvlastplayed > c05 then tvlastplayed else c05 end as tvlastplayed from (SELECT files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, files.lastplayed, tvshowcounts.lastplayed as tvlastplayed from episode, files, tvshow, tvshowcounts where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and episode.idshow = tvshowcounts.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by tvlastplayed desc, c05 desc").fetchall())

#next up tv shows (in progress only) ordered by the last time the show was played
#sql_result = (cur.execute(" select idepisode,c18,c13,show, genre,case when tvlastplayed > c05 then tvlastplayed else c05 end as tvlastplayed from (SELECT files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, files.lastplayed, tvshowcounts.lastplayed as tvlastplayed from episode, files, tvshow, tvshowcounts where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and episode.idshow = tvshowcounts.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where idshow in (select idshow from(SELECT files.idfile, episode.c00, episode.c05, idepisode, tvshow.c00, episode.idShow, playcount, files.lastplayed, tvshowcounts.lastplayed from episode, files, tvshow, tvshowcounts where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and episode.idshow = tvshowcounts.idshow and files.idfile in (select idfile from(SELECT max(files.idfile) as idfile, max(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount>0   GROUP BY tvshow.c00) ) )) and c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by tvlastplayed desc").fetchall())

cur.close()

for k in sql_result:
    xbmc.log(str(k[4]), level=2)

    kodi_params = ('{"jsonrpc":"2.0","id":1,"method":"VideoLibrary.GetEpisodeDetails","params":{"episodeid":'+str(k[0])+', "properties": ["title", "plot", "votes", "rating", "writer", "firstaired", "playcount", "runtime", "director", "productioncode", "season", "episode", "originaltitle", "showtitle", "cast", "streamdetails", "lastplayed", "fanart", "thumbnail", "file", "resume", "tvshowid", "dateadded", "uniqueid", "art"]}}')


    request = xbmc.executeJSONRPC(kodi_params)
#    xbmc.log(request)
    json_data = json.loads(request)
#    xbmc.log(print(json_data['result']['episodedetails']), level=2)
#    xbmc.log(xbmc.executeJSONRPC(kodi_params), level=2)

    #listing.append((url, list_item, is_folder))

#    xbmc.log(json_data['result']['episodedetails']['art']['tvshow.banner'], level=2)
    list_item = xbmcgui.ListItem(label=json_data['result']['episodedetails']['title'], thumbnailImage=json_data['result']['episodedetails']['thumbnail'])
    list_item.setProperty('fanart_image', json_data['result']['episodedetails']['fanart'])
    list_item.setInfo('video', {'title': json_data['result']['episodedetails']['title'], 'plot': json_data['result']['episodedetails']['plot'], 'path': json_data['result']['episodedetails']['file'],'premiered': json_data['result']['episodedetails']['firstaired'], 'aired': json_data['result']['episodedetails']['firstaired'], 'dbid': str(k[0]), 'tvshowtitle': json_data['result']['episodedetails']['showtitle'], 'season': json_data['result']['episodedetails']['season'], 'episode': json_data['result']['episodedetails']['episode']})
    list_item.setArt({ 'poster': json_data['result']['episodedetails']['art']['tvshow.poster'], 'banner' : json_data['result']['episodedetails']['art']['tvshow.banner']})


    list_item.setProperty('IsPlayable', 'true')

    url = json_data['result']['episodedetails']['file']
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item)

xbmcplugin.endOfDirectory(addon_handle)
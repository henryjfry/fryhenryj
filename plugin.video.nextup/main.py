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

db_path = str(xbmc.translatePath('special://database')) + 'MyVideos116.db'

import sqlite3
con = sqlite3.connect(db_path)
cur = con.cursor()

addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'episodes')

#next up tv shows (in progress only) ordered by airdate
sql_result = (cur.execute(" select idepisode,c18,c13,show,genre,idshow,idseason from (SELECT idseason ,files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, lastplayed from episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where idshow in (select idshow from(SELECT files.idfile, episode.c00, episode.c05, idepisode, tvshow.c00, episode.idShow, playcount, lastplayed from episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and files.idfile in (select idfile from(SELECT max(files.idfile) as idfile, max(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount>0   GROUP BY tvshow.c00) ) )) and c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by c05 desc").fetchall())

#next up all tv shows ordered by airdate
#sql_result = (cur.execute(" select idepisode,c18,c13,show,genre,idshow,idseason from (SELECT idseason,files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, lastplayed from episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by c05 desc").fetchall())

#next up all tv shows sorted by last played then date aired for unwatched shows.
#sql_result = (cur.execute("select idepisode,c18,c13,show,genre,idshow,idseason,case when tvlastplayed > c05 then tvlastplayed else c05 end as tvlastplayed from (SELECT idseason,files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, files.lastplayed, tvshowcounts.lastplayed as tvlastplayed from episode, files, tvshow, tvshowcounts where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and episode.idshow = tvshowcounts.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by tvlastplayed desc, c05 desc").fetchall())

#next up tv shows (in progress only) ordered by the last time the show was played
#sql_result = (cur.execute(" select idepisode,c18,c13,show, genre,idshow,idseason,case when tvlastplayed > c05 then tvlastplayed else c05 end as tvlastplayed from (SELECT idseason,files.idfile, episode.c00, episode.c18, episode.c12, episode.c13, episode.c05,tvshow.c08 as genre, idepisode, tvshow.c00 as show, episode.idShow, playcount, files.lastplayed, tvshowcounts.lastplayed as tvlastplayed from episode, files, tvshow, tvshowcounts where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and episode.idshow = tvshowcounts.idshow and files.idfile in (select idfile from(SELECT min(files.idfile) as idfile, min(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount is null   GROUP BY tvshow.c00) )  ) where idshow in (select idshow from(SELECT files.idfile, episode.c00, episode.c05, idepisode, tvshow.c00, episode.idShow, playcount, files.lastplayed, tvshowcounts.lastplayed from episode, files, tvshow, tvshowcounts where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and episode.idshow = tvshowcounts.idshow and files.idfile in (select idfile from(SELECT max(files.idfile) as idfile, max(episode.c05) as firstaired, tvshow.c00 FROM  episode, files, tvshow where episode.idfile=files.idfile and episode.idshow = tvshow.idshow and playcount>0   GROUP BY tvshow.c00) ) )) and c05 < strftime('%Y-%m-%d', CURRENT_TIMESTAMP) order by tvlastplayed desc").fetchall())

cur.close()

for k in sql_result:
#    xbmc.log(str(k[6]), level=2)

    kodi_params = ('{"jsonrpc":"2.0","id":1,"method":"VideoLibrary.GetEpisodeDetails","params":{"episodeid":'+str(k[0])+', "properties": ["title", "plot", "votes", "rating", "writer", "firstaired", "playcount", "runtime", "director", "productioncode", "season", "episode", "originaltitle", "showtitle", "cast", "streamdetails", "lastplayed", "fanart", "thumbnail", "file", "resume", "tvshowid", "dateadded", "uniqueid", "art"]}}')
    kodi_params += ','
    kodi_params += ('{"jsonrpc":"2.0","id":1,"method":"VideoLibrary.GetTVShowDetails","params":{"tvshowid":'+str(k[5])+', "properties": ["title","genre","year","rating","plot","studio","mpaa","cast","playcount","episode","imdbnumber","premiered","votes","lastplayed","fanart","thumbnail","file","originaltitle","sorttitle","episodeguide","season","watchedepisodes","dateadded","tag","art","userrating","ratings","runtime","uniqueid"]}}')
    kodi_params += ','
    kodi_params += ('{"jsonrpc":"2.0","id":1,"method":"VideoLibrary.GetSeasonDetails","params":{"seasonid":'+str(k[6])+', "properties": ["art"]}}')

    kodi_params = '['+ kodi_params + ']'

    request = xbmc.executeJSONRPC(kodi_params)
    json_data = json.loads(request)
    episode_details = json_data[0]['result']
    tvshow_details = json_data[1]['result']['tvshowdetails']
    season_art = json_data[2]['result']['seasondetails']['art']

    label = episode_details['episodedetails']['showtitle']+' - S'+str(episode_details['episodedetails']['season']).rjust(2, '0')+'E'+str(episode_details['episodedetails']['episode']).rjust(2, '0')+ ' - '+episode_details['episodedetails']['title']

    list_item = xbmcgui.ListItem(label=label, thumbnailImage=episode_details['episodedetails']['thumbnail'])
    list_item.setProperty('fanart_image', episode_details['episodedetails']['fanart'])

    list_item.setProperty('startoffset', str(episode_details['episodedetails']['resume']['position']))

    list_item.setInfo('video', {'title': episode_details['episodedetails']['title'],'genre': str(k[4]), 'plot': episode_details['episodedetails']['plot'], 'path': episode_details['episodedetails']['file'],'premiered': episode_details['episodedetails']['firstaired'], 'aired': episode_details['episodedetails']['firstaired'], 'tvshowtitle': episode_details['episodedetails']['showtitle'], 'season': episode_details['episodedetails']['season'], 'episode': episode_details['episodedetails']['episode'], 'dbid': str(k[0]), 'mediatype': 'episode', 'writer': episode_details['episodedetails']['writer'], 'director': episode_details['episodedetails']['director'],  'code': episode_details['episodedetails']['productioncode'], 'showlink': episode_details['episodedetails']['showtitle']})

    try:
        list_item.setArt({ 'thumb': tvshow_details['art']['landscape'], "poster": season_art['poster'], "banner": season_art['tvshow.banner'], "fanart": season_art['tvshow.fanart'], "landscape": tvshow_details['art']['landscape']})
    except:
        try:
            list_item.setArt({ 'thumb': season_art['tvshow.fanart'], "poster": season_art['poster'], "banner": season_art['tvshow.banner'], "fanart": season_art['tvshow.fanart'], "landscape": season_art['tvshow.fanart']})
        except:
            try:
                list_item.setArt({ 'thumb': season_art['tvshow.fanart'], "poster": season_art['tvshow.poster'], "banner": season_art['tvshow.banner'], "fanart": season_art['tvshow.fanart'], "landscape": season_art['tvshow.fanart']})
            except:
                list_item.setArt({ 'poster': tvshow_details['art']['poster'], 'thumb': tvshow_details['fanart'], 'banner' : tvshow_details['art']['banner']})
                try:
                    list_item.setArt({ 'poster': tvshow_details['art']['poster'], 'thumb': tvshow_details['fanart'], 'banner' : tvshow_details['art']['banner']})
                except: 
                    try:
                        list_item.setArt({ 'poster': tvshow_details['art']['poster'], 'thumb': tvshow_details['fanart']})
                    except:
                        try:
                            list_item.setArt({ 'poster': tvshow_details['art']['poster']})
                        except:
                            pass

    url = episode_details['episodedetails']['file']
    list_item.setProperty('IsPlayable', 'true')

    commands = []
#    commands.append(( 'InformationXBMC','XBMC.InfoTagVideo()', ))
    commands.append(( 'Browse Series','XBMC.ActivateWindow(10025,"videodb://tvshows/titles/' +str(k[5])+'/",return)', ))
    list_item.addContextMenuItems(commands)

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=list_item)

xbmcplugin.endOfDirectory(addon_handle)
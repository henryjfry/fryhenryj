# -*- coding: utf-8 -*-
# Module: default
# Author: fryhenryj
# Created on: 24.05.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import routing

plugin = routing.Plugin()

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')

update_playlist_path = str(xbmc.translatePath('special://userdata').replace('userdata','addons'))+str(__addonid__)

if ':' in update_playlist_path:
    update_playlist_path = update_playlist_path +'\emptywidget.xsp'
else:
    update_playlist_path = update_playlist_path +'/emptywidget.xsp'

@plugin.route('/settings')
def open_settings():
	__addon__.openSettings()

@plugin.route('/')
def run_addon():
	__addon__.openSettings()

@plugin.route('/update_widget_method')
def open_update_widget():
        xbmc.executebuiltin('PlayMedia(update_playlist_path)')
        xbmc.sleep(1500)
        xbmc.executebuiltin('XBMC.ReloadSkin()')
        xbmc.sleep(1500)
        xbmc.executebuiltin('PlayMedia(update_playlist_path)')

#	xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":'+__addonid__+',"enabled":false},"id":1}')
#	__addon__.SetAddonEnabled('false')
#
#        json = '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"service.next_playlist","enabled":false},"id":1}'
#        result = xbmc.executeJSONRPC(json)
#
#       xbmc.sleep(10500)
#	__addon__.SetAddonEnabled('true')
#        json = '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"service.next_playlist","enabled":true},"id":1}'
#        result = xbmc.executeJSONRPC(json)
#	xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":'+__addonid__+',"enabled":true},"id":1}')
#        xbmc.executebuiltin('PlayMedia(update_playlist_path)')

@plugin.route('/update_widget')
def open_update_widget():
        xbmc.executebuiltin('PlayMedia(update_playlist_path)')
	xbmc.sleep(2000)
        xbmc.executebuiltin('PlayMedia(update_playlist_path)')

#plugin routing startup
if __name__ == '__main__':
    plugin.run()
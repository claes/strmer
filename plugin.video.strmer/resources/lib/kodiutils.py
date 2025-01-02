'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import os
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs


class AddonUtils():
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.name = self.addon.getAddonInfo("name")
        self.id = self.addon.getAddonInfo("id")
        self.handle = int(sys.argv[1])
        self.url = sys.argv[0]
        self.icon = os.path.join(self.addon.getAddonInfo("path"), "icon.png")
        self.fanart = os.path.join(self.addon.getAddonInfo("path"), "fanart.jpg")
        self.profile_dir = xbmcvfs.translatePath(self.addon.getAddonInfo("Profile"))
        os.makedirs(self.profile_dir, exist_ok=True)
        self.cache_file = xbmcvfs.translatePath(os.path.join(self.profile_dir,
                                                             "requests_cache"))

    def view_menu(self, menu):
        items = []
        for item in menu:
            li = xbmcgui.ListItem(label=item.title, offscreen=True)
            li.setArt({"thumb": item.icon})
            li.setInfo("video", {"title": item.title})
            if item.playable:
                li.setProperty("IsPlayable", "true")
                li.setInfo("video", {"plot": item.description})
            items.append((item.url, li, not item.playable))
        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)

    def url_for(self, url):
        return "plugin://{0}{1}".format(self.id, url)


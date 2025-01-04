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
import requests
import xbmc
import xbmcgui
import xbmcplugin
from resources.lib.streammanager import StreamManager
from resources.lib.kodiutils import AddonUtils
from urllib.parse import parse_qs

def run():

    addon_utils = AddonUtils()
    params = parse_qs(sys.argv[2][1:])
    page_size = 50

    sm = StreamManager(addon_utils)
    if "mode" in params:
        try:
            mode = params["mode"][0]
            page = int(params["page"][0]) if "page" in params else 1
            url = params["url"][0] if "url" in params else None
            title = params["title"][0] if "title" in params else None

            if mode == "streams":
                path = url
                contents = sm.get_streams(path, page, page_size)
                addon_utils.view_menu(contents)
            if mode == "watch":
                media_url = requests.utils.unquote(url)
                xbmcplugin.setResolvedUrl(
                    addon_utils.handle, True, xbmcgui.ListItem(path=media_url)
                )
            if mode == "queue":
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO )
                mode_url = addon_utils.mode_url("watch")
                media_url = requests.utils.quote(url)
                u = f"{mode_url}&url={media_url}"
                playlist_item = xbmcgui.ListItem(label=title, path=u)
                playlist.add(url, playlist_item)
            if mode == "queuedir":
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO )

                params2 = parse_qs(url)
                url2 = params2["url"][0] if "url" in params2 else None
                list_items = sm.get_streams(url2, 1, 100, include_dirs=False)

                for list_item in list_items:
                    if list_item.playable:
                        mode_url = addon_utils.mode_url("watch")
                        media_url_encoded = requests.utils.quote(list_item.url)
                        u = f"{mode_url}&url={media_url_encoded}"

                        playlist_item = xbmcgui.ListItem(label=list_item.title, path=u)
                        playlist.add(u, playlist_item)

        except Exception as e:
            addon_utils.show_error(e)
    else:
        addon_utils.view_menu(sm.get_streams("/", 1, page_size))

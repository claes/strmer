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

            if mode == "streams":
                path = url
                contents = sm.get_streams(path, page, page_size)
                addon_utils.view_menu(contents)
            if mode == "watch":
                media_url = requests.utils.unquote(url)
                xbmcplugin.setResolvedUrl(
                    addon_utils.handle, True, xbmcgui.ListItem(path=media_url)
                )

        except Exception as e:
            addon_utils.show_error(e)
    else:
        addon_utils.view_menu(sm.get_streams("/home/claes/tmp/Vimjoyer", 1, page_size))

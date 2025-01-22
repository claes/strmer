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

    stream_manager = StreamManager(addon_utils)
    if "mode" in params:
        try:
            mode = params["mode"][0]
            page = int(params["page"][0]) if "page" in params else 1
            url = params["url"][0] if "url" in params else None
            title = params["title"][0] if "title" in params else None

            if mode == "streams":
                path = url
                streams = stream_manager.get_streams(path, page, page_size)
                addon_utils.view_menu(streams)
            if mode == "watch":
                if url.startswith("http"):
                    media_url = url
                else:
                    media_url = requests.utils.unquote(url)

                xbmcplugin.setResolvedUrl(
                    addon_utils.handle, True, xbmcgui.ListItem(path=media_url)
                )
            if mode == "ytdlp":
                xbmc.log(f"YTDLP", xbmc.LOGERROR)
                xbmc.log(url, xbmc.LOGERROR)
                inner_params = parse_qs(url)
                path = inner_params["url"][0] if "url" in inner_params else None
                xbmc.log(path, xbmc.LOGERROR)

                youtube_id = addon_utils.extract_youtube_video_id(path)
                xbmc.log(youtube_id, xbmc.LOGERROR)
                youtube_url = addon_utils.get_youtube_url(youtube_id)
                xbmc.log(youtube_url, xbmc.LOGERROR)
                ytdlp_extracted_url = addon_utils.execute_ytdlp_get_url(youtube_url)
                xbmc.log("Play" + ytdlp_extracted_url, xbmc.LOGERROR)

                local_url = addon_utils.stream_ffmpeg(youtube_url)

                xbmc.log("Play local_url " + local_url, xbmc.LOGERROR)

                list_item = xbmcgui.ListItem(label="My Stream")
                list_item.setPath(local_url)
                list_item.setProperty('IsPlayable', 'true')
                #list_item.setMimeType('video/mp2t')
                list_item.setMimeType('video/mp4')
                list_item.setContentLookup(False)

                xbmc.Player().play(local_url, list_item)
                # Resolve the URL to play it
                #xbmcplugin.setResolvedUrl(handle=addon_utils.handle, succeeded=True, listitem=list_item)

                xbmc.log("It should be playing? " + local_url, xbmc.LOGERROR)

                #player = xbmc.Player()
                #player.play(local_url)
                # xbmcplugin.setResolvedUrl(
                #     addon_utils.handle, True, xbmcgui.ListItem(path=local_url)
                # )

                # xbmcplugin.setResolvedUrl(
                #     addon_utils.handle, True, xbmcgui.ListItem(path=ytdlp_extracted_url)
                # )

            if mode == "queue":
                mode_url = addon_utils.mode_url("watch")
                media_url = requests.utils.quote(url)
                u = f"{mode_url}&url={media_url}"
                stream_manager.queue_stream(title, u)
            if mode == "queuedir" or mode == "queuedir_recursive":
                inner_params = parse_qs(url)
                path = inner_params["url"][0] if "url" in inner_params else None
                if mode == "queuedir":
                    recursive=False
                else: 
                    recursive=True
                stream_manager.queue_directory(path, recursive)

        except Exception as e:
            addon_utils.show_error(e)
    else:
        addon_utils.view_menu(stream_manager.get_streams("/", 1, page_size))

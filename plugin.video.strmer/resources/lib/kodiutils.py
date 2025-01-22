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
import time
import subprocess
import os
import re
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
        self.profile_dir = xbmcvfs.translatePath(self.addon.getAddonInfo("Profile"))
        os.makedirs(self.profile_dir, exist_ok=True)
        self.cache_file = xbmcvfs.translatePath(os.path.join(self.profile_dir,
                                                             "requests_cache"))
        sort_methods = [
            xbmcplugin.SORT_METHOD_VIDEO_TITLE,
            xbmcplugin.SORT_METHOD_DATE,
        ]
        for method in sort_methods:
            xbmcplugin.addSortMethod(self.handle, method)        

    def mode_url(self, mode):
        return "plugin://{0}?mode={1}".format(self.id, mode)

    def view_menu(self, menu):
        items = []
        for item in menu:
            li = xbmcgui.ListItem(label=item.title, offscreen=True)
            li.setArt({"icon": item.icon, "thumb": item.icon, 'poster': item.icon, 'banner' : item.icon, 'landscape' : item.icon, 'clearlogo' : item.icon})
            li.setInfo("video", {"title": item.title})
            li.setDateTime(item.modified_time)
            if item.playable:
                li.setProperty("IsPlayable", "true")
                li.setInfo("video", {"plot": item.description})

                mode_url = self.mode_url("queue")
                media_url = requests.utils.quote(item.url)
                url = f"{mode_url}&url={media_url}"
                queue_url = f"RunPlugin("+"{0}&title={1}".format(url, item.title)+")"

                context_menu = [
                    ("Add to queue", queue_url),
                ]

                mode_url = self.mode_url("ytdlp")
                media_url = requests.utils.quote(item.url)
                url = f"{mode_url}&url={media_url}"
                ytdlp_url = f"RunPlugin("+"{0}&title={1}".format(url, item.title)+")"
                context_menu.append(('Play via yt-dlp', ytdlp_url))
                xbmc.log(ytdlp_url, xbmc.LOGERROR)
                    
                li.addContextMenuItems(context_menu)

            else:
                mode_url = self.mode_url("queuedir")
                media_url = requests.utils.quote(item.url)
                url = f"{mode_url}&url={media_url}"
                queue_url = f"RunPlugin("+"{0}&title={1}".format(url, item.title)+")"

                mode_url = self.mode_url("queuedir_recursive")
                url = f"{mode_url}&url={media_url}"
                queue_url_recursive = f"RunPlugin("+"{0}&title={1}".format(url, item.title)+")"
                context_menu = [
                    ("Add to queue", queue_url),
                    ("Add to queue (recursive)", queue_url_recursive),
                ]
                li.addContextMenuItems(context_menu)

            items.append((item.url, li, not item.playable))
        xbmcplugin.setContent(self.handle, 'videos')            
        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)

    def url_for(self, url):
        return "plugin://{0}{1}".format(self.id, url)

    def show_error(self, e):
        xbmcgui.Dialog().textviewer("{0} - {1}".format(
            self.name, "Error"), "Error: {0}".format(str(e)))


    def extract_youtube_video_id(self, plugin_url):
        match = re.search(r'plugin://plugin\.video\.youtube/play/\?video_id=([\w-]+)', plugin_url)
        if match:
            return match.group(1)
        return None

    def get_youtube_url(self, video_id):
        return f"https://www.youtube.com/watch?v={video_id}"


    def execute_ytdlp_get_url(self, youtube_url):
        try:
            # yt-dlp -F to select a non VP9 format
            # yt-dlp -f 136+140 -o - 'https://www.youtube.com/watch?v=eDr6_cMtfdA' | ffmpeg -i pipe: -c:v copy -c:a copy -f mpegts -listen 1 http://0.0.0.0:18080
            # mplayer http://localhost:18080
            # But ugly artifacts
            # vlc http://localhost:18080 works well though!

            # Call yt-dlp with the `-g` flag to get the direct URL
            result = subprocess.run(['yt-dlp', '-f', 'bestvideo', '-g', youtube_url], capture_output=True, text=True, check=True)
            # The output will be the direct URL
            direct_url = result.stdout.strip()
            return direct_url
        except subprocess.CalledProcessError as e:
            xbmc.log(f"yt-dlp failed with error code {e.returncode}.", xbmc.LOGERROR)
            return None
        except FileNotFoundError:
            xbmc.log("yt-dlp is not installed or not found in PATH.", xbmc.LOGERROR)
            return None

    def ytdlp_ffmpeg(self, youtube_url):
        try:
            # yt-dlp -F to select a non VP9 format
            # yt-dlp -f 136+140 -o - 'https://www.youtube.com/watch?v=eDr6_cMtfdA' | ffmpeg -i pipe: -c:v copy -c:a copy -f mpegts -listen 1 http://0.0.0.0:18080
            # vlc http://localhost:18080 to test

            stream_port = "18088"
            yt_dlp_command = [
                "yt-dlp", "-f", "136+140", "-o", "-", youtube_url
            ]
            ffmpeg_command = [
                "ffmpeg", "-i", "pipe:", "-c:v", "copy", "-c:a", "copy", "-f", "mpegts", 
                "-listen", "1", "http://0.0.0.0:" + stream_port
            ]

            yt_dlp_proc = subprocess.Popen(yt_dlp_command, stdout=subprocess.PIPE)
            ffmpeg_proc = subprocess.Popen(ffmpeg_command, stdin=yt_dlp_proc.stdout)
            time.sleep(5)
            return "http://127.0.0.1:" + stream_port
        except subprocess.CalledProcessError as e:
            xbmc.log(f"yt-dlp failed with error code {e.returncode}.", xbmc.LOGERROR)
            return None
        except FileNotFoundError:
            xbmc.log("yt-dlp is not installed or not found in PATH.", xbmc.LOGERROR)
            return None

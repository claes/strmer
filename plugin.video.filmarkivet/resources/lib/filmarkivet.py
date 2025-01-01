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

from bs4 import BeautifulSoup
import resources.lib.webget as webget
from resources.lib.kodiutils import AddonUtils
import requests
import re
import os
import xml.etree.ElementTree as ET

class Filmarkivet():
    MOVIES_PER_PAGE = 50

    MAIN_MENU = [{'mode': 'streams', 'title': 30011},
                 {'mode': 'categories', 'title': 30010},
                 {'mode': 'letters', 'title': 30011},
                 {'mode': 'themes', 'title': 30012},
                 {'mode': 'search', 'title': 30023}]


    class StreamInfo:
        def __init__(self, streamURL, title, sorttitle, plot, thumb, tag):
            self.streamURL = streamURL
            self.title = title
            self.sorttitle = sorttitle
            self.plot = plot
            self.thumb = thumb
            self.tag = tag

    class ListItem():
        def __init__(self, title, url, description, icon):
            self.title = title
            self.url = url
            self.description = description
            self.icon = icon
            self.playable = False
            self.year = None
            self.duration = None

    def __init__(self, addon_utils):
        self.addon_utils = addon_utils
        self.webget = webget.WebGet(self.addon_utils.cache_file)
        self.movies_regex = re.compile(".*Visar.*av (.*) filmer")
        self.meta_regex = re.compile("(\d+) / (\d+) min")

    def get_mainmenu(self):
        for item in self.MAIN_MENU:
            li = self.ListItem(
                self.addon_utils.localize(item["title"]),
                self.addon_utils.url_for("?mode={0}".format(item["mode"])),
                "",
                ""
            )
            yield li

    def mode_url(self, mode):
        return "plugin://{0}?mode={1}".format(self.addon_utils.id, mode)


    def __get_range(self, soup):
        try:
            soup = soup.find("span", {"id": "pageSpan"})
            m_range = soup.string.split("-")
            t = soup.parent.get_text().strip()
            match = self.movies_regex.match(t)
            return [int(m_range[0]), int(m_range[1])], int(match.group(1))
        except Exception:
            return None, None

    def get_url_movies(self, url, mode, page=1, limit=False):
        get_url = url
        if limit:
            get_url += "{0}limit={1}&pg={2}".format(
                "?" if url.rfind("?") < 0 else "&", self.MOVIES_PER_PAGE, page
            )
        html = self.webget.get_url(get_url)
        soup = BeautifulSoup(html, "html.parser")
        _range, range_max = self.__get_range(soup)
        soup = soup.find("div", {"id": "list"})
        movies = soup.find_all("a", {"class": "item"})
        mode_url = self.mode_url("watch")
        for movie in movies:
            meta = movie.h3.span.string.strip()
            title = "{0} ({1})".format(movie.h3.contents[0].strip(), meta)
            movie_url = "{0}&url={1}".format(
                mode_url,
                requests.utils.quote(movie["href"].replace("#038;", ""))
            )
            img = movie.figure.img["src"]
            try:
                desc = movie.p.string.strip()
            except Exception:
                desc = ""
            li = self.ListItem(title, movie_url, desc, img)
            li.playable = True
            try:
                match = self.meta_regex.match(meta)
                if match:
                    li.year = int(match.group(1))
                    li.duration = int(match.group(2)) * 60
            except Exception:
                pass
            yield li

        if _range is not None and _range[1] < range_max:
            next_url = "{0}&url={1}&page={2}".format(
                self.mode_url(mode),
                requests.utils.quote(url),
                page + 1
            )
            li = self.ListItem(
                self.addon_utils.localize(30001), next_url, None, None
            )
            yield li

    def parse_strm_and_nfo(self, file_path):
        if not file_path.endswith('.strm'):
            raise ValueError("Provided file must have a .strm extension")

        base_name = os.path.splitext(file_path)[0]

        # Read the content of the .strm file
        with open(file_path, 'r', encoding='utf-8') as strm_file:
            streamURL = strm_file.read().strip()

        # Determine the corresponding .nfo file
        nfo_file_path = f"{base_name}.nfo"

        if not os.path.exists(nfo_file_path):
            raise FileNotFoundError(f"The corresponding .nfo file was not found: {nfo_file_path}")

        # Parse the .nfo file
        tree = ET.parse(nfo_file_path)
        root = tree.getroot()

        # Extract values from the .nfo XML structure
        title = root.findtext('title', default='')
        sorttitle = root.findtext('sorttitle', default='')
        plot = root.findtext('plot', default='')
        thumb = root.findtext('thumb', default='')
        tag = root.findtext('tag', default='')

        # Return collected variables in a StreamInfo object
        return self.StreamInfo(streamURL, title, sorttitle, plot, thumb, tag)


    def list_directories(self, path):
        if not os.path.exists(path):
            raise ValueError("The specified path does not exist.")
        if not os.path.isdir(path):
            raise ValueError("The specified path is not a directory.")
        
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    def list_strm_files(self, directory):
        if not os.path.isdir(directory):
            raise ValueError("Provided path must be a directory")
        return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.strm')]

    def get_streams(self, path):
        list_items = []

        directories = self.list_directories(path) 
        for dir in directories:
            mode_url = self.mode_url("streams")
            try:
                list_item = self.ListItem(
                    title=dir,
                    url = "{0}&url={1}".format(mode_url, os.path.join(path, dir)),
                    description="", 
                    icon=""
                )
                list_item.playable = False
                list_items.append(list_item)
            except Exception as e:
                print(f"Error processing file {file}: {e}")

        strm_files = self.list_strm_files(path)
        for file in strm_files:
            mode_url = self.mode_url("watch")
            try:
                stream_info = self.parse_strm_and_nfo(file)
                list_item = self.ListItem(
                    title=stream_info.title,
                    url = "{0}&url={1}".format(mode_url, stream_info.streamURL),
                    description=stream_info.plot,
                    icon=stream_info.thumb
                )
                list_item.playable = True
                list_items.append(list_item)
            except Exception as e:
                print(f"Error processing file {file}: {e}")

        return list_items

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

    def __init__(self, addon_utils):
        self.addon_utils = addon_utils

    def mode_url(self, mode):
        return "plugin://{0}?mode={1}".format(self.addon_utils.id, mode)

    def parse_strm_and_nfo(self, file_path):
        if not file_path.endswith('.strm'):
            raise ValueError("Provided file must have a .strm extension")

        base_name = os.path.splitext(file_path)[0]

        with open(file_path, 'r', encoding='utf-8') as strm_file:
            streamURL = strm_file.read().strip()

        nfo_file_path = f"{base_name}.nfo"

        if not os.path.exists(nfo_file_path):
            raise FileNotFoundError(f"The corresponding .nfo file was not found: {nfo_file_path}")

        tree = ET.parse(nfo_file_path)
        root = tree.getroot()

        title = root.findtext('title', default='')
        sorttitle = root.findtext('sorttitle', default='')
        plot = root.findtext('plot', default='')
        thumb = root.findtext('thumb', default='')
        tag = root.findtext('tag', default='')

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

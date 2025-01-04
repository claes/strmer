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

from pathlib import Path
import os
from datetime import datetime
import xml.etree.ElementTree as ET
import xbmc

class StreamManager():

    class StreamInfo:
        def __init__(self, streamURL, title, sorttitle, plot, thumb, tag, modified):
            self.streamURL = streamURL
            self.title = title
            self.sorttitle = sorttitle
            self.plot = plot
            self.thumb = thumb
            self.tag = tag
            self.modified = modified

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
            modified_time = datetime.fromtimestamp(os.fstat(strm_file.fileno()).st_mtime)

        nfo_file_path = f"{base_name}.nfo"

        if not os.path.exists(nfo_file_path):
            raise FileNotFoundError(f"The corresponding .nfo file was not found: {nfo_file_path}")

        with open(nfo_file_path, 'r', encoding='utf-8') as nfo_file:
            nfo_content = nfo_file.read()
  
        try:
            tree = ET.ElementTree(ET.fromstring(nfo_content))
        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML in {nfo_file_path}: {e}")
  
        root = tree.getroot()

        title = root.findtext('title', default='')
        sorttitle = root.findtext('sorttitle', default='')
        plot = root.findtext('plot', default='')
        thumb = root.findtext('thumb', default='')
        tag = root.findtext('tag', default='')

        return self.StreamInfo(streamURL, title, sorttitle, plot, thumb, tag, modified_time)


    def list_directories(self, path):
        if not os.path.exists(path):
            raise ValueError("The specified path does not exist.")
        if not os.path.isdir(path):
            raise ValueError("The specified path is not a directory.")
        
        directories = [
            entry for entry in Path(path).iterdir()
            if entry.is_dir()
        ]
        
        directories.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        return [d.name for d in directories]


    def list_strm_files(self, directory):
        if not os.path.isdir(directory):
            raise ValueError("Provided path must be a directory")

        strm_files = [str(file) for file in Path(directory).iterdir() if file.suffix == '.strm']
        strm_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)        
        return strm_files

    def get_streams(self, path, page, page_size, include_dirs=True):
        if page < 1:
            raise ValueError("Page number must be greater than or equal to 1.")
        if page_size < 1:
            raise ValueError("Page size must be greater than or equal to 1.")
        
        list_items = []

        if include_dirs:
            directories = self.list_directories(path)
            for dir in directories:
                mode_url = self.mode_url("streams")
                try:
                    list_item = self.ListItem(
                        title=dir,
                        url="{0}&url={1}".format(mode_url, os.path.join(path, dir)),
                        description="",
                        icon=""
                    )
                    list_item.playable = False
                    list_items.append(list_item)
                except Exception as e:
                    print(f"Error processing directory {dir}: {e}")

        strm_files = self.list_strm_files(path)
        for file in strm_files:
            mode_url = self.mode_url("watch")
            try:
                stream_info = self.parse_strm_and_nfo(file)
                list_item = self.ListItem(
                    title=stream_info.title,
                    url="{0}&url={1}".format(mode_url, stream_info.streamURL),
                    description=stream_info.plot,
                    icon=stream_info.thumb
                )
                list_item.playable = True
                list_items.append(list_item)
            except Exception as e:
                print(f"Error processing file {file}: {e}")

        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        sub_list = list_items[start_index:end_index] 
        if end_index < len(list_items):
            next_url = "{0}&url={1}&page={2}".format(self.mode_url("streams"), path, page + 1)
            sub_list.append(self.ListItem("Next", next_url, None, None))
        return sub_list

# -*- coding: utf-8 -*-

import urllib
import re
import xbmc
import json

from cdam import Def
from utils import get_html_source, log

url_search = "http://www.theaudiodb.com/api/v1/json/{0}/search.php".format(Def.TADB_API_KEY)
url_search_artist = url_search + "?s={0}"
url_search_album = url_search + "?s={0}&a={1}"


def search_artist(artist_name):
    log("TADB search for artist: {0}".format(artist_name), xbmc.LOGNOTICE)
    url = url_search_artist.format(urllib.quote_plus(artist_name))
    log(url, xbmc.LOGNOTICE)
    filename = "TADB_S-{0}".format(re.sub('[^0-9a-zA-Z]+', '_', str(artist_name)))
    return get_html_source(url, filename, save_file=True, overwrite=False)


def search_artist_mbid(artist_name):
    source = json.loads(search_artist(artist_name))
    if source and "artists" in source:
        return source["artists"][0]["strMusicBrainzID"]
    else:
        return ""


def search_album(artist_name, album_name):
    log("TADB search for album: {0} / {1}".format(artist_name, album_name), xbmc.LOGNOTICE)
    url = url_search_album.format(urllib.quote_plus(artist_name), urllib.quote_plus(album_name))
    filename = "TADB_S-{0}_A-{1}".format(
        re.sub('[^0-9a-zA-Z]+', '_', str(artist_name)),
        re.sub('[^0-9a-zA-Z]+', '_', str(album_name)))
    return get_html_source(url, filename, save_file=True, overwrite=False)

#    url = url_search_artist.format(Def.TADB_API_KEY, urllib.quote_plus(name))
#    log(url, xbmc.LOGNOTICE)
#    filename = "TADB_SA_{0}".format(re.sub('[^0-9a-zA-Z]+', '_', str(name)))
#    htmlsource = get_html_source(url, filename, save_file=True, overwrite=False)

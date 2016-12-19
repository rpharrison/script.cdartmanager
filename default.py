# -*- coding: utf-8 -*-

import calendar
import datetime
import os
import sys
import time
import traceback
from sqlite3 import dbapi2 as sqlite3

import xbmc
import xbmcgui
from xbmcvfs import copy as file_copy
from xbmcvfs import delete as delete_file
from xbmcvfs import exists as exists
from xbmcvfs import rename as file_rename

import lib.cdam

true = True
false = False
null = None

__cdam__ = lib.cdam.CDAM()
__settings__ = lib.cdam.Settings()

__addon__ = __cdam__.getAddon()
__addon_path__ = __cdam__.path()

__language__ = __cdam__.getLocalizedString

enable_all_artists = __settings__.enable_all_artists()
music_path = __settings__.path_music_path()


addon_work_folder = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode('utf-8')
download_temp_folder = os.path.join(addon_work_folder, "temp").decode("utf8")
tempxml_folder = os.path.join(addon_work_folder, "tempxml")
tempgfx_folder = os.path.join(addon_work_folder, "tempgfx")
addon_db = os.path.join(addon_work_folder, "l_cdart.db").replace("\\\\", "\\")
addon_db_update = os.path.join(addon_work_folder, "l_cdart." + lib.cdam.Constants.db_version_old() + ".db").replace("\\\\", "\\")
addon_db_backup = os.path.join(addon_work_folder, "l_cdart.db.bak").replace("\\\\", "\\")
addon_db_crash = os.path.join(addon_work_folder, "l_cdart.db-journal").replace("\\\\", "\\")
settings_file = os.path.join(addon_work_folder, "settings.xml").replace("\\\\", "\\")


script_fail = False
first_run = False
rebuild = False
soft_exit = False
background_db = False
script_mode = ""

from lib.utils import settings_to_log, get_unicode, change_characters, log, dialog_msg
from lib.database import store_counts, new_local_count, get_local_artists_db, get_local_albums_db, update_database, \
    retrieve_album_details_full, mbid_repair, refresh_db
from lib.jsonrpc_calls import retrieve_album_details, retrieve_artist_details, get_fanart_path, get_thumbnail_path
from lib.musicbrainz_utils import get_musicbrainz_artist_id
from lib.fanarttv_scraper import first_check, remote_banner_list, remote_hdlogo_list, \
    remote_cdart_list, remote_coverart_list, remote_fanart_list, remote_clearlogo_list, \
    remote_artistthumb_list
from lib.download import auto_download
import lib.gui

try:
    from xbmcvfs import mkdirs as _makedirs
except:
    from lib.utils import _makedirs


def clear_skin_properties():
    xbmcgui.Window(10000).setProperty("cdart_manager_running", "False")
    xbmcgui.Window(10000).setProperty("cdart_manager_update", "False")
    xbmcgui.Window(10000).setProperty("cdart_manager_allartist", "False")


def artist_musicbrainz_id(artist_id, artist_mbid):
    artist_details = retrieve_artist_details(artist_id)
    artist = []
    if not artist_details["musicbrainzartistid"] or not artist_mbid:
        name, artist["musicbrainz_artistid"], sortname = get_musicbrainz_artist_id(get_unicode(artist_details["label"]))
        artist["name"] = get_unicode(artist_details["label"])
    else:
        artist["name"] = get_unicode(artist_details["label"])
        if artist_mbid:
            artist["musicbrainz_artistid"] = artist_mbid
        else:
            artist["musicbrainz_artistid"] = artist_details["musicbrainzartistid"]
    return artist


def album_musicbrainz_id(album_id):
    album_list = retrieve_album_details(album_id)
    if album_list:
        album_detail_list = retrieve_album_details_full(album_list, 1, background=True)
        return album_detail_list
    else:
        return []


def select_artwork(details, media_type):
    artwork = None
    selection = None
    if media_type in ("cdart", "cover"):
        if media_type == "cdart":
            artwork = remote_cdart_list(details)
        else:
            artwork = remote_coverart_list(details)
        if artwork:
            for art in artwork:
                if art["musicbrainz_albumid"] == details["musicbrainz_albumid"]:
                    selection = art
            if not selection:
                dialog_msg("okdialog", heading=__language__(32033), line1=__language__(32030),
                           line2=__language__(32031), background=False)
        else:
            dialog_msg("okdialog", heading=__language__(32033), line1=__language__(32030), line2=__language__(32031),
                       background=False)
    else:
        if media_type == "fanart":
            artwork = remote_fanart_list(details)
        elif media_type == "clearlogo":
            artwork = remote_clearlogo_list(details)
        elif media_type == "hdlogo":
            artwork = remote_hdlogo_list(details)
        elif media_type == "artistthumb":
            artwork = remote_artistthumb_list(details)
        elif media_type == "musicbanner":
            artwork = remote_banner_list(details)
        if artwork:
            for art in artwork:
                print art


def thumbnail_copy(art_path, thumb_path, type="artwork"):
    if not thumb_path.startswith("http://") or not thumb_path.startswith("image://"):
        if exists(art_path):
            if file_copy(art_path, thumb_path):
                log("Successfully copied %s" % type, xbmc.LOGDEBUG)
            else:
                log("Failed to copy to %s" % type, xbmc.LOGDEBUG)
            log("Source Path: %s" % repr(art_path), xbmc.LOGDEBUG)
            log("Destination Path: %s" % repr(thumb_path), xbmc.LOGDEBUG)
    elif thumb_path.startswith("http://") or thumb_path.startswith("image://"):
        log("Destination Path is not able to be copied to: %s" % repr(thumb_path), xbmc.LOGDEBUG)


def update_xbmc_thumbnails(background=False):
    log("Updating Thumbnails/fanart Images", xbmc.LOGNOTICE)
    fanart = "fanart.jpg"
    artistthumb_temp = "artist.jpg"
    artistthumb = "folder.jpg"
    albumthumb = "folder.jpg"
    # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ( __language__(32042), __language__(32112), 2000, image) )
    xbmc.sleep(1000)
    dialog_msg("create", heading=__language__(32042), background=background)
    # Artists
    artists = get_local_artists_db(mode="local_artists")
    if not artists:
        artists = get_local_artists_db(mode="album_artists")
    # Albums
    albums = get_local_albums_db("all artists", False)
    percent = 1
    count = 0
    for artist in artists:
        percent = percent = int((count / float(len(artists))) * 100)
        count += 1
        if percent == 0:
            percent = 1
        if percent > 100:
            percent = 100
        if dialog_msg("iscanceled"):
            break
        dialog_msg("update", percent=percent, line1=__language__(32112),
                   line2=" %s %s" % (__language__(32038), get_unicode(artist["name"])), background=background)
        xbmc_thumbnail_path = ""
        xbmc_fanart_path = ""
        fanart_path = os.path.join(music_path, change_characters(artist["name"]), fanart).replace("\\\\", "\\")
        artistthumb_path = os.path.join(music_path, change_characters(artist["name"]), artistthumb).replace("\\\\",
                                                                                                            "\\")
        artistthumb_rename = os.path.join(music_path, change_characters(artist["name"]), artistthumb_temp).replace(
            "\\\\", "\\")
        if exists(artistthumb_rename):
            file_rename(artistthumb_rename, artistthumb_path)
        if exists(fanart_path):
            xbmc_fanart_path = get_fanart_path(artist["local_id"], "artist")
        elif exists(artistthumb_path):
            xbmc_thumbnail_path = get_thumbnail_path(artist["local_id"], "artist")
        else:
            continue
        if xbmc_fanart_path:  # copy to XBMC supplied fanart path
            thumbnail_copy(fanart_path, xbmc_fanart_path, "fanart")
        if xbmc_thumbnail_path:  # copy to XBMC supplied artist image path
            thumbnail_copy(artistthumb_path, xbmc_thumbnail_path, "artist thumb")
    percent = 1
    count = 1
    for album in albums:
        percent = percent = int((count / float(len(albums))) * 100)
        if percent < 1:
            percent = 1
        if percent > 100:
            percent = 100
        if dialog_msg("iscanceled"):
            break
        dialog_msg("update", percent=percent, line1=__language__(32042), line2=__language__(32112),
                   line3=" %s %s" % (__language__(32039), get_unicode(album["title"])), background=background)
        xbmc_thumbnail_path = ""
        coverart_path = os.path.join(album["path"], albumthumb).replace("\\\\", "\\")
        if exists(coverart_path):
            xbmc_thumbnail_path = get_thumbnail_path(album["local_id"], "album")
        if xbmc_thumbnail_path:
            thumbnail_copy(coverart_path, xbmc_thumbnail_path, "album cover")
        count += 1
    log("Finished Updating Thumbnails/fanart Images", xbmc.LOGNOTICE)
    # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ( __language__(32042), __language__(32113), 2000, image) )


def write_cache_file():
    cache_file = open(os.path.join(addon_work_folder, "cache.txt"), "wb")
    line = "%s/%s/%s\n" % (time.strftime("%m"), time.strftime("%d"), time.strftime("%Y"))
    cache_file.write(line)
    cache_file.close()


def update_cache():
    line = ""
    try:
        if exists(os.path.join(addon_work_folder, "cache.txt")):
            cache_file = open(os.path.join(addon_work_folder, "cache.txt"), "rb")
            line = str(cache_file.readline()).replace("\n", "")
            cache_file.close()
            cache_date = datetime.datetime.strptime(line, "%m/%d/%Y").date()
            check_date = datetime.date.today() - datetime.timedelta(days=3)
            if not cache_date < check_date:
                log("Cache not being cleared", xbmc.LOGNOTICE)
                return False
            else:
                log("Cache is being cleared", xbmc.LOGNOTICE)
                write_cache_file()
                return True
        else:
            log("No Cache File existing.", xbmc.LOGNOTICE)
            write_cache_file()
            return True
    except:
        traceback.print_exc()
        return False


def get_script_mode():
    script_mode = ""
    start_mbid = ""
    start_dbid = 0
    start_media_type = ()
    if len(sys.argv) < 2:
        script_mode = "normal"
    try:
        log("sys.argv[0]: %s" % sys.argv[0])
        log("sys.argv[1]: %s" % sys.argv[1])
        log("sys.argv[2]: %s" % sys.argv[2])
        log("sys.argv[3]: %s" % sys.argv[3])
    except:
        pass
    for arg in sys.argv:
        if arg in (
                "autocdart", "autocover", "autofanart", "autologo", "autothumb", "autobanner", "autoall", "database",
                "update",
                "oneshot", "artist"):
            script_mode = arg
        if len(arg) == 36 and arg[8] == "-":  # MBID
            start_mbid = arg
        try:
            start_dbid = int(arg)
        except:
            pass
        if arg.startswith("mediatype="):
            start_media_type = arg.replace("mediatype=", "").split("/")
    return script_mode, start_mbid, start_dbid, start_media_type


if (__name__ == "__main__"):
    # xbmc.executebuiltin('Dialog.Close(all, true)')
    log("#############################################################", xbmc.LOGNOTICE)
    for credit in __cdam__.credits():
        log("#  %-55s  #" % credit, xbmc.LOGNOTICE)
    log("#############################################################", xbmc.LOGNOTICE)
    log("Looking for settings.xml", xbmc.LOGNOTICE)
    if not exists(settings_file):  # Open Settings if settings.xml does not exists
        log("settings.xml File not found, creating path and opening settings", xbmc.LOGNOTICE)
        _makedirs(addon_work_folder)
        __addon__.openSettings()
        soft_exit = True

    settings_to_log(addon_work_folder, "[script.cdartmanager]")
    try:
        recognized_ = __settings__.color_recognized()
        soft_exit = False
    except:
        dialog_msg("okdialog", heading=__language__(32181), line1=__language__(32182))
        __addon__.openSettings()
        soft_exit = True
    script_mode, provided_mbid, provided_dbid, media_type = get_script_mode()
    if xbmcgui.Window(10000).getProperty("cdart_manager_running") == "True":
        log("cdART Manager Already running, exiting...", xbmc.LOGNOTICE)
        soft_exit = True
    else:
        xbmcgui.Window(10000).setProperty("cdart_manager_running", "True")
    if not soft_exit:
        try:
            if enable_all_artists:
                xbmcgui.Window(10000).setProperty("cdart_manager_allartist", "True")
            else:
                xbmcgui.Window(10000).setProperty("cdart_manager_allartist", "False")
            # xbmc.executebuiltin('Dialog.Close(all, true)')
            if script_mode in ("database"):
                log("Start method - Build Database in background", xbmc.LOGNOTICE)
                xbmcgui.Window(10000).setProperty("cdartmanager_update", "True")
                local_album_count, local_artist_count, local_cdart_count = refresh_db(background=True)
                local_artists = get_local_artists_db(mode="album_artists", background=True)
                if enable_all_artists:
                    all_artists = get_local_artists_db(mode="all_artists", background=True)
                else:
                    all_artists = []
                first_check(all_artists, local_artists, background=True)
                xbmcgui.Window(10000).setProperty("cdartmanager_update", "False")
            elif script_mode in (
            "autocdart", "autocover", "autofanart", "autologo", "autothumb", "autobanner", "autoall", "update"):
                local_artists = get_local_artists_db(mode="album_artists", background=True)
                if enable_all_artists:
                    all_artists = get_local_artists_db(mode="all_artists", background=True)
                else:
                    all_artists = []
                all_artists_list = all_artists
                album_artists = local_artists
            if script_mode in ("autocdart", "autocover", "autofanart", "autologo", "autothumb", "autobanner"):
                xbmcgui.Window(10000).setProperty("cdart_manager_running", "True")
                if script_mode == "autocdart":
                    log("Start method - Autodownload Album cdARTs in background", xbmc.LOGNOTICE)
                    artwork_type = "cdart"
                elif script_mode == "autocover":
                    log("Start method - Autodownload Album Cover art in background", xbmc.LOGNOTICE)
                    artwork_type = "cover"
                elif script_mode == "autofanart":
                    log("Start method - Autodownload Artist Fanarts in background", xbmc.LOGNOTICE)
                    artwork_type = "fanart"
                elif script_mode == "autologo":
                    log("Start method - Autodownload Artist Logos in background", xbmc.LOGNOTICE)
                    artwork_type = "clearlogo"
                elif script_mode == "autothumb":
                    log("Start method - Autodownload Artist Thumbnails in background", xbmc.LOGNOTICE)
                    artwork_type = "artistthumb"
                elif script_mode == "autobanner":
                    log("Start method - Autodownload Artist Music Banners in background", xbmc.LOGNOTICE)
                    artwork_type = "musicbanner"
                if artwork_type in ("fanart", "clearlogo", "artistthumb", "musicbanner") and enable_all_artists:
                    download_count, successfully_downloaded = auto_download(artwork_type, all_artists_list,
                                                                            background=True)
                else:
                    download_count, successfully_downloaded = auto_download(artwork_type, album_artists,
                                                                            background=True)
                log("Autodownload of %s artwork completed\nTotal artwork downloaded: %d" % (
                    artwork_type, download_count), xbmc.LOGNOTICE)
            elif script_mode == "update":
                log("Start method - Update Database in background", xbmc.LOGNOTICE)
                xbmcgui.Window(10000).setProperty("cdart_manager_update", "True")
                clear_cache = update_cache()
                update_database(background=True)
                local_artists = get_local_artists_db(mode="album_artists", background=True)
                if enable_all_artists:
                    all_artists = get_local_artists_db(mode="all_artists", background=True)
                else:
                    all_artists = []
                d = datetime.datetime.utcnow()
                present_datecode = calendar.timegm(d.utctimetuple())
                first_check(all_artists, local_artists, background=True, update_db=clear_cache)
            elif script_mode == "autoall":
                xbmcgui.Window(10000).setProperty("cdart_manager_running", "True")
                log("Start method - Autodownload all artwork in background", xbmc.LOGNOTICE)
                total_artwork = 0
                for artwork_type in ("cdart", "cover", "fanart", "clearlogo", "artistthumb", "musicbanner"):
                    log("Start method - Autodownload %s in background" % artwork_type, xbmc.LOGNOTICE)
                    if artwork_type in ("fanart", "clearlogo", "artistthumb", "musicbanner") and enable_all_artists:
                        download_count, successfully_downloaded = auto_download(artwork_type, all_artists_list,
                                                                                background=True)
                    elif artwork_type:
                        download_count, successfully_downloaded = auto_download(artwork_type, album_artists,
                                                                                background=True)
                    total_artwork += download_count
                log("Autodownload all artwork completed\nTotal artwork downloaded: %d" % total_artwork, xbmc.LOGNOTICE)
            elif script_mode == "update_thumbs":
                log("Start method - Update Thumbnails in background", xbmc.LOGNOTICE)
                update_xbmc_thumbnails()
            elif script_mode == "oneshot":
                log("Start method - One Shot Download method", xbmc.LOGNOTICE)
                if provided_dbid or provided_mbid:
                    if media_type[0] in ("clearlogo", "fanart", "artistthumb", "musicbanner"):
                        artist = artist_musicbrainz_id(provided_dbid, provided_mbid)
                        if not artist:
                            log("No MBID found", xbmc.LOGNOTICE)
                        else:
                            print artist
                            log("Artist: %s" % artist["artist"], xbmc.LOGDEBUG)
                            log("MBID: %s" % artist["musicbrainz_artistid"], xbmc.LOGDEBUG)
                            select_artwork(artist, media_type[0])
                    elif media_type[0] in ("cdart", "cover"):
                        if provided_dbid:
                            album_details = album_musicbrainz_id(provided_dbid)
                            if not album_details:
                                log("No MBID found", xbmc.LOGNOTICE)
                            else:
                                for album in album_details:
                                    log("Album: %s" % album["title"])
                                    log("MBID: %s" % album["musicbrainz_albumid"])
                                    log("Artist: %s" % album["artist"])
                                    log("MBID: %s" % album["musicbrainz_artistid"])
                                    select_artwork(album, media_type[0])
                        else:
                            log("No Database ID provided")
                else:
                    log("A Database ID or MusicBrainz ID needed")
            elif script_mode == "normal":
                log("Addon Work Folder: %s" % addon_work_folder, xbmc.LOGNOTICE)
                log("Addon Database: %s" % addon_db, xbmc.LOGNOTICE)
                log("Addon settings: %s" % settings_file, xbmc.LOGNOTICE)
                query = "SELECT version FROM counts"
                if xbmcgui.Window(10000).getProperty(
                        "cdart_manager_update") == "True":  # Check to see if skin property is set, if it is, gracefully exit the script
                    if not os.environ.get("OS", "win32") in ("win32", "Windows_NT"):
                        background_db = False
                        # message "cdART Manager, Stopping Background Database Building"
                        dialog_msg("okdialog", heading=__language__(32042), line1=__language__(32119))
                        log("Background Database Was in Progress, Stopping, allowing script to continue",
                            xbmc.LOGNOTICE)
                        xbmcgui.Window(10000).setProperty("cdartmanager_update", "False")
                    else:
                        background_db = True
                        # message "cdART Manager, Background Database building in progress...  Exiting Script..."
                        dialog_msg("okdialog", heading=__language__(32042), line1=__language__(32118))
                        log("Background Database Building in Progress, exiting", xbmc.LOGNOTICE)
                        xbmcgui.Window(10000).setProperty("cdartmanager_update", "False")
                if not background_db and not soft_exit:  # If Settings exists and not in background_db mode, continue on
                    log("Addon Work Folder Found, Checking For Database", xbmc.LOGNOTICE)
                if not exists(addon_db) and not background_db:  # if l_cdart.db missing, must be first run
                    log("Addon Db not found, Must Be First Run", xbmc.LOGNOTICE)
                    first_run = True
                elif not background_db and not soft_exit:
                    log("Addon Db Found, Checking Database Version", xbmc.LOGNOTICE)
                if exists(
                        addon_db_crash) and not first_run and not background_db and not soft_exit:  # if l_cdart.db.journal exists, creating database must have crashed at some point, delete and start over
                    log("Detected Database Crash, Trying to delete", xbmc.LOGNOTICE)
                    try:
                        delete_file(addon_db)
                        delete_file(addon_db_crash)
                    except StandardError, e:
                        log("Error Occurred: %s " % e.__class__.__name__, xbmc.LOGNOTICE)
                        traceback.print_exc()
                        script_fail = True
                elif not first_run and not background_db and not soft_exit and not script_fail:  # Test database version
                    log("Looking for database version: %s" % lib.cdam.Constants.db_version(), xbmc.LOGNOTICE)
                    try:
                        conn_l = sqlite3.connect(addon_db)
                        c = conn_l.cursor()
                        c.execute(query)
                        version = c.fetchall()
                        c.close()
                        if version[0][0] == lib.cdam.Constants.db_version():
                            log("Database matched", xbmc.LOGNOTICE)
                        elif version[0][0] == lib.cdam.Constants.db_version_old():
                            log("Old version found, Removing Bach MBID's from database", xbmc.LOGNOTICE)
                            mbid_repair()
                        elif version[0][0] == lib.cdam.Constants.db_version_ancient():
                            log("Ancient version found, Adding new column to Local Album Artist and Local Artists",
                                xbmc.LOGNOTICE)
                            all_artists = []
                            local_artists = []
                            file_copy(addon_db, addon_db_update)
                            conn = sqlite3.connect(addon_db)
                            c = conn.cursor()
                            try:
                                c.execute('ALTER TABLE lalist ADD COLUMN fanarttv_has_art;')
                            except:
                                traceback.print_exc()
                            try:
                                c.execute('ALTER TABLE local_artists ADD COLUMN fanarttv_has_art;')
                            except:
                                traceback.print_exc()
                            c.close()
                            local_artist_count, album_count, artist_count, cdart_existing = new_local_count()
                            store_counts(local_artist_count, artist_count, album_count, cdart_existing)
                            local_artists = get_local_artists_db(mode="album_artists")
                            if enable_all_artists:
                                all_artists = get_local_artists_db(mode="all_artists")
                            first_check(all_artists, local_artists, background=False, update_db=True)
                        else:
                            log("Database Not Matched - trying to delete", xbmc.LOGNOTICE)
                            rebuild = dialog_msg("yesno", heading=__language__(32108), line1=__language__(32109))
                            soft_exit = True
                    except StandardError, e:
                        traceback.print_exc()
                        log("# Error: %s" % e.__class__.__name__, xbmc.LOGNOTICE)
                        try:
                            log("Trying To Delete Database", xbmc.LOGNOTICE)
                            delete_file(addon_db)
                        except StandardError, e:
                            traceback.print_exc()
                            log("# unable to remove folder", xbmc.LOGNOTICE)
                            log("# Error: %s" % e.__class__.__name__, xbmc.LOGNOTICE)
                            script_fail = True
                path = __addon__.getAddonInfo('path')
                if not script_fail and not background_db:
                    if rebuild:
                        local_album_count, local_artist_count, local_cdart_count = refresh_db(True)
                    elif not rebuild and not soft_exit:
                        try:
                            ui = lib.gui.GUI("script-cdartmanager.xml", __addon__.getAddonInfo('path'), "Default")
                            xbmc.sleep(2000)
                            ui.doModal()
                            del ui
                            clear_skin_properties()
                        except:
                            log("Error in script occured", xbmc.LOGNOTICE)
                            traceback.print_exc()
                            dialog_msg("close")
                            clear_skin_properties()
                elif not background_db and not soft_exit:
                    log("Problem accessing folder, exiting script", xbmc.LOGNOTICE)
                    xbmc.executebuiltin(
                        "Notification( %s, %s, %d, %s)" % (__language__(32042), __language__(32110), 500, __cdam__.file_icon()))
            clear_skin_properties()
        except:
            print "Unexpected error:", sys.exc_info()[0]
            clear_skin_properties()
            raise
    else:
        clear_skin_properties()

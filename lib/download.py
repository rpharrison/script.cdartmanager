# -*- coding: utf-8 -*-

import os
import urllib
from traceback import print_exc

import xbmc
import xbmcvfs

from sqlite3 import dbapi2 as sqlite3
import cdam

from fanarttv_scraper import remote_banner_list, remote_hdlogo_list, remote_cdart_list, \
    remote_coverart_list, remote_fanart_list, remote_clearlogo_list, remote_artistthumb_list
from db import get_local_albums_db, artwork_search
from utils import get_unicode, change_characters, log, dialog_msg, smart_unicode
# from jsonrpc_calls import get_thumbnail_path, get_fanart_path

__cdam__ = cdam.CDAM()
__settings__ = cdam.Settings()
__lang__ = __cdam__.getLocalizedString
addon_db = __cdam__.file_addon_db()
resizeondownload = False  # disabled because fanart.tv API V3 doesn't deliver correct sizes
music_path = __settings__.path_music_path()
fanart_limit = __settings__.fanart_limit()
enable_fanart_limit = __settings__.enable_fanart_limit()
tempgfx_folder = __cdam__.path_temp_gfx()


def check_size(path, type, size_w, size_h):
    # size check is disabled because currently fanart.tv always returns size=1000
    # ref: https://forum.fanart.tv/viewtopic.php?f=4&t=403
    file_name = get_filename(type, path, "auto")
    source = os.path.join(path, file_name)
    if xbmcvfs.exists(source):
        log("size check n.a. in new fanart.tv API, returning False for %s" % source)
        return False
    else:
        log("size check n.a. in new fanart.tv API, returning True for %s" % source)
        return True


# # first copy from source to work directory since Python does not support SMB://
#    file_name = get_filename(type, path, "auto")
#    destination = os.path.join(addon_work_folder, "temp", file_name)
#    source = os.path.join(path, file_name)
#    log("Checking Size", xbmc.LOGDEBUG)
#    if exists(source):
#        file_copy(source, destination)
#    else:
#        return True
#    try:
#        # Helix: PIL is not available in Helix 14.1 on Android
#        if (pil_is_available):
#            # Helix: not really a Helix problem but file cannot be removed after Image.open locking it
#            with open(str(destination), 'rb') as destf:
#                artwork = Image.open(destf)
#            log("Image Size: %s px(W) X %s px(H)" % (artwork.size[0], artwork.size[1]), xbmc.LOGDEBUG)
#            if artwork.size[0] < size_w and artwork.size[
#                1] < size_h:  # if image is smaller than 1000 x 1000 and the image on fanart.tv = 1000
#                delete_file(destination)
#                log("Image is smaller", xbmc.LOGDEBUG)
#                return True
#            else:
#                delete_file(destination)
#                log("Image is same size or larger", xbmc.LOGDEBUG)
#                return False
#        else:
#            log("PIL not available, skipping size check", xbmc.LOGDEBUG)
#            return False
#    except:
#        log("artwork does not exist. Source: %s" % source, xbmc.LOGDEBUG)
#        return True


def get_filename(type_, url, mode):
    if type_ == "cdart":
        file_name = "cdart.png"
    elif type_ == "cover":
        file_name = "folder.jpg"
    elif type_ == "fanart":
        if mode == "auto":
            file_name = os.path.basename(url)
        else:
            file_name = "fanart.jpg"
    elif type_ == "clearlogo":
        file_name = "logo.png"
    elif type_ == "artistthumb":
        file_name = "folder.jpg"
    elif type_ == "musicbanner":
        file_name = "banner.jpg"
    else:
        file_name = "unknown"
    return file_name


def make_music_path(artist):
    # Helix: paths MUST end with trailing slash
    path = os.path.join(music_path, artist).replace("\\\\", "\\")
    path2 = os.path.join(music_path, str.lower(artist)).replace("\\\\", "\\")
    if not xbmcvfs.exists(path2):
        if not xbmcvfs.exists(path):
            if xbmcvfs.mkdirs(path):
                log("Path to music artist made", xbmc.LOGDEBUG)
                return True
            else:
                log("unable to make path to music artist", xbmc.LOGDEBUG)
                return False
    else:
        if not xbmcvfs.exists(path):
            if xbmcvfs.mkdirs(path):
                log("Path to music artist made", xbmc.LOGDEBUG)
                return True
            else:
                log("unable to make path to music artist", xbmc.LOGDEBUG)
                return False


def download_art(url_cdart, album, database_id, type_, mode, size, background=False):
    log("Downloading artwork... ", xbmc.LOGDEBUG)
    download_success = False
#    percent = 1
    is_canceled = False
    if mode == "auto":
        dialog_msg("update", percent=1, background=background)
    else:
        dialog_msg("create", heading=__lang__(32047), background=background)
        # Onscreen Dialog - "Downloading...."
    file_name = get_filename(type_, url_cdart, mode)
    # Helix: paths MUST end with trailing slash
    path = os.path.join(album["path"].replace("\\\\", "\\"), '')
    if file_name == "unknown":
        log("Unknown Type ", xbmc.LOGDEBUG)
        message = [__lang__(32026), __lang__(32025), "File: %s" % get_unicode(path),
                   "Url: %s" % get_unicode(url_cdart)]
        return message, download_success
#    if type_ in ("artistthumb", "cover"):
#        thumbnail_path = get_thumbnail_path(database_id, type_)
#    else:
#        thumbnail_path = ""
#    if type_ == "fanart" and mode in ("manual", "single"):
#        thumbnail_path = get_fanart_path(database_id, type_)
    if not xbmcvfs.exists(path):
        try:
            xbmcvfs.mkdirs(album["path"].replace("\\\\", "\\"))
        except Exception as e:
            log(e.message, xbmc.LOGDEBUG)
    log("Path: %s" % path, xbmc.LOGDEBUG)
    log("Filename: %s" % file_name, xbmc.LOGDEBUG)
    log("url: %s" % url_cdart, xbmc.LOGDEBUG)

    # cosmetic: use subfolder for downloading instead of work folder
    if not xbmcvfs.exists(os.path.join(tempgfx_folder, '').replace("\\\\", "\\")):
        xbmcvfs.mkdirs(os.path.join(tempgfx_folder, '').replace("\\\\", "\\"))
    destination = os.path.join(tempgfx_folder, file_name).replace("\\\\", "\\")  # download to work folder first
    final_destination = os.path.join(path, file_name).replace("\\\\", "\\")
    try:
        # this give the ability to use the progress bar by retrieving the downloading information
        # and calculating the percentage
        def _report_hook(count, blocksize, totalsize):
            try:
                percent = int(float(count * blocksize * 100) / totalsize) if totalsize > 0 else 100
                if percent < 1:
                    percent = 1
                if percent > 100:
                    percent = 100
            except Exception as ex:
                log(ex.message, xbmc.LOGDEBUG)
                percent = 1
            if type_ in ("fanart", "clearlogo", "artistthumb", "musicbanner"):
                dialog_msg("update", percent=percent,
                           line1="%s%s" % (__lang__(32038), get_unicode(album["artist"])), background=background)
            else:
                dialog_msg("update", percent=percent,
                           line1="%s%s" % (__lang__(32038), get_unicode(album["artist"])),
                           line2="%s%s" % (__lang__(32039), get_unicode(album["title"])), background=background)
#            if mode == "auto":
#                if dialog_msg("iscanceled", background=background):
#                    is_canceled = True

        if xbmcvfs.exists(path):
            log("Fetching image: %s" % url_cdart, xbmc.LOGDEBUG)
            urllib.urlretrieve(url_cdart, destination, _report_hook)
            # message = ["Download Sucessful!"]
            message = [__lang__(32023), __lang__(32024), "File: %s" % get_unicode(path),
                       "Url: %s" % get_unicode(url_cdart)]
            xbmcvfs.copy(destination, final_destination)  # copy it to album folder
            # update database
            try:
                conn = sqlite3.connect(addon_db)
                c = conn.cursor()
                if type_ == "cdart":
                    c.execute('''UPDATE alblist SET cdart="True" WHERE path="%s"''' % (get_unicode(album["path"])))
                elif type_ == "cover":
                    c.execute('''UPDATE alblist SET cover="True" WHERE path="%s"''' % (get_unicode(album["path"])))
                conn.commit()
                c.close()
            except Exception as e:
                log(e.message, xbmc.LOGERROR)
                log("Error updating database", xbmc.LOGDEBUG)
                print_exc()
            download_success = True

        else:
            log("Path error", xbmc.LOGDEBUG)
            log("    file path: %s" % repr(destination), xbmc.LOGDEBUG)
            message = [__lang__(32026), __lang__(32025), "File: %s" % get_unicode(path),
                       "Url: %s" % get_unicode(url_cdart)]
            # message = Download Problem, Check file paths - Artwork Not Downloaded]
        # always cleanup downloaded files
        # if type == "fanart":
        xbmcvfs.delete(destination)
    except Exception as e:
        log(e.message, xbmc.LOGWARNING)
        log("General download error", xbmc.LOGDEBUG)
        message = [__lang__(32026), __lang__(32025), "File: %s" % get_unicode(path),
                   "Url: %s" % get_unicode(url_cdart)]
        # message = [Download Problem, Check file paths - Artwork Not Downloaded]
        # print_exc()
    if mode == "auto" or mode == "single":
        return message, download_success, final_destination, is_canceled  # returns one of the messages built based on success or lack of
    else:
        dialog_msg("close", background=background)
        return message, download_success, is_canceled


def cdart_search(cdart_url, id_, disc):
    cdart = {}
    for item in cdart_url:
        if item["musicbrainz_albumid"] == id_ and item["disc"] == disc:
            cdart = item
            break
    return cdart


# Automatic download of non existing cdarts and refreshes addon's db
def auto_download(type_, artist_list, background=False):
    is_canceled = False
    log("Autodownload", xbmc.LOGDEBUG)
    try:
        artist_count = 0
        download_count = 0
        album_count = 0
        d_error = False
        successfully_downloaded = []
        if type_ in ("clearlogo_allartists", "artistthumb_allartists", "fanart_allartists", "musicbanner_allartists"):
            if type_ == "clearlogo_allartists":
                type_ = "clearlogo"
            elif type_ == "artistthumb_allartists":
                type_ = "artistthumb"
            elif type_ == "musicbanner_allartists":
                type_ = "musicbanner"
            else:
                type_ = "fanart"
        count_artist_local = len(artist_list)
        dialog_msg("create", heading=__lang__(32046), background=background)
        # Onscreen Dialog - Automatic Downloading of Artwork
        key_label = type_
        for artist in artist_list:
            if dialog_msg("iscanceled", background=background) or is_canceled:
                break
            artist_count += 1
            if not artist["has_art"] == "True":
                # If fanart.tv does not report that it has an artist match skip it.
                continue
            percent = int((artist_count / float(count_artist_local)) * 100)
            if percent < 1:
                percent = 1
            if percent > 100:
                percent = 100
            log("Artist: %-40s Local ID: %-10s   Distant MBID: %s" % (
                artist["name"], artist["local_id"], artist["musicbrainz_artistid"]), xbmc.LOGNOTICE)
            if type_ in ("fanart", "clearlogo", "artistthumb", "musicbanner") and artist["has_art"]:
                dialog_msg("update", percent=percent, line1="%s%s" % (__lang__(32038), get_unicode(artist["name"])),
                           background=background)

                temp_art = {"musicbrainz_artistid": artist["musicbrainz_artistid"], "artist": artist["name"]}
                auto_art = {"musicbrainz_artistid": artist["musicbrainz_artistid"], "artist": artist["name"]}

                path = os.path.join(music_path, change_characters(smart_unicode(artist["name"])))
                if type_ == "fanart":
                    art = remote_fanart_list(auto_art)
                elif type_ == "clearlogo":
                    art = remote_hdlogo_list(auto_art)
                    if not art:
                        art = remote_clearlogo_list(auto_art)
                elif type_ == "musicbanner":
                    art = remote_banner_list(auto_art)
                else:
                    art = remote_artistthumb_list(auto_art)
                if art:
                    if type_ == "fanart":
                        temp_art["path"] = path
                        auto_art["path"] = os.path.join(path, "extrafanart").replace("\\\\", "\\")
                        if not xbmcvfs.exists(auto_art["path"]):
                            try:
                                if xbmcvfs.mkdirs(auto_art["path"]):
                                    log("extrafanart directory made", xbmc.LOGDEBUG)
                            except Exception as e:
                                log(e.message, xbmc.LOGWARNING)
                                print_exc()
                                log("unable to make extrafanart directory", xbmc.LOGDEBUG)
                                continue
                        else:
                            log("extrafanart directory already exists", xbmc.LOGDEBUG)
                    else:
                        auto_art["path"] = path
                    if type_ == "fanart":
                        if enable_fanart_limit:
                            fanart_dir, fanart_files = xbmcvfs.listdir(auto_art["path"])
                            fanart_number = len(fanart_files)
                            if fanart_number == fanart_limit:
                                continue
                        if not xbmcvfs.exists(os.path.join(path, "fanart.jpg").replace("\\\\", "\\")):
                            message, d_success, final_destination, is_canceled = download_art(art[0], temp_art,
                                                                                              artist["local_id"],
                                                                                              "fanart", "single", 0,
                                                                                              background)
                        for artwork in art:
                            fanart = {}
                            fanart_number = 0
                            if enable_fanart_limit and fanart_number == fanart_limit:
                                log("Fanart Limit Reached", xbmc.LOGNOTICE)
                                continue
                            if xbmcvfs.exists(os.path.join(auto_art["path"], os.path.basename(artwork))):
                                log("Fanart already exists, skipping", xbmc.LOGDEBUG)
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "fanart", "auto", 0,
                                                                                                  background)
                            if d_success == 1:
                                if enable_fanart_limit:
                                    fanart_number += 1
                                download_count += 1
                                fanart["artist"] = auto_art["artist"]
                                fanart["path"] = final_destination
                                successfully_downloaded.append(fanart)
                            else:
                                log("Download Error...  Check Path.", xbmc.LOGDEBUG)
                                log("    Path: %s" % auto_art["path"], xbmc.LOGDEBUG)
                                d_error = True
                    else:
                        artwork = art[0]
                        d_success = 0
                        final_destination = None
                        if type_ == "artistthumb":
                            if xbmcvfs.exists(os.path.join(auto_art["path"], "folder.jpg")):
                                log("Artist Thumb already exists, skipping", xbmc.LOGDEBUG)
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "artistthumb", "auto",
                                                                                                  0, background)
                        elif type_ == "clearlogo":
                            if xbmcvfs.exists(os.path.join(auto_art["path"], "logo.png")):
                                log("ClearLOGO already exists, skipping", xbmc.LOGDEBUG)
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "clearlogo", "auto",
                                                                                                  0, background)
                        elif type_ == "musicbanner":
                            if xbmcvfs.exists(os.path.join(auto_art["path"], "banner.jpg")):
                                log("Music Banner already exists, skipping", xbmc.LOGDEBUG)
                                continue
                            else:
                                message, d_success, final_destination, is_canceled = download_art(artwork, auto_art,
                                                                                                  artist["local_id"],
                                                                                                  "musicbanner", "auto",
                                                                                                  0, background)
                        if d_success == 1:
                            download_count += 1
                            auto_art["path"] = final_destination
                            successfully_downloaded.append(auto_art)
                        else:
                            log("Download Error...  Check Path.", xbmc.LOGDEBUG)
                            log("    Path: %s" % auto_art["path"], xbmc.LOGDEBUG)
                            d_error = True
                else:
                    log("Artist Match not found", xbmc.LOGDEBUG)
            elif type_ in ("cdart", "cover") and artist["has_art"]:
                local_album_list = get_local_albums_db(artist["name"], background)
                if type_ == "cdart":
                    remote_art_url = remote_cdart_list(artist)
                else:
                    remote_art_url = remote_coverart_list(artist)
                for album in local_album_list:
                    low_res = True
                    if dialog_msg("iscanceled", background=background):
                        break
                    if not remote_art_url:
                        log("No artwork found", xbmc.LOGDEBUG)
                        break
                    album_count += 1
                    if not album["musicbrainz_albumid"]:
                        continue
                    dialog_msg("update", percent=percent,
                               line1="%s%s" % (__lang__(32038), get_unicode(artist["name"])),
                               line2="%s%s" % (__lang__(32039), get_unicode(album["title"])), background=background)
                    log("Album: %s" % album["title"], xbmc.LOGDEBUG)
                    if not album[key_label] or resizeondownload:
                        musicbrainz_albumid = album["musicbrainz_albumid"]
                        art = artwork_search(remote_art_url, musicbrainz_albumid, album["disc"], key_label)
                        if art:
                            if resizeondownload:
                                low_res = check_size(album["path"].replace("\\\\", "\\"), key_label, art["size"],
                                                     art["size"])
                            if art["picture"]:
                                log("ALBUM MATCH ON FANART.TV FOUND", xbmc.LOGDEBUG)
                                # log( "test_album[0]: %s" % test_album[0], xbmc.LOGDEBUG )
                                if low_res:
                                    message, d_success, final_destination, is_canceled = download_art(art["picture"],
                                                                                                      album,
                                                                                                      album["local_id"],
                                                                                                      key_label, "auto",
                                                                                                      0, background)
                                    if d_success == 1:
                                        download_count += 1
                                        album[key_label] = True
                                        album["path"] = final_destination
                                        successfully_downloaded.append(album)
                                    else:
                                        log("Download Error...  Check Path.", xbmc.LOGDEBUG)
                                        log("    Path: %s" % repr(album["path"]), xbmc.LOGDEBUG)
                                        d_error = True
                                else:
                                    pass
                            else:
                                log("ALBUM NOT MATCHED ON FANART.TV", xbmc.LOGDEBUG)
                        else:
                            log("ALBUM NOT MATCHED ON FANART.TV", xbmc.LOGDEBUG)
                    else:
                        log("%s artwork file already exists, skipping..." % key_label, xbmc.LOGDEBUG)
        dialog_msg("close", background=background)
        if d_error:
            dialog_msg("ok", line1=__lang__(32026), line2="%s: %s" % (__lang__(32041), download_count),
                       background=background)
        else:
            dialog_msg("ok", line1=__lang__(32040), line2="%s: %s" % (__lang__(32041), download_count),
                       background=background)
        return download_count, successfully_downloaded
    except Exception as e:
        xbmc.log(e.message, xbmc.LOGERROR)
        print_exc()
        dialog_msg("close", background=background)

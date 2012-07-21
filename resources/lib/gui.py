# -*- coding: utf-8 -*-

import sys
import urllib
import os
import unicodedata
import re
from traceback import print_exc 
import socket
import shutil
import tarfile  
import xbmcgui
import xbmcaddon
import xbmc
from PIL import Image
from string import maketrans
from ftplib import FTP
try:
    from sqlite3 import dbapi2 as sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
# pull information from default.py
__language__         = sys.modules[ "__main__" ].__language__
__scriptname__       = sys.modules[ "__main__" ].__scriptname__
__scriptID__         = sys.modules[ "__main__" ].__scriptID__
__author__           = sys.modules[ "__main__" ].__author__
__credits__          = sys.modules[ "__main__" ].__credits__
__credits2__         = sys.modules[ "__main__" ].__credits2__
__version__          = sys.modules[ "__main__" ].__version__
__addon__            = sys.modules[ "__main__" ].__addon__
__dbversion__        = sys.modules[ "__main__" ].__dbversion__
addon_db             = sys.modules[ "__main__" ].addon_db
addon_db_backup      = sys.modules[ "__main__" ].addon_db_backup
addon_work_folder    = sys.modules[ "__main__" ].addon_work_folder
__useragent__        = sys.modules[ "__main__" ].__useragent__
image                = sys.modules[ "__main__" ].image
BASE_RESOURCE_PATH   = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
#variables
download_temp_folder = os.path.join( addon_work_folder, "temp" )
addon_image_path     = os.path.join( BASE_RESOURCE_PATH, "skins", "Default", "media")
addon_img            = os.path.join( addon_image_path, "cdart-icon.png" )
missing_cdart_image  = os.path.join( addon_image_path, "missing_cdart.png" )
missing_cover_image  = os.path.join( addon_image_path, "missing_cover.png" )
safe_db_version      = __dbversion__
skin_art_path        = os.path.join( BASE_RESOURCE_PATH, "skins", "Default", "media" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )



from convert import set_entity_or_charref
from folder import dirEntries
from fanarttv_scraper import get_distant_artists, retrieve_fanarttv_xml, get_recognized, remote_cdart_list, remote_fanart_list, remote_clearlogo_list, remote_coverart_list, remote_artistthumb_list
from utils import get_html_source, clear_image_cache, empty_tempxml_folder, get_unicode
from download import download_art, auto_download
from database import backup_database, store_alblist, store_lalist, retrieve_distinct_album_artists, store_counts, new_database_setup, get_local_albums_db, get_local_artists_db, new_local_count, refresh_db, artwork_search, update_database, check_album_mbid, check_artist_mbid, update_missing_artist_mbid, update_missing_album_mbid
from musicbrainz_utils import get_musicbrainz_artist_id, get_musicbrainz_album, update_musicbrainzid, get_musicbrainz_artists
from file_item import Thumbnails
from jsonrpc_calls import get_all_local_artists, retrieve_album_list, retrieve_album_details, get_album_path
from xbmcvfs import delete as delete_file
from xbmcvfs import exists as exists
from xbmcvfs import copy as file_copy
try:
    from xbmcvfs import mkdirs as _makedirs
except:
    from utils import _makedirs

kb      = xbmc.Keyboard()
pDialog = xbmcgui.DialogProgress()
#time socket out at 30 seconds
socket.setdefaulttimeout(30)

KEY_BUTTON_BACK  = 275
KEY_KEYBOARD_ESC = 61467

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        pass
        
    def onInit( self ):
        xbmc.log( sys.getdefaultencoding(), xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - ############################################################", xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    %-50s    #" % __scriptname__, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #        gui.py module                                     #", xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    %-50s    #" % __scriptID__, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    %-50s    #" % __author__, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    %-50s    #" % __version__, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    %-50s    #" % __credits__, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    %-50s    #" % __credits2__, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - #    Thanks for the help...                                #", xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - ############################################################", xbmc.LOGNOTICE )
        self.retrieve_settings()
        self.setup_colors()
        try:
            self.setup_all()
        except:
            print_exc()
            try:
                pDialog.close()
            except:
                pass            

    def retrieve_settings( self ):
        backup_path  = xbmc.translatePath( __addon__.getSetting( "backup_path" ) )
        missing_path = xbmc.translatePath( __addon__.getSetting( "missing_path" ) )
        enableresize = xbmc.translatePath( __addon__.getSetting( "enableresize" ) )
        folder       = xbmc.translatePath( __addon__.getSetting( "folder" ) )
        enablecustom = xbmc.translatePath( __addon__.getSetting( "enablecustom" ) )
        xbmc.log( "[script.cdartmanager] - # Settings                                                 #", xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #                                                          #", xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Backup Folder: %-35s    #" % backup_path, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Missing Folder: %-35s    #" % missing_path, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Resize Enabled: %-34s    #" % enableresize, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Saving format: %-35s    #" % folder, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Enable Custom Colours: %-27s    #" % enablecustom, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #                                                          #", xbmc.LOGDEBUG )
        
    def setup_colors( self ):
        if __addon__.getSetting( "enablecustom" ) == "true":
            self.recognized_color   = str.lower( __addon__.getSetting( "recognized" ) )
            self.unrecognized_color = str.lower( __addon__.getSetting( "unrecognized" ) )
            self.remote_color       = str.lower( __addon__.getSetting( "remote" ) )
            self.local_color        = str.lower( __addon__.getSetting( "local" ) )
            self.remotelocal_color  = str.lower( __addon__.getSetting( "remotelocal" ) )
            self.unmatched_color    = str.lower( __addon__.getSetting( "unmatched" ) )
            self.localcdart_color   = str.lower( __addon__.getSetting( "localcdart" ) )
        else:
            self.recognized_color   = "green"
            self.unrecognized_color = "white"
            self.remote_color       = "green"
            self.local_color        = "orange"
            self.remotelocal_color  = "yellow"
            self.unmatched_color    = "white"
            self.localcdart_color   = "orange"
        xbmc.log( "[script.cdartmanager] - ############################################################", xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - # Custom Colours                                           #", xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #                                                          #", xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Recognized: %-38s    #" % self.recognized_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Unrecognized: %-36s    #" % self.unrecognized_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Remote: %-42s    #" % self.remote_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Local: %-43s    #" % self.local_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Local & Remote Match: %-28s    #" % self.remotelocal_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Unmatched: %-39s    #" % self.unmatched_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #    Local cdART: %-37s    #" % self.localcdart_color, xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - #                                                          #", xbmc.LOGDEBUG )
        xbmc.log( "[script.cdartmanager] - ############################################################", xbmc.LOGDEBUG )            

    def remove_special( self, temp ):
        return temp.translate(transtab, "!@#$^*()?[]{}<>',./")

    # sets the colours for the lists
    def coloring( self , text , color , colorword ):
        if color == "white":
            color = "FFFFFFFF"
        if color == "blue":
            color = "FF0000FF"
        if color == "cyan":
            color = "FF00FFFF"
        if color == "violet":
            color = "FFEE82EE"
        if color == "pink":
            color = "FFFF1493"
        if color == "red":
            color = "FFFF0000"
        if color == "green":
            color = "FF00FF00"
        if color == "yellow":
            color = "FFFFFF00"
        if color == "orange":
            color = "FFFF4500"
        colored_text = text.replace( colorword , "[COLOR=%s]%s[/COLOR]" % ( color , colorword ) )
        return colored_text

    def remove_color( self, text ):
        clean_text = text.replace( "[/COLOR]","" ).replace( "[COLOR=FFFFFFFF]","" ).replace( "[COLOR=FF0000FF]","" ).replace( "[COLOR=FF00FFFF]","" ).replace( "[COLOR=FFEE82EE]","" ).replace( "[COLOR=FFFF1493]","" ).replace( "[COLOR=FFFF0000]","" ).replace( "[COLOR=FF00FF00]","" ).replace( "[COLOR=FFFFFF00]","" ).replace( "[COLOR=FFFF4500]","" )
        return clean_text

    #creates the album list on the skin
    def populate_album_list( self, artist_menu, art_url, focus_item, type ):
        xbmc.log( "[script.cdartmanager] - Populating Album List", xbmc.LOGNOTICE )
        self.getControl( 122 ).reset()
        if not art_url:
            #no cdart found
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            xbmcgui.Window(10001).clearProperty( "artwork" )
            xbmcgui.Dialog().ok( __language__(32033), __language__(32030), __language__(32031) )
            #Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
            #return
        else:
            local_album_list = get_local_albums_db( art_url[0]["local_name"], self.background )
            label1 = ""
            label2 = ""
            album_list= {}
            xbmc.log( "[script.cdartmanager] - Building album list", xbmc.LOGNOTICE )
            empty_list = False
            check = False
            try:
                for album in local_album_list:
                    if type == "cdart":
                        art_image = missing_cdart_image
                        filename = "cdart.png"
                    else:
                        art_image = missing_cover_image
                        filename = "folder.jpg"
                    empty_list = False
                    if album["disc"] > 1:
                        label1 = "%s - %s %s" % ( album["title"], __language__(32016), album["disc"] )
                    else:
                        label1 = album["title"]
                    name = art_url[0]["artist"]
                    musicbrainz_albumid = album["musicbrainz_albumid"]
                    if not musicbrainz_albumid:
                        empty_list = True
                        continue
                    else:
                        check = True
                    #check to see if there is a thumb
                    artwork = artwork_search( art_url, musicbrainz_albumid, album["disc"], type )
                    if not artwork:
                        temp_path = os.path.join( album["path"], filename ).replace( "\\\\", "\\" )
                        if exists( temp_path ):
                            url = art_image = temp_path
                            color = self.local_color
                        else:
                            url = art_image
                            color = self.unrecognized_color
                    else:
                        if artwork["picture"]:
                            #check to see if artwork already exists
                            # set the matched colour local and distant colour
                            #colour the label to the matched colour if not
                            url = artwork["picture"]
                            if album[type]:
                                art_image = os.path.join( album["path"], filename ).replace( "\\\\", "\\" )
                                color = self.remotelocal_color
                            else:
                                art_image = url + "/preview"
                                color = self.remote_color                          
                        else:
                            url = ""
                            if album[type]:
                                art_image = os.path.join( album["path"], filename ).replace( "\\\\", "\\" )
                                color = self.local_color
                            else:
                                art_image = url
                                color = self.unmatched_color
                    label2 = "%s&&%s&&&&%s&&%s" % (url, album["path"] , art_image, str(album["local_id"]))
                    listitem = xbmcgui.ListItem( label=label1, label2=label2, thumbnailImage = art_image )
                    self.getControl( 122 ).addItem( listitem )
                    listitem.setLabel( self.coloring( label1 , color , label1 ) )
                    listitem.setLabel2( label2 )                        
                    listitem.setThumbnailImage( art_image )            
                    self.cdart_url = art_url
                    clear_image_cache( art_image )
            except:
                print_exc()
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            if ( not empty_list ) or check:
                self.setFocus( self.getControl( 122 ) )
                self.getControl( 122 ).selectItem( focus_item )
            else:
                xbmcgui.Window(10001).clearProperty( "artwork" )
                xbmcgui.Dialog().ok( __language__(32033), __language__(32030), __language__(32031) )
                #Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
        return
        
    def populate_album_list_mbid( self, local_album_list, selected_item=0 ):
        xbmc.log( "[script.cdartmanager] - MBID Edit - Populating Album List", xbmc.LOGNOTICE )
        if not local_album_list:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            return
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            for album in local_album_list:
                label2 = "%s MBID: %s[CR][COLOR=7fffffff]%s MBID: %s[/COLOR]" % ( __language__( 32138 ), album["musicbrainz_albumid"], __language__( 32137 ), album["musicbrainz_artistid"] )
                label1 = "%s: %s[CR][COLOR=7fffffff]%s: %s[/COLOR][CR][COLOR=FFE85600]%s[/COLOR]" % (  __language__( 32138 ), album["title"],  __language__( 32137 ), album["artist"], album["path"] )
                listitem = xbmcgui.ListItem( label=label1 , label2=label2 )
                self.getControl( 145 ).addItem( listitem )
                listitem.setLabel( label1 )
                listitem.setLabel2( label2 )
        except:
            print_exc()
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        self.setFocus( self.getControl( 145 ) )
        self.getControl( 145 ).selectItem( selected_item )
        return

    def populate_search_list_mbid( self, mbid_list, type="artist", selected_item=0 ):
        xbmc.log( "[script.cdartmanager] - MBID Search - Populating Search List", xbmc.LOGNOTICE )
        if not mbid_list:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            return
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        if type == "artists":
            try:
                for item in mbid_list:
                    label2 = "MBID: %s" % item["id"]
                    label1 = "%-3s%%: %s" % ( item["score"], item["name"] )
                    listitem = xbmcgui.ListItem( label=self.coloring( label1 , "white" , label1 ), label2=label2 )
                    self.getControl( 161 ).addItem( listitem )
                    listitem.setLabel( self.coloring( label1 , "white" , label1 ) )
                    listitem.setLabel2( label2 )
            except:
                print_exc()
        elif type == "albums":
            try:
                for item in mbid_list:
                    label2 = "%s MBID: %s[CR][COLOR=7fffffff]%s MBID: %s[/COLOR]" % ( __language__( 32138 ), item["id"], __language__( 32137 ), item["artist_id"] )
                    label1 = "%-3s%%  %s: %s[CR][COLOR=7fffffff]%s: %s[/COLOR]" % ( item["score"], __language__( 32138 ), item["title"], __language__( 32137 ), item["artist"] )
                    listitem = xbmcgui.ListItem( label=label1, label2=label2 )
                    self.getControl( 161 ).addItem( listitem )
                    listitem.setLabel( label1  )
                    listitem.setLabel2( label2 )
            except:
                print_exc()
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        self.setFocus( self.getControl( 161 ) )
        self.getControl( 161 ).selectItem( selected_item )
        return
        
    def populate_artist_list_mbid( self, local_artist_list, selected_item=0 ):
        xbmc.log( "[script.cdartmanager] - MBID Edit - Populating Artist List", xbmc.LOGNOTICE )
        if not local_artist_list:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            return
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            for artist in local_artist_list:
                label2 = "MBID: %s" % artist["musicbrainz_artistid"]
                label1 = artist["name"]
                listitem = xbmcgui.ListItem( label=label1, label2=label2 )
                self.getControl( 145 ).addItem( listitem )
                listitem.setLabel( label1 )
                listitem.setLabel2( label2 )
        except:
            print_exc()
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        self.setFocus( self.getControl( 145 ) )
        self.getControl( 145 ).selectItem( selected_item )
        return
        
    #creates the artist list on the skin        
    def populate_artist_list( self, local_artist_list):
        xbmc.log( "[script.cdartmanager] - Populating Artist List", xbmc.LOGNOTICE )
        if not local_artist_list:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            return
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        try:
            for artist in local_artist_list:
                if not artist["distant_id"] == "":                    
                    listitem = xbmcgui.ListItem( label=self.coloring( artist["name"] , "green" , artist["name"] ) )
                    self.getControl( 120 ).addItem( listitem )
                    listitem.setLabel( self.coloring( artist["name"] , self.recognized_color , artist["name"] ) )
                else:
                    listitem = xbmcgui.ListItem( label=artist["name"] )
                    self.getControl( 120 ).addItem( listitem )
                    listitem.setLabel( self.coloring( artist["name"] , self.unrecognized_color , artist["name"] ) )
        except KeyError:
            for artist in local_artist_list:
                label2 = "MBID: %s" % artist["musicbrainz_artistid"]
                label1 = artist["name"]
                listitem = xbmcgui.ListItem( label=label1, label2=label2 )
                self.getControl( 120 ).addItem( listitem )
                listitem.setLabel( label1 )
                listitem.setLabel2( label2 )
        except:
            print_exc()
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        self.setFocus( self.getControl( 120 ) )
        self.getControl( 120 ).selectItem( 0 )
        return

    def populate_fanarts( self, artist_menu, focus_item ):
        xbmc.log( "[script.cdartmanager] - Populating Fanart List", xbmc.LOGNOTICE )
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        self.getControl( 160 ).reset()
        try:
            fanart = remote_fanart_list( artist_menu )
            if fanart:
                for artwork in fanart:
                    #listitem = xbmcgui.ListItem( label = os.path.basename( artwork ), label2 = artist_menu["name"] + "&&&&" + artwork, thumbnailImage = artwork )
                    listitem = xbmcgui.ListItem( label = os.path.basename( artwork ), label2 = artist_menu["name"] + "&&&&" + artwork, thumbnailImage = artwork + "/preview" )
                    self.getControl( 160 ).addItem( listitem )
                    listitem.setLabel( os.path.basename( artwork ) )
                    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                    self.setFocus( self.getControl( 160 ) )
                    self.getControl( 160 ).selectItem( focus_item )
            else:
                xbmc.log( "[script.cdartmanager - No Fanart for this artist", xbmc.LOGNOTICE )
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmcgui.Window(10001).clearProperty( "artwork" )
                xbmcgui.Dialog().ok( __language__(32033), __language__(32030), __language__(32031) )
                #Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            print_exc()
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
    def populate_clearlogos( self, artist_menu, focus_item ):
        xbmc.log( "[script.cdartmanager] - Populating ClearLOGO List", xbmc.LOGNOTICE )
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        self.getControl( 167 ).reset()
        try:
            clearlogo = remote_clearlogo_list( artist_menu )
            if clearlogo:
                for artwork in clearlogo:
                    clear_image_cache( artwork )
                    listitem = xbmcgui.ListItem( label = os.path.basename( artwork ), label2 = artist_menu["name"] + "&&&&" + artwork, thumbnailImage = artwork + "/preview" )
                    self.getControl( 167 ).addItem( listitem )
                    listitem.setLabel( os.path.basename( artwork ) )
                    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                    self.setFocus( self.getControl( 167 ) )
                    self.getControl( 167 ).selectItem( focus_item )
            else:
                xbmc.log( "[script.cdartmanager - No ClearLOGO for this artist", xbmc.LOGNOTICE )
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmcgui.Window(10001).clearProperty( "artwork" )
                xbmcgui.Dialog().ok( __language__(32033), __language__(32030), __language__(32031) )
                #Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            print_exc()
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    def populate_artistthumbs( self, artist_menu, focus_item ):
        xbmc.log( "[script.cdartmanager] - Populating artist thumb List", xbmc.LOGNOTICE )
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        self.getControl( 199 ).reset()
        try:
            artistthumb = remote_artistthumb_list( artist_menu )
            if artistthumb:
                for artwork in artistthumb:
                    clear_image_cache( artwork )
                    listitem = xbmcgui.ListItem( label = os.path.basename( artwork ), label2 = artist_menu["name"] + "&&&&" + artwork, thumbnailImage = artwork + "/preview" )
                    self.getControl( 199 ).addItem( listitem )
                    listitem.setLabel( os.path.basename( artwork ) )
                    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                    self.setFocus( self.getControl( 199 ) )
                    self.getControl( 199 ).selectItem( focus_item )
            else:
                xbmc.log( "[script.cdartmanager - No artist thumb for this artist", xbmc.LOGNOTICE )
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmcgui.Window(10001).clearProperty( "artwork" )
                xbmcgui.Dialog().ok( __language__(32033), __language__(32030), __language__(32031) )
                #Onscreen Dialog - Not Found on Fanart.tv, Please contribute! Upload your cdARTs, On fanart.tv
                return
        except:
            print_exc()
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    def populate_downloaded( self, successfully_downloaded, type ):
        xbmc.log( "[script.cdartmanager] - Populating ClearLOGO List", xbmc.LOGNOTICE )
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        self.getControl( 404 ).reset()
        xbmcgui.Window(10001).setProperty( "artwork", type )
        for item in successfully_downloaded:
            try:
                try:
                    listitem = xbmcgui.ListItem( label = item["artist"], label2 = item["title"], thumbnailImage = item["path"] )
                except:
                    listitem = xbmcgui.ListItem( label = item["artist"], label2 = "", thumbnailImage = item["path"] )
                self.getControl( 404 ).addItem( listitem )
                listitem.setLabel( item["artist"] )
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                self.setFocus( self.getControl( 404 ) )
                self.getControl( 404 ).selectItem( 0 )
            except:
                print_exc()
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    def populate_local_cdarts( self, focus_item ):
        xbmc.log( "[script.cdartmanager] - Populating Local cdARTS", xbmc.LOGNOTICE )
        label2= ""
        cdart_img=""
        url = ""
        work_temp = []
        l_artist = get_local_albums_db( "all artists", self.background )
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        self.getControl( 140 ).reset()
        for album in l_artist:
            if album["cdart"]:
                cdart_img = os.path.join( album["path"], "cdart.png" )
                label2 = "%s&&%s&&&&%s&&%s" % ( url, album["path"], cdart_img, album["local_id"] )
                label1 = "%s * %s" % ( album["artist"] , album["title"] )
                listitem = xbmcgui.ListItem( label=label1, label2=label2, thumbnailImage=cdart_img )
                self.getControl( 140 ).addItem( listitem )
                listitem.setLabel( self.coloring( label1 , "orange" , label1 ) )
                listitem.setLabel2( label2 )
                work_temp.append( album )
            else:
                pass
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        self.setFocus( self.getControl( 140 ) )
        self.getControl( 140 ).selectItem( focus_item )
        return work_temp

    def single_unique_copy(self, artist, album, source):
        xbmc.log( "[script.cdartmanager] - Copying to Unique Folder: %s - %s" % ( artist, album ) , xbmc.LOGNOTICE )
        destination = ""
        fn_format = int( __addon__.getSetting( "folder" ) )
        unique_folder = __addon__.getSetting( "unique_path" )
        if unique_folder =="":
            __addon__.openSettings()
            unique_folder = __addon__.getSetting( "unique_path" )
        resize = __addon__.getSetting( "enableresize" )
        xbmc.log( "[script.cdartmanager] - Resize: %s" % resize, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - Unique Folder: %s" % repr( unique_folder ), xbmc.LOGNOTICE )
        if exists(source):
            xbmc.log( "[script.cdartmanager] - source: %s" % repr( source ), xbmc.LOGNOTICE )
            if fn_format == 0:
                destination=os.path.join( unique_folder, ( artist.replace( "/","" ) ).replace( "'","" ) ) #to fix AC/DC
                fn = os.path.join( destination, ( ( ( album.replace( "/","" ) ).replace( "'","" ) ) + ".png" ) )
            else:
                destination=unique_folder
                fn = os.path.join( destination, ( ( ( (artist.replace( "/", "" ) ).replace( "'","" ) ) + " - " + ( ( album.replace( "/","" ) ).replace( "'","" ) ) + ".png" ).lower() ) )
            xbmc.log( "[script.cdartmanager] - destination: %s" % repr( destination ), xbmc.LOGNOTICE )
            if not exists(destination):
                #pass
                _makedirs(destination)
            else:
                pass
            try:
                xbmc.log( "[script.cdartmanager] - Saving: %s" % repr( fn ), xbmc.LOGNOTICE )
                file_copy(source, fn)
            except:
                xbmc.log( "[script.cdartmanager] - Copying error, check path and file permissions", xbmc.LOGNOTICE )
        else:
            xbmc.log( "[script.cdartmanager] - Error: cdART file does not exist..  Please check...", xbmc.LOGNOTICE )
        return

    def single_backup_copy(self, artist, album, source):
        xbmc.log( "[script.cdartmanager] - Copying To Backup Folder: %s - %s" % ( artist, album ) , xbmc.LOGNOTICE )
        destination = ""
        fn_format = int(__addon__.getSetting("folder"))
        backup_folder = __addon__.getSetting("backup_path")
        if backup_folder =="":
            __addon__.openSettings()
            backup_folder = __addon__.getSetting("backup_path")
        xbmc.log( "[script.cdartmanager] - source: %s" % source, xbmc.LOGNOTICE )
        if exists(source):
            xbmc.log( "[script.cdartmanager] - source: %s" % source, xbmc.LOGNOTICE )
            if fn_format == 0:
                destination=os.path.join(backup_folder, (artist.replace("/","")).replace("'","")) #to fix AC/DC
                fn = os.path.join(destination, ( ((album.replace("/","")).replace("'","")) + ".png"))
            else:
                destination=backup_folder
                fn = os.path.join(destination, ((((artist.replace("/", "")).replace("'","")) + " - " + ((album.replace("/","")).replace("'","")) + ".png").lower()))
            xbmc.log( "[script.cdartmanager] - destination: %s" % destination, xbmc.LOGNOTICE )
            if not exists(destination):
                #pass
                _makedirs(destination)
            else:
                pass
            xbmc.log( "[script.cdartmanager] - filename: %s" % fn, xbmc.LOGNOTICE )
            try:
                file_copy(source, fn)
            except:
                xbmc.log( "[script.cdartmanager] - copying error, check path and file permissions", xbmc.LOGNOTICE )
        else:
            xbmc.log( "[script.cdartmanager] - Error: cdART file does not exist..  Please check...", xbmc.LOGNOTICE )
        return

    def single_cdart_delete(self, source, album):
        xbmc.log( "[script.cdartmanager] - Deleting: %s" % source, xbmc.LOGNOTICE )
        conn = sqlite3.connect(addon_db)
        c = conn.cursor()
        cdart = False
        if exists(source):
            try:
                delete_file( source )
                c.execute("""UPDATE alblist SET cdart=%s WHERE title='%s'""" % ( cdart, album ) )
                conn.commit()
            except:
                xbmc.log( "[script.cdartmanager] - Deleteing error, check path and file permissions", xbmc.LOGNOTICE )
        else:
            xbmc.log( "[script.cdartmanager] - Error: cdART file does not exist..  Please check...", xbmc.LOGNOTICE )
        c.close()
        return
    
    # Copy's all the local unique cdARTs to a folder specified by the user
    def unique_cdart_copy( self, unique ):
        xbmc.log( "[script.cdartmanager] - Copying Unique cdARTs...", xbmc.LOGNOTICE )
        percent = 0
        count = 0
        duplicates = 0
        destination = ""
        album = {}
        fn_format = int(__addon__.getSetting("folder"))
        unique_folder = __addon__.getSetting("unique_path")
        if unique_folder =="":
            __addon__.openSettings()
            unique_folder = __addon__.getSetting("unique_path")
        resize = __addon__.getSetting("enableresize")
        xbmc.log( "[script.cdartmanager] - Unique Folder: %s" % unique_folder, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - Resize: %s" % resize, xbmc.LOGNOTICE )
        pDialog.create( __language__(32060) )
        for album in unique:
            percent = int((count/len(unique))*100)
            xbmc.log( "[script.cdartmanager] - Artist: %-30s    ##    Album:%s" % (album["artist"], album["title"]), xbmc.LOGNOTICE )
            if (pDialog.iscanceled()):
                break
            if album["local"] == "TRUE" and album["distant"] == "FALSE":
                source=os.path.join(album["path"].replace("\\\\" , "\\"), "cdart.png")
                xbmc.log( "[script.cdartmanager] - Source: %s" % repr(source), xbmc.LOGNOTICE )
                if exists(source):
                    if fn_format == 0:
                        destination=os.path.join(unique_folder, (album["artist"].replace("/","")).replace("'","")) #to fix AC/DC
                        fn = os.path.join(destination, ( ((album["title"].replace("/","")).replace("'","")) + ".png"))
                    else:
                        destination=unique_folder
                        fn = os.path.join(destination, ((((album["artist"].replace("/", "")).replace("'","")) + " - " + ((album["title"].replace("/","")).replace("'","")) + ".png").lower()))
                    if not exists(destination):
                        #pass
                        os.makedirs(destination)
                    else:
                        pass
                    xbmc.log( "[script.cdartmanager] - Destination: %s" % repr(fn), xbmc.LOGNOTICE )
                    if exists(fn):
                        xbmc.log( "[script.cdartmanager] - ################## cdART Not being copied, File exists: %s" % repr(fn), xbmc.LOGNOTICE )
                        duplicates += 1
                    else:
                        try:
                            xbmc.log( "[script.cdartmanager] - Saving: %s" % repr(fn)                                    , xbmc.LOGNOTICE )
                            file_copy(source, fn)
                            conn = sqlite3.connect(addon_db)
                            c = conn.cursor()
                            c.execute("insert into unqlist(title, artist, path, cdart) values (?, ?, ?, ?)", ( unicode(album["title"], 'utf-8'), unicode(album["artist"], 'utf-8'), repr(album["path"]), album["local"]))
                            c.commit
                            count += 1
                        except:
                            xbmc.log( "[script.cdartmanager] - Copying error, check path and file permissions", xbmc.LOGNOTICE )
                            count += 1
                        c.close()
                        pDialog.update( percent, __language__(32064) % unique_folder , "Filename: %s" % fn, "%s: %s" % ( __language__(32056) , count ) )
                else:
                    xbmc.log( "[script.cdartmanager] - Error: cdART file does not exist..  Please check...", xbmc.LOGNOTICE )
            else:
                if album["local"] and album["distant"]:
                    xbmc.log( "[script.cdartmanager] - Local and Distant cdART exists", xbmc.LOGNOTICE )
                else:
                    xbmc.log( "[script.cdartmanager] - Local cdART does not exists", xbmc.LOGNOTICE )
        pDialog.close()
        xbmcgui.Dialog().ok( __language__(32057), "%s: %s" % ( __language__(32058), unique_folder), "%s %s" % ( count , __language__(32059)))
        # uncomment the next line when website is ready
        #self.compress_cdarts( unique_folder )
        return

    def restore_from_backup( self ):
        xbmc.log( "[script.cdartmanager] - Restoring cdARTs from backup folder", xbmc.LOGNOTICE )
        pDialog.create( __language__(32069) )
        #Onscreen Dialog - Restoring cdARTs from backup...
        bkup_folder = __addon__.getSetting("backup_path")
        if bkup_folder =="":
            __addon__.openSettings()
            bkup_folder = __addon__.getSetting("backup_path")
        else:
            pass
        self.copy_cdarts(bkup_folder)
        pDialog.close()
        
    def copy_cdarts( self, from_folder ): 
        xbmc.log( "[script.cdartmanager] - Copying cdARTs from: %s" % repr(from_folder), xbmc.LOGNOTICE )
        conn = sqlite3.connect(addon_db)
        c = conn.cursor()
        destination = ""
        source = ""
        fn = ""
        part = {}
        local_db = []
        percent = 0
        count = 0
        total_albums = 0 
        total_count = 0
        fn_format = int(__addon__.getSetting("folder"))
        xbmc.log( "[script.cdartmanager] - Filename format: %s" % fn_format, xbmc.LOGNOTICE )
        xbmc.log( "[script.cdartmanager] - From Folder: %s" % from_folder, xbmc.LOGNOTICE )
        local_db = get_local_albums_db( "all artists", self.background )
        total_albums=len(local_db)
        xbmc.log( "[script.cdartmanager] - total albums: %s" % total_albums, xbmc.LOGNOTICE )
        pDialog.create( __language__(32069) )
        for album in local_db:
            if (pDialog.iscanceled()):
                break
            xbmc.log( "[script.cdartmanager] - Artist: %-30s  ##  Album: %s" % (repr(album["artist"]), repr(album["title"])), xbmc.LOGNOTICE )
            xbmc.log( "[script.cdartmanager] - Album Path: %s" % repr(album["path"]), xbmc.LOGNOTICE )
            percent = int(total_count/float(total_albums))*100
            if fn_format == 0:
                source=os.path.join( from_folder, (album["artist"].replace("/","").replace("'","") ) )#to fix AC/DC and other artists with a / in the name
                if album["disc"] > 1:
                    fn = os.path.join( source, ( ( album["title"].replace("/","").replace("'","") ) + "_disc_" + str( album["disc"] ) + ".png") )
                else:
                    fn = os.path.join( source, ( ( album["title"].replace("/","").replace("'","") ) + ".png") )
                if not exists(fn):
                    source = os.path.join( from_folder )
                    if album["disc"] > 1:
                        fn = os.path.join(source, ( ( ( album["artist"].replace("/", "").replace("'","") ) + " - " + ( album["title"].replace("/","").replace("'","") ) + "_disc_" + str( album["disc"] ) + ".png").lower() ) )
                    else:
                        fn = os.path.join(source, ( ( ( album["artist"].replace("/", "").replace("'","") ) + " - " + ( album["title"].replace("/","").replace("'","") ) + ".png").lower() ) )
            else:
                source=os.path.join( from_folder ) #to fix AC/DC
                if album["disc"] > 1:
                    fn = os.path.join(source, ( ( ( album["artist"].replace("/", "").replace("'","") ) + " - " + ( album["title"].replace("/","").replace("'","") ) + "_disc_" + str( album["disc"] ) + ".png").lower() ) )
                else:
                    fn = os.path.join(source, ( ( ( album["artist"].replace("/", "").replace("'","") ) + " - " + ( album["title"].replace("/","").replace("'","") ) + ".png").lower() ) )
                if not exists(fn):
                    source=os.path.join( from_folder, (album["artist"].replace("/","").replace("'","") ) )#to fix AC/DC and other artists with a / in the name
                    fn = os.path.join(source, ( ( album["title"].replace("/","").replace("'","") ) + ".png") )
            xbmc.log( "[script.cdartmanager] - Source folder: %s" % repr( source ), xbmc.LOGNOTICE )
            xbmc.log( "[script.cdartmanager] - Source filename: %s" % repr( fn ), xbmc.LOGNOTICE )
            if exists(fn):
                destination = os.path.join(album["path"], "cdart.png")
                xbmc.log( "[script.cdartmanager] - Destination: %s" % repr(destination), xbmc.LOGNOTICE )
                try:
                    file_copy(fn, destination)
                    if not from_folder == __addon__.getSetting("backup_path"):
                        delete_file( fn )  # remove file
                    count += 1
                except:
                    xbmc.log( "[script.cdartmanager] - ######  Copying error, check path and file permissions", xbmc.LOGNOTICE )
                try:
                    c.execute("""UPDATE alblist SET cdart="True" WHERE path='%s'""" % album["path"] )
                except:
                    xbmc.log( "[script.cdartmanager] - ######  Problem modifying Database!!  Artist: %s   Album: %s" % (repr(album["artist"]), repr(album["title"])), xbmc.LOGNOTICE )
            else:
                pass
            pDialog.update( percent , "From Folder: %s" % from_folder, "Filename: %s" % repr( fn ), "%s: %s" % ( __language__(32056) , count ) )
            total_count += 1
        pDialog.close()
        conn.commit()
        c.close()
        xbmcgui.Dialog().ok( __language__(32057),  "%s %s" % ( count , __language__(32070) ) ) 
        return        
        
    # copy cdarts from music folder to temporary location
    # first step to copy to skin folder
    def cdart_copy( self ):
        xbmc.log( "[script.cdartmanager] - Copying cdARTs to Backup folder", xbmc.LOGNOTICE )
        destination = ""
        duplicates = 0
        percent = 0
        count = 0
        total = 0
        album = {}
        albums = []
        fn_format = int(__addon__.getSetting( "folder" ) )
        bkup_folder = __addon__.getSetting( "backup_path" )
        cdart_list_folder = __addon__.getSetting( "cdart_path" )
        if bkup_folder =="":
            __addon__.openSettings()
            bkup_folder = __addon__.getSetting( "backup_path" )
            cdart_list_folder = __addon__.getSetting( "cdart_path" )
        albums = get_local_albums_db( "all artists", self.background )
        pDialog.create( __language__(32060) )
        for album in albums:
            if (pDialog.iscanceled()):
                break
            if album["cdart"]:
                source=os.path.join( album["path"].replace( "\\\\" , "\\" ), "cdart.png" )
                xbmc.log( "[script.cdartmanager] - cdART #: %s" % count, xbmc.LOGNOTICE )
                xbmc.log( "[script.cdartmanager] - Artist: %-30s  Album: %s" % ( repr( album["artist"] ), repr( album["title"] ) ), xbmc.LOGNOTICE )
                xbmc.log( "[script.cdartmanager] - Album Path: %s" % repr( source ), xbmc.LOGNOTICE )
                if exists(source):
                    if fn_format == 0:
                        destination=os.path.join( bkup_folder, ( album["artist"].replace("/","").replace("'","") ) ) #to fix AC/DC
                        if album["disc"] > 1:
                            fn = os.path.join( destination, ( ( album["title"].replace("/","").replace("'","") ) + "_disc_" + str( album["disc"] ) + ".png") )
                        else:
                            fn = os.path.join( destination, ( ( album["title"].replace("/","").replace("'","") ) + ".png") )
                    elif fn_format == 1:
                        destination=os.path.join( bkup_folder ) #to fix AC/DC
                        if album["disc"] > 1:
                            fn = os.path.join( destination, ( ( album["artist"].replace("/", "").replace("'","") ) + " - " + ( album["title"].replace("/","").replace("'","") ) + "_disc_" + str( album["disc"] ) + ".png").lower() )
                        else:
                            fn = os.path.join( destination, ( ( album["artist"].replace("/", "").replace("'","") ) + " - " + ( album["title"].replace("/","").replace("'","") ) + ".png").lower() )
                    xbmc.log( "[script.cdartmanager] - Destination Path: %s" % repr( destination ), xbmc.LOGNOTICE )
                    if not exists(destination):
                        _makedirs(destination)
                    xbmc.log( "[script.cdartmanager] - Filename: %s" % repr( fn ), xbmc.LOGNOTICE )
                    if exists(fn):
                        xbmc.log( "[script.cdartmanager] - ################## cdART Not being copied, File exists: %s" % repr( fn ), xbmc.LOGNOTICE )
                        duplicates += 1
                    else:
                        try:
                            file_copy(source, fn)
                            count += 1
                            pDialog.update( percent , "backup folder: %s" % bkup_folder, "Filename: %s" % repr( fn ), "%s: %s" % ( __language__(32056) , count ) )
                        except:
                            xbmc.log( "[script.cdartmanager] - ######  Copying error, check path and file permissions", xbmc.LOGNOTICE )
                else:
                    xbmc.log( "[script.cdartmanager] - ######  Copying error, cdart.png does not exist", xbmc.LOGNOTICE )
            else:
                pass
            percent = int(total/float(len(albums))*100)
            total += 1
        pDialog.close()
        xbmc.log( "[script.cdartmanager] - Duplicate cdARTs: %s" % duplicates, xbmc.LOGNOTICE )
        xbmcgui.Dialog().ok( __language__(32057), "%s: %s" % ( __language__(32058), bkup_folder), "%s %s" % ( count , __language__(32059)), "%s Duplicates Found" % duplicates)
        return        
        
# Search for missing cdARTs and save to missing.txt in Missing List path
    def missing_list( self ):
        xbmc.log( "[script.cdartmanager] - Saving missing.txt file", xbmc.LOGNOTICE )
        count = 0
        percent = 0
        line = ""
        path_provided = False
        missing_path = xbmc.translatePath( __addon__.getSetting( "missing_path" ) )
        albums = get_local_albums_db("all artists", self.background)
        artists = get_local_artists_db( mode="local_artists" )
        if not artists:
            artists = get_local_artists_db( mode="album_artists" )
        pDialog.create( __language__(32103), __language__(20186) )
        temp_destination = os.path.join( addon_work_folder, "missing.txt")
        if missing_path:
            final_destination = os.path.join( missing_path, "missing.txt" )
            path_provided = True
        else:
            xbmc.log( "[script.cdartmanager] - Path for missing.txt file not provided", xbmc.LOGNOTICE )
            path_provided = False
        try:
            missing=open( temp_destination, "wb" )
            pDialog.update( percent )
            missing.write("Albums Missing Artwork\n")
            missing.write("\n")
            missing.write("|  %-45s|  %-75s              |  %-50s|  cdART  |  Cover  |\n" % ( "MusicBrainz ID", "Album Title", "Album Artist" ) )
            missing.write("-" * 214)
            missing.write("\n")
            percent = 1
            for album in albums:
                percent = percent = int( ( count/float( len( albums ) ) ) * 100 ) 
                count +=1
                if percent == 0:
                    percent = 1
                if percent > 100:
                    percent = 100
                if ( pDialog.iscanceled() ):
                    break
                try:
                    pDialog.update( percent, __language__(32103), " %s: %s" % ( __language__( 32039 ), album["title"].encode("utf-8") ) )
                except:
                    pDialog.update( percent, __language__( 32103 ), " %s: %s" % ( __language__( 32039 ), repr( album["title"] ) ) )
                cdart = " "
                cover = " "
                if album["cdart"]:
                    cdart = "X"
                if album["cover"]:
                    cover = "X"
                if album["cdart"] and album["cover"]:
                    continue
                else:
                    if int( album["disc"] ) > 1:
                        line = "|  %-45s| %-75s     disc#: %2s |  %-50s|    %s    |    %s    |\n" % ( album["musicbrainz_albumid"], album["title"], album["disc"], album["artist"], cdart, cover )
                    elif int( album["disc"] ) == 1:
                        line = "|  %-45s| %-75s               |  %-50s|    %s    |    %s    |\n" % ( album["musicbrainz_albumid"], album["title"], album["artist"], cdart, cover )
                    else:
                        line = ""
                    if line:
                        try:
                            missing.write( line.encode("utf8") )
                        except:
                            missing.write( repr(line) )
                        missing.write("-" * 214)
                        missing.write("\n")
            missing.write("\n")
            pDialog.update( 50 )
            missing.write("Artists Missing Artwork\n")
            missing.write("\n")
            music_path = xbmc.translatePath( __addon__.getSetting( "music_path" ) )
            missing.write("|  %-45s| %-70s|  Fanart  |  clearLogo  |  Artist Thumb |\n" % ( "MusicBrainz ID", "Artist Name" ) )
            missing.write("-" * 162)
            missing.write("\n")
            count = 0
            percent =1
            for artist in artists:
                count +=1
                percent = percent = int( ( count/float( len( artists ) ) ) * 100 ) 
                if percent == 0:
                    percent = 1
                if percent > 100:
                    percent = 100
                if ( pDialog.iscanceled() ):
                    break
                try:
                    pDialog.update( percent, __language__( 32103 ), " %s: %s" % ( __language__( 32038 ), artist["name"].encode("utf-8") ) )
                except:
                    pDialog.update( percent, __language__( 32103 ), " %s: %s" % ( __language__( 32038 ), repr( artist["name"] ) ) )
                fanart = " "
                clearlogo = " "
                artistthumb = " "
                line = ""
                fanart_path = os.path.join( music_path, artist["name"], "fanart.jpg" ).replace( "\\\\", "\\" )
                clearlogo_path = os.path.join( music_path, artist["name"], "logo.png" ).replace( "\\\\", "\\" )
                artistthumb_path = os.path.join( music_path, artist["name"], "folder.jpg" ).replace( "\\\\", "\\" )
                if exists( fanart_path ):
                    fanart = "X"
                if exists( clearlogo_path ):
                    clearlogo = "X"
                if exists( artistthumb_path ):
                    artistthumb = "X"
                if not exists( fanart_path ) or not exists( clearlogo_path ) or not exists( artistthumb_path ):
                    line = "|  %-45s| %-70s|     %s    |     %s       |       %s       |\n" % ( artist["musicbrainz_artistid"], artist["name"], fanart, clearlogo, artistthumb )
                if line:
                    try:
                        missing.write( line.encode("utf8") )
                    except:
                        missing.write( repr( line ) )
                    missing.write("-" * 162)
                    missing.write("\n")
            missing.close()
        except:
            xbmc.log( "[script.cdartmanager] - Error saving missing.txt file", xbmc.LOGNOTICE )
            print_exc()
        if exists( temp_destination ) and path_provided:
            file_copy( temp_destination, final_destination )
        pDialog.close()
                    
    def refresh_counts( self, local_album_count, local_artist_count, local_cdart_count ):
        xbmc.log( "[script.cdartmanager] - Refreshing Counts", xbmc.LOGNOTICE )
        self.getControl( 109 ).setLabel( __language__(32007) % local_artist_count)
        self.getControl( 110 ).setLabel( __language__(32010) % local_album_count)
        self.getControl( 112 ).setLabel( __language__(32008) % local_cdart_count)
        
    # This selects which cdART image shows up in the display box (image id 210) 
    def cdart_icon( self ):
        blank_art = os.path.join( skin_art_path, "blank_artwork.png")
        image = blank_art
        cdart_path = {}
        try: # If there is information in label 2 of list id 140(local album list)
            local_cdart = ( self.getControl(140).getSelectedItem().getLabel2() ).split("&&&&")[1]
            url = (( self.getControl( 140 ).getSelectedItem().getLabel2() ).split("&&&&")[0]).split("&&")[1]
            cdart_path["path"] = ((self.getControl( 140 ).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[0]
            xbmc.log( "[script.cdartmanager] - # cdART url: %s" % url, xbmc.LOGNOTICE )
            xbmc.log( "[script.cdartmanager] - # cdART path: %s" % cdart_path["path"], xbmc.LOGNOTICE )
            if not local_cdart == "": #Test to see if there is a path in local_cdart
                image = (local_cdart.replace("\\\\" , "\\"))
                self.getControl( 210 ).setImage( image )
            else:
                if not cdart_path["path"] =="": #Test to see if there is an url in cdart_path["path"]
                    image = (cdart_path["path"].replace("\\\\" , "\\"))
                    self.getControl( 210 ).setImage( image )
                else:
                    image =""
                    #image = addon_img
        except: # If there is not any information in any of those locations, no image.
            print_exc()
            image = blank_art
        self.getControl( 210 ).setImage( image )

    def clear_artwork( self ):
        self.getControl( 211 ).setImage( addon_img )
        self.getControl( 210 ).setImage( addon_img )
            
    def popup(self, header, line1, line2, line3):        
        #self.getControl( 400 ).setLabel( header )
        #self.getControl( 401 ).setLabel( line1 )
        #self.getControl( 402 ).setLabel( line2 )
        #self.getControl( 403 ).setLabel( line3 )
        #self.getControl( 9012 ).setVisible( True )
        pDialog.create( header, line1, line2, line3 )
        xbmc.sleep(2000)
        pDialog.close()
        #self.getControl( 9012 ).setVisible( False ) 

    def get_mbid_keyboard( self, type = "artist" ):
        mbid = "canceled"
        if type == "artist":
            kb.setHeading( __language__( 32159 ) )
            #default_text = self.artist_menu["musicbrainz_artistid"]
        elif type == "albumartist":
            kb.setHeading( __language__( 32159 ) )
            #default_text = self.album_menu["musicbrainz_artistid"]
        elif type == "album":
            kb.setHeading( __language__( 32166 ) )
            #default_text = self.album_menu["musicbrainz_albumid"]
        #try:
        #    kb.setDefault( default_text )
        #except:
        #    kb.setDefault( repr( default_text ) )
        kb.doModal()
        while(1):
            if not (kb.isConfirmed()):
                canceled = True
                break
            else:
                mbid = kb.getText()
                if type == "artist":
                    if len(mbid) == 0 and not len(self.artist_menu["musicbrainz_artistid"]) == 0:
                        if xbmcgui.Dialog().yesno( __language__( 32163 ), self.artist_menu["musicbrainz_artistid"] ):
                            canceled = False
                            break
                elif type == "albumartist":
                    if len(mbid) == 0 and not len(self.artist_menu["musicbrainz_artistid"]) == 0:
                        if xbmcgui.Dialog().yesno( __language__( 32163 ), self.album_menu["musicbrainz_artistid"] ):
                            canceled = False
                            break
                elif type == "album":
                    if len(mbid) == 0 and not len(self.artist_menu["musicbrainz_albumid"]) == 0:
                        if xbmcgui.Dialog().yesno( __language__( 32163 ), self.album_menu["musicbrainz_albumid"] ):
                            canceled = False
                            break
                if len(mbid) == 36:
                    if xbmcgui.Dialog().yesno( __language__( 32162 ), mbid ):
                        canceled = False
                        break
                    else:
                        mbid = "canceled"
                        kb.doModal()
                        continue
                if len(mbid) == 32: # user did not enter dashes
                    temp_mbid = list( mbid )
                    temp_mbid.insert( 8, "-" )
                    temp_mbid.insert( 13, "-" )
                    temp_mbid.insert( 18, "-" )
                    temp_mbid.insert( 23, "-" )
                    mbid = "".join( temp_mbid )
                else:
                    mbid = "canceled"
                    if xbmcgui.Dialog().yesno( __language__(32160), __language__(32161) ):
                        kb.doModal()
                        continue
                    else:
                        canceled = True
                        break
        return mbid, canceled

    # setup self. strings and initial local counts
    def setup_all( self ):
        self.background = False
        xbmc.log( "[script.cdartmanager] - # Setting up Script", xbmc.LOGNOTICE )
        self.menu_mode = 0
        self.artist_menu = {}
        self.remote_cdart_url =[]
        self.recognized_artists = []
        self.all_artists = []
        self.cdart_url = []
        self.local_artists = []
        self.local_albums = []
        self.label_1 = ""
        self.label_2 = addon_img
        self.cdartimg = ""
        self.artwork_type = ""
        self.artists = []
        self.albums = []
        self.album_artists = []
        self.album_artists_recognized = []
        self.all_artists_recognized = []
        self.all_artists_list = []
        self.recognized_artists = []
        self.selected_item = 0
        listitem = xbmcgui.ListItem( label=self.label_1, label2=self.label_2, thumbnailImage=self.cdartimg )
        self.getControl( 122 ).addItem( listitem )
        listitem.setLabel2(self.label_2)
        #checking to see if addon_db exists, if not, run database_setup()
        if exists( (addon_db).replace("\\\\" , "\\").encode("utf-8") ):
            xbmc.log( "[script.cdartmanager] - Addon Db found - Loading Counts", xbmc.LOGNOTICE )
            local_album_count, local_artist_count, local_cdart_count = new_local_count()
        else:
            xbmc.log( "[script.cdartmanager] - Addon Db Not Found - Building New Addon Db", xbmc.LOGNOTICE )
            local_album_count, local_artist_count, local_cdart_count = new_database_setup( self.background )
        self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
        self.local_artists = get_local_artists_db() # retrieve data from addon's database
        self.setFocusId( 100 ) # set menu selection to the first option(cdARTs)
        distant_artist = get_distant_artists()
        local_artists = get_local_artists_db( mode="album_artists" )
        if __addon__.getSetting("enable_all_artists") == "true":
            all_artists = get_local_artists_db( mode="all_artists" )
        else:
            all_artists = []
        if distant_artist:
            self.album_recognized_artists, self.all_artists_recognized, self.all_artists_list, self.album_artists = get_recognized( distant_artist, all_artists, local_artists )
        

    def onClick( self, controlId ):
        #print controlId
        empty = []
        if controlId in ( 105, 150 ) : #cdARTs Search Artists 
            if controlId == 105:
                self.menu_mode = 1
                self.artwork_type = "cdart"
            elif controlId == 150:
                self.menu_mode = 3
                self.artwork_type = "cover"
            self.recognized_artists = self.album_recognized_artists
            self.local_artists = self.album_artists
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            self.getControl( 120 ).reset()
            self.getControl( 140 ).reset()
            self.populate_artist_list( self.recognized_artists )
        if controlId == 120: #Retrieving information from Artists List
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            #self.clear_artwork()
            self.artist_menu = {}
            if not self.menu_mode == 11:
                self.artist_menu["local_id"] = ( self.recognized_artists[self.getControl( 120 ).getSelectedPosition()]["local_id"] )
                self.artist_menu["name"] = get_unicode( self.recognized_artists[self.getControl( 120 ).getSelectedPosition()]["name"] )
                self.artist_menu["musicbrainz_artistid"] = get_unicode( self.local_artists[self.getControl( 120 ).getSelectedPosition()]["musicbrainz_artistid"] )
            else:
                self.artist_menu["local_id"] = ( self.local_artists[self.getControl( 120 ).getSelectedPosition()]["local_id"] )
                self.artist_menu["name"] = get_unicode( self.local_artists[self.getControl( 120 ).getSelectedPosition()]["name"] )
                self.artist_menu["musicbrainz_artistid"] = get_unicode( self.local_artists[self.getControl( 120 ).getSelectedPosition()]["musicbrainz_artistid"] )
            if not self.menu_mode in ( 10, 11, 12, 14):
                self.artist_menu["distant_id"] = get_unicode( self.recognized_artists[self.getControl( 120 ).getSelectedPosition()]["distant_id"] )
                if not self.artist_menu["musicbrainz_artistid"]:
                    self.artist_menu["musicbrainz_artistid"] = update_musicbrainzid( "artist", self.artist_menu )
            artist_name = get_unicode( self.artist_menu["name"] )
            self.getControl( 204 ).setLabel( __language__(32038) + "[CR]%s" % artist_name )
            if self.menu_mode == 1:
                self.remote_cdart_url = remote_cdart_list( self.artist_menu )
                xbmcgui.Window(10001).setProperty( "artwork", "cdart" )
                self.populate_album_list( self.artist_menu, self.remote_cdart_url, 0, "cdart" )
            elif self.menu_mode == 3:
                self.remote_cdart_url = remote_coverart_list( self.artist_menu )
                xbmcgui.Window(10001).setProperty( "artwork", "cover" )
                self.populate_album_list( self.artist_menu, self.remote_cdart_url, 0, "cover" )
            elif self.menu_mode == 6:
                xbmcgui.Window(10001).setProperty( "artwork", "fanart" )
                self.populate_fanarts( self.artist_menu, 0 )
            elif self.menu_mode == 7:
                xbmcgui.Window(10001).setProperty( "artwork", "clearlogo" )
                self.populate_clearlogos( self.artist_menu, 0 )
            elif self.menu_mode == 9:
                xbmcgui.Window(10001).setProperty( "artwork", "artistthumb" )
                self.populate_artistthumbs( self.artist_menu, 0 )
            elif self.menu_mode == 11:
                self.local_albums = get_local_albums_db( self.artist_menu["name"] )
                self.getControl( 145 ).reset()
                self.populate_album_list_mbid( self.local_albums )
        if controlId == 145:
            self.selected_item = self.getControl( 145 ).getSelectedPosition()
            if self.menu_mode == 10: # Artist
                self.artist_menu = {}
                self.artist_menu["local_id"] = ( self.local_artists[self.getControl( 145 ).getSelectedPosition()]["local_id"] )
                self.artist_menu["name"] = get_unicode( self.local_artists[self.getControl( 145 ).getSelectedPosition()]["name"] )
                self.artist_menu["musicbrainz_artistid"] = get_unicode( self.local_artists[self.getControl( 145 ).getSelectedPosition()]["musicbrainz_artistid"] )
                self.setFocusId( 157 )
                try:
                    self.getControl( 156 ).setLabel( __language__(32038) + "[CR]%s" % self.artist_menu["name"].encode("utf-8") )
                except:
                    self.getControl( 156 ).setLabel( __language__(32038) + "[CR]%s" % repr( self.artist_menu["name"] ) )
            if self.menu_mode in ( 11, 12 ): # Album
                self.album_menu = {}
                self.album_menu["local_id"] = ( self.local_albums[self.getControl( 145 ).getSelectedPosition()]["local_id"] )
                self.album_menu["title"] = get_unicode( self.local_albums[self.getControl( 145 ).getSelectedPosition()]["title"] )
                self.album_menu["musicbrainz_albumid"] = get_unicode( self.local_albums[self.getControl( 145 ).getSelectedPosition()]["musicbrainz_albumid"] )
                self.album_menu["artist"] = get_unicode( self.local_albums[self.getControl( 145 ).getSelectedPosition()]["artist"] )
                self.album_menu["path"] = get_unicode( self.local_albums[self.getControl( 145 ).getSelectedPosition()]["path"] )
                self.album_menu["musicbrainz_artistid"] = get_unicode( self.local_albums[self.getControl( 145 ).getSelectedPosition()]["musicbrainz_artistid"] )
                self.setFocusId( 157 )
                try:
                    self.getControl( 156 ).setLabel( __language__(32039) + "[CR]%s" % self.album_menu["title"].encode("utf-8") )
                except:
                    self.getControl( 156 ).setLabel( __language__(32039) + "[CR]%s" % repr( self.album_menu["title"] ) )
        if controlId == 157: #Manual Edit
            canceled = False
            if self.menu_mode == 10: # Artist
                conn = sqlite3.connect(addon_db)
                c = conn.cursor()
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                mbid, canceled = self.get_mbid_keyboard( "artist" )
                if not canceled:
                    try:
                        c.execute('''UPDATE lalist SET musicbrainz_artistid="%s" WHERE local_id=%s''' % ( mbid, self.artist_menu["local_id"] ) )
                    except:
                        xbmc.log( "[script.cdartmanager] - Error updating database(lalist)", xbmc.LOGERROR )
                        print_exc()
                    try:
                        c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s" WHERE local_id=%s''' % ( mbid, self.artist_menu["local_id"] ) )
                    except:
                        xbmc.log( "[script.cdartmanager] - Error updating database(local_artists)", xbmc.LOGERROR )
                        print_exc()
                    conn.commit()
                c.close()
            if self.menu_mode == 11: # album
                conn = sqlite3.connect(addon_db)
                c = conn.cursor()
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                artist_mbid, canceled = self.get_mbid_keyboard( "albumartist" )
                if not canceled:
                    album_mbid, canceled = self.get_mbid_keyboard( "album" )
                    if not canceled:
                        try:
                            c.execute('''UPDATE alblist SET musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s and path="%s"''' % ( album_mbid, artist_mbid, self.album_menu["local_id"], self.album_menu["path"] ) )
                        except:
                            xbmc.log( "[script.cdartmanager] - Error updating database(alblist)", xbmc.LOGERROR )
                            print_exc()
                        try:
                            c.execute('''UPDATE lalist SET musicbrainz_artistid="%s" WHERE local_id=%s''' % ( mbid, self.album_menu["local_id"] ) )
                        except:
                            xbmc.log( "[script.cdartmanager] - Error updating database(lalist)", xbmc.LOGERROR )
                            print_exc()
                        try:
                            c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s" WHERE local_id=%s''' % ( mbid, self.album_menu["local_id"] ) )
                        except:
                            xbmc.log( "[script.cdartmanager] - Error updating database(local_artists)", xbmc.LOGERROR )
                            print_exc()
                        conn.commit()
                c.close()
            distant_artist = get_distant_artists()
            local_artists = get_local_artists_db( mode="album_artists" )
            if __addon__.getSetting("enable_all_artists") == "true":
                all_artists = get_local_artists_db( mode="all_artists" )
            else:
                all_artists = []
            if distant_artist:
                self.album_recognized_artists, self.all_artists_recognized, self.all_artists_list, self.album_artists = get_recognized( distant_artist, all_artists, local_artists )
            if self.menu_mode == 11:
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                self.getControl( 145 ).reset()
                self.local_albums = get_local_albums_db( "all artists" )
                self.populate_album_list_mbid( self.local_albums, self.selected_item )
            elif self.menu_mode == 10:
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                self.getControl( 145 ).reset()
                if __addon__.getSetting("enable_all_artists") == "true":
                    self.local_artists = all_artists
                else:
                    self.local_artists = local_artists
                self.populate_artist_list_mbid( self.local_artists )
        if controlId == 122 : #Retrieving information from Album List
            self.getControl( 140 ).reset()
            select = None
            local = ""
            url = ""
            album = {}
            album_search=[]
            album_selection=[]
            cdart_path = {}
            local_cdart = ""
            count = 0
            select=0
            local_cdart =  ( (self.getControl(122).getSelectedItem().getLabel2() ).split("&&&&")[1] ).split("&&")[0]
            database_id = int( ( ( self.getControl(122).getSelectedItem().getLabel2() ).split("&&&&")[1] ).split("&&")[1] )
            url = ((self.getControl( 122 ).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[0]
            cdart_path["path"] = ((self.getControl( 122 ).getSelectedItem().getLabel2()).split("&&&&")[0]).split("&&")[1]
            try:
                cdart_path["artist"] = ( self.getControl( 204 ).getLabel().encode('utf-8') ).replace( __language__(32038) + "[CR]","")
            except:
                cdart_path["artist"] = ( self.getControl( 204 ).getLabel().decode('utf-8') ).replace( __language__(32038) + "[CR]","")
            cdart_path["title"] = self.getControl( 122 ).getSelectedItem().getLabel()
            cdart_path["title"] = self.remove_color(cdart_path["title"])
            self.selected_item = self.getControl( 122 ).getSelectedPosition()
            if not url =="" : # If it is a recognized Album...
                if self.menu_mode == 1:
                    message, d_success, is_canceled = download_art( url, cdart_path, database_id, "cdart", "manual", 0 )
                elif self.menu_mode == 3:
                    message, d_success, is_canceled = download_art( url, cdart_path, database_id, "cover", "manual", 0 )
                try:
                    pDialog.close()
                except:
                    pass # pDialog not open anyways
                try:
                    xbmcgui.Dialog().ok( message[0], message[1], message[2], message[3] )
                except:
                    xbmcgui.Dialog().ok( message[0], message[1], repr( message[2] ), repr( message[3] ) )
            else : # If it is not a recognized Album...
                xbmc.log( "[script.cdartmanager] - Oops --  Some how I got here... - ControlID(122)", xbmc.LOGDEBUG )
            local_album_count, local_artist_count, local_cdart_count = new_local_count()
            self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
            artist_name = self.artist_menu["name"].decode("utf-8")
            self.getControl( 204 ).setLabel( __language__(32038) + "[CR]%s" % artist_name )
            if self.menu_mode == 1:
                self.remote_cdart_url = remote_cdart_list( self.artist_menu )
                xbmcgui.Window(10001).setProperty( "artwork", "cdart" )
                self.populate_album_list( self.artist_menu, self.remote_cdart_url, self.selected_item, "cdart" )
            elif self.menu_mode == 3:
                self.remote_cdart_url = remote_coverart_list( self.artist_menu )
                xbmcgui.Window(10001).setProperty( "artwork", "cover" )
                self.populate_album_list( self.artist_menu, self.remote_cdart_url, self.selected_item, "cover" )
        if controlId == 132 : #Clean Music database selected from Advanced Menu
            xbmc.log( "[script.cdartmanager] - #  Executing Built-in - CleanLibrary(music)", xbmc.LOGNOTICE )
            xbmc.executebuiltin( "CleanLibrary(music)") 
        if controlId == 133 : #Update Music database selected from Advanced Menu
            xbmc.log( "[script.cdartmanager] - #  Executing Built-in - UpdateLibrary(music)", xbmc.LOGNOTICE )
            xbmc.executebuiltin( "UpdateLibrary(music)")
        if controlId == 135 : #Back up cdART selected from Advanced Menu
            self.cdart_copy()
        if controlId == 134 : 
            xbmc.log( "[script.cdartmanager] - No function here anymore", xbmc.LOGNOTICE )
        if controlId == 131 : #Modify Local Database
            self.setFocusId( 190 ) # change when other options 
        if controlId == 190 : # backup database
            backup_database()
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ( __language__(32042), __language__(32139), 2000, image) )
        if controlId == 191 : #Refresh Local database selected from Advanced Menu
            refresh_db( False )
            try:
                pDialog.close()
            except:
                pass
            distant_artist = get_distant_artists()
            local_artists = get_local_artists_db( mode="album_artists" )
            if __addon__.getSetting("enable_all_artists") == "true":
                all_artists = get_local_artists_db( mode="all_artists" )
            else:
                all_artists = []
            if distant_artist:
                self.album_recognized_artists, self.all_artists_recognized, self.all_artists_list, self.album_artists = get_recognized( distant_artist, all_artists, local_artists )
            local_album_count, local_artist_count, local_cdart_count = new_local_count()
            self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
        if controlId == 192: #Update database
            update_database( False )
            try:
                pDialog.close()
            except:
                pass
            distant_artist = get_distant_artists()
            local_artists = get_local_artists_db( mode="album_artists" )
            if __addon__.getSetting("enable_all_artists") == "true":
                all_artists = get_local_artists_db( mode="all_artists" )
            else:
                all_artists = []
            if distant_artist:
                self.album_recognized_artists, self.all_artists_recognized, self.all_artists_list, self.album_artists = get_recognized( distant_artist, all_artists, local_artists )
            local_album_count, local_artist_count, local_cdart_count = new_local_count()
            self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
        if controlId == 136 : #Restore from Backup
            self.restore_from_backup()
            local_album_count, local_artist_count, local_cdart_count = new_local_count()
            self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
        if controlId == 137 : #Local cdART List
            self.getControl( 122 ).reset()
            self.menu_mode = 8
            xbmcgui.Window(10001).setProperty( "artwork", "cdart" )
            self.populate_local_cdarts( 0 )
        if controlId == 107 :
            self.setFocusId( 200 )
        if controlId == 108 :
            self.setFocusId( 200 ) 
        if controlId == 130 : #cdART Backup Menu
            self.setFocusId( 135 )
        if controlId == 140 : #Local cdART selection
            self.cdart_icon()
            self.setFocusId( 142 )
            artist_album = self.getControl(140).getSelectedItem().getLabel()
            artist_album = self.remove_color(artist_album)
            artist = artist_album.split(" * ")[0]
            album_title = artist_album.split(" * ")[1]
            self.getControl( 300 ).setLabel( self.getControl(140).getSelectedItem().getLabel() )
        if controlId in ( 142, 143, 144 ):
            path = ((self.getControl( 140 ).getSelectedItem().getLabel2()).split("&&&&")[1]).split("&&")[0]
            database_id = int( ( (self.getControl( 140 ).getSelectedItem().getLabel2()).split("&&&&")[1]).split("&&")[1] )
            artist_album = self.getControl(140).getSelectedItem().getLabel()
            artist_album = self.remove_color(artist_album)
            artist = artist_album.split(" * ")[0]
            album_title = artist_album.split(" * ")[1]
            if controlId == 143:  #Delete cdART
                self.single_cdart_delete( path, album_title )
                local_album_count, local_artist_count, local_cdart_count = new_local_count()
                self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
                popup_label = __language__( 32075 )
            elif controlId == 142: #Backup to backup folder
                self.single_backup_copy( artist, album_title, path )
                popup_label = __language__( 32074 )
            else: #Copy to Unique folder
                self.single_unique_copy( artist, album_title, path )
                popup_label = __language__( 32076 )
            self.popup( popup_label, self.getControl(140).getSelectedItem().getLabel(),"", "")
            self.setFocusId( 140 )            
            self.populate_local_cdarts()
        if controlId == 100 : #cdARTS
            self.artwork_type = "cdart"
            self.setFocusId( 105 )
        if controlId == 101 : #Cover Arts
            self.artwork_type = "cover"
            self.setFocusId( 150 )
        if controlId == 103 : #Advanced
            self.setFocusId( 130 )
        if controlId == 104 : #Settings
            self.menu_mode = 5
            __addon__.openSettings()
            self.setup_colors()
        if controlId == 111 : #Exit
            self.menu_mode = 0
            empty_tempxml_folder()
            if __addon__.getSetting("enable_missing") == "true":
                self.missing_list()
            self.close()
        if controlId in ( 180, 181 ): # fanart Search Album Artists
            self.menu_mode = 6
        if controlId in ( 184, 185 ): # Clear Logo Search Artists
            self.menu_mode = 7
        if controlId in ( 197, 198 ): # Artist Thumb Search Artists
            self.menu_mode = 9
        if controlId == 102:
            self.artwork_type = "fanart"
            self.setFocusId( 170 )
        if controlId == 170:
            self.setFocusId( 180 )
        if controlId == 171:
            self.setFocusId( 182 )
        if controlId == 168:
            self.setFocusId( 184 )
        if controlId == 169:
            self.setFocusId( 186 )
        if controlId == 193:
            self.setFocusId( 197 )
        if controlId == 194:
            self.setFocusId( 195 )
        if controlId == 152:
            self.artwork_type = "clearlogo"
            xbmcgui.Window(10001).setProperty( "artwork", "clearlogo" )
            self.menu_mode = 7
            self.setFocusId( 168 )
        if controlId == 153:
            self.artwork_type = "artistthumb"
            xbmcgui.Window(10001).setProperty( "artwork", "artistthumb" )
            self.menu_mode = 9
            self.setFocusId( 193 )
        if controlId in ( 180, 181, 184, 185, 197, 198 ):
            distant_artist = get_distant_artists()
            if controlId in ( 180, 184, 197 ):
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                self.getControl( 120 ).reset()
                self.recognized_artists = self.album_recognized_artists
                self.local_artists = self.album_artists
                self.populate_artist_list( self.recognized_artists )
            elif controlId in ( 181, 185, 198 ) and __addon__.getSetting("enable_all_artists") == "true":
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                self.getControl( 120 ).reset()
                self.recognized_artists = self.all_artists_recognized
                self.local_artists = self.all_artists_list
                self.populate_artist_list( self.recognized_artists )
        if controlId == 167:
            artist = {}
            if self.menu_mode == 7:
                url = ( self.getControl( 167 ).getSelectedItem().getLabel2() ).split("&&&&")[ 1 ]
                artist["artist"] = ( self.getControl( 167 ).getSelectedItem().getLabel2() ).split("&&&&")[ 0 ]
                artist["path"] = os.path.join( __addon__.getSetting("music_path"), artist["artist"] )
                selected_item = self.getControl( 167 ).getSelectedPosition()
                if url:
                    message, success, is_canceled = download_art( url, artist, self.artist_menu["local_id"], "clearlogo", "manual", 0 )
                    try:
                        pDialog.close()
                    except:
                        pass
                    try:
                        xbmcgui.Dialog().ok( message[0], message[1], message[2], message[3] )
                    except:
                        xbmcgui.Dialog().ok( message[0], message[1], repr( message[2] ), repr( message[3] ) )
                else:
                    xbmc.log( "[script.cdartmanager] - Nothing to download", xbmc.LOGDEBUG )
                xbmcgui.Window(10001).setProperty( "artwork", "clearlogo" )
                self.populate_clearlogos( self.artist_menu, selected_item )
        if controlId == 160:
            artist = {}
            if self.menu_mode == 6:
                url = ( self.getControl( 160 ).getSelectedItem().getLabel2() ).split("&&&&")[ 1 ]
                artist["artist"] = ( self.getControl( 160 ).getSelectedItem().getLabel2() ).split("&&&&")[ 0 ]
                artist["path"] =  os.path.join( __addon__.getSetting("music_path"), artist["artist"] )
                selected_item = self.getControl( 160 ).getSelectedPosition()
                if url:
                    message, success, is_canceled = download_art( url, artist, self.artist_menu["local_id"], "fanart", "manual", 0 )
                    try:
                        pDialog.close()
                    except:
                        pass
                    try:
                        xbmcgui.Dialog().ok( message[0], message[1], message[2], message[3] )
                    except:
                        xbmcgui.Dialog().ok( message[0], message[1], repr( message[2] ), repr( message[3] ) )
                else:
                    xbmc.log( "[script.cdartmanager] - Nothing to download", xbmc.LOGDEBUG )
                xbmcgui.Window(10001).setProperty( "artwork", "fanart" )
                self.populate_fanarts( self.artist_menu, selected_item )
        if controlId == 199:
            artist = {}
            if self.menu_mode == 9:
                url = ( self.getControl( 199 ).getSelectedItem().getLabel2() ).split("&&&&")[ 1 ]
                artist["artist"] = ( self.getControl( 199 ).getSelectedItem().getLabel2() ).split("&&&&")[ 0 ]
                artist["path"] = os.path.join( __addon__.getSetting("music_path"), artist["artist"] )
                selected_item = self.getControl( 199 ).getSelectedPosition()
                if url:
                    download_art( url, artist, self.artist_menu["local_id"], "artistthumb", "manual", 0 )
                    try:
                        pDialog.close()
                    except:
                        pass
                else:
                    xbmc.log( "[script.cdartmanager] - Nothing to download", xbmc.LOGDEBUG )
                xbmcgui.Window(10001).setProperty( "artwork", "artistthumb" )
                self.populate_artistthumbs( self.artist_menu, selected_item )
        if controlId in ( 182, 186, 187, 183, 106, 151, 195, 196 ): # Automatic Download
            self.artwork_type = ""
            if controlId in ( 106, 151, 186, 182, 195 ):
                self.recognized_artists = self.album_recognized_artists
                self.local_artists = self.album_artists
                if controlId == 106: #cdARTs
                    self.menu_mode = 2
                    self.artwork_type = "cdart"
                elif controlId == 151: #cover arts
                    self.menu_mode = 4
                    self.artwork_type = "cover"
                elif controlId == 186:# ClearLOGOs
                    self.artwork_type = "clearlogo"
                elif controlId == 182:# Fanarts
                    self.artwork_type = "fanart"
                elif controlId == 195:# Artist Thumbs
                    self.artwork_type = "artistthumb"
                download_count, successfully_downloaded = auto_download( self.artwork_type, self.recognized_artists, self.local_artists  )
                local_album_count, local_artist_count, local_cdart_count = new_local_count()
                self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
                if successfully_downloaded:
                    self.populate_downloaded( successfully_downloaded, self.artwork_type )
            if controlId in ( 183, 187, 196 ) and __addon__.getSetting("enable_all_artists") == "true":
                self.recognized_artists = self.all_artists_recognized
                self.local_artists = self.all_artists_list
                if controlId == 187:# ClearLOGOs All Artists
                    self.artwork_type = "clearlogo_allartists"
                if controlId == 183:# Fanarts All Artists
                    self.artwork_type = "fanart_allartists"
                if controlId == 196:# Artist Thumbs All Artists
                    self.artwork_type = "artistthumb_allartists"            
                download_count, successfully_downloaded = auto_download( self.artwork_type, self.recognized_artists, self.local_artists  )
                local_album_count, local_artist_count, local_cdart_count = new_local_count()
                self.refresh_counts( local_album_count, local_artist_count, local_cdart_count )
                if successfully_downloaded:
                    self.populate_downloaded( successfully_downloaded, self.artwork_type )
        if controlId == 113:
            self.setFocusId( 107 )
        if controlId == 114: # Refresh Artist MBIDs
            self.setFocusId( 139 ) # change to 138 when selected artist is added to script
        if controlId == 189: # Edit By Album
            self.setFocusId( 123 )
        if controlId == 115: # Find Missing Artist MBIDs
            if __addon__.getSetting("enable_all_artists") == "true":
                updated_artists, canceled = update_missing_artist_mbid( empty, False, mode="all_artists" )
            else:
                updated_artists, canceled = update_missing_artist_mbid( empty, False, mode="album_artists" )
            conn = sqlite3.connect(addon_db)
            c = conn.cursor()
            for updated_artist in updated_artists:
                if updated_artist["musicbrainz_artistid"]:
                    try:
                        c.execute('''UPDATE lalist SET musicbrainz_artistid="%s" WHERE local_id=%s''' % ( updated_artist["musicbrainz_artistid"], updated_artist["local_id"] ) )
                    except:
                        xbmc.log( "[script.cdartmanager] - Error updating database", xbmc.LOGERROR )
                        print_exc()
                    try:
                        c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s" WHERE local_id=%s''' % ( updated_artist["musicbrainz_artistid"], updated_artist["local_id"] ) )
                    except:
                        xbmc.log( "[script.cdartmanager] - Error updating database", xbmc.LOGERROR )
                        print_exc()
            conn.commit()
            c.close()
        if controlId == 139: # Automatic Refresh Artist MBIDs
            check_artist_mbid( empty, False, mode = "album_artists" )
        if controlId == 123:
            self.setFocusId( 126 )
        if controlId == 124: # Refresh Album MBIDs
            self.setFocusId( 148 ) # change to 147 when selected album is added to script
        if controlId == 125:
            updated_albums, canceled = update_missing_album_mbid( empty, False )
            conn = sqlite3.connect(addon_db)
            c = conn.cursor()
            for updated_album in updated_albums:
                if updated_album["musicbrainz_albumid"]:
                    try:
                        c.execute('''UPDATE alblist SET musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s''' % ( updated_album["musicbrainz_albumid"], updated_album["musicbrainz_artistid"], updated_album["local_id"] ) )
                    except:
                        xbmc.log( "[script.cdartmanager] - Error updating database", xbmc.LOGERROR )
                        print_exc()
            conn.commit()
            c.close()
        if controlId == 126:
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            self.getControl( 120 ).reset()
            self.menu_mode = 11
            self.local_artists = get_local_artists_db( "album_artists")
            self.populate_artist_list( self.local_artists )
        if controlId == 127: # Change Album MBID
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            self.getControl( 145 ).reset()
            self.local_albums = get_local_albums_db( "all artists" )
            self.menu_mode = 12
            self.populate_album_list_mbid( self.local_albums )
        if controlId == 148: # Automatic Refresh Album MBIDs
            check_album_mbid( empty, False )
        if controlId == 113:
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            self.getControl( 145 ).reset()
            self.menu_mode = 10
            if __addon__.getSetting("enable_all_artists") == "true":
                self.local_artists = get_local_artists_db( "all_artists")
            else:
                self.local_artists = get_local_artists_db( "album_artists")
            self.populate_artist_list_mbid( self.local_artists )
        if controlId == 158:
            self.getControl( 161 ).reset()
            artist = ""
            album = ""
            albums = []
            artists = []
            canceled = False
            if self.menu_mode == 10:
                kb.setHeading( __language__( 32164 ) )
                try:
                    kb.setDefault( self.artist_menu["name"] )
                except:
                    kb.setDefault( repr(self.artist_menu["name"] ) )
                kb.doModal()
                while(1):
                    if not (kb.isConfirmed()):
                        canceled = True
                        break
                    else:
                        artist = kb.getText()
                        canceled = False
                        break
                if not canceled:
                    self.artists = get_musicbrainz_artists( artist, 10 )
                    if self.artists:
                        self.populate_search_list_mbid( self.artists, "artists" )
            if self.menu_mode in ( 11, 12 ):
                kb.setHeading( __language__( 32165 ) )
                try:
                    kb.setDefault( self.album_menu["title"] )
                except:
                    kb.setDefault( repr(self.album_menu["title"] ) )
                kb.doModal()
                while(1):
                    if not (kb.isConfirmed()):
                        canceled = True
                        break
                    else:
                        album = kb.getText()
                        canceled = False
                        break
                if not canceled:
                    kb.setHeading( __language__( 32164 ) )
                    try:
                        kb.setDefault( self.album_menu["artist"] )
                    except:
                        kb.setDefault( repr(self.album_menu["artist"] ) )
                    kb.doModal()
                    while(1):
                        if not (kb.isConfirmed()):
                            canceled = True
                            break
                        else:
                            artist = kb.getText()
                            canceled = False
                            break
                    if not canceled:
                        album, self.albums = get_musicbrainz_album( album, artist, 0, 10 )
                if self.albums:
                    self.populate_search_list_mbid( self.albums, "albums" )
        if controlId == 159:
            self.getControl( 161 ).reset()
            if self.menu_mode == 10:
                self.artists = get_musicbrainz_artists( self.artist_menu["name"], 10 )
                if self.artists:
                    self.populate_search_list_mbid( self.artists, "artists" )
            if self.menu_mode in ( 11, 12 ):
                album, self.albums = get_musicbrainz_album( self.album_menu["title"], self.album_menu["artist"], 0, 10 )
                if self.albums:
                    self.populate_search_list_mbid( self.albums, "albums" )
        if controlId == 161:
            conn = sqlite3.connect(addon_db)
            c = conn.cursor()
            if self.menu_mode == 10:
                artist_musicbrainzid = self.artists[self.getControl( 161 ).getSelectedPosition()]["id"]
                artist_name = self.artists[self.getControl( 161 ).getSelectedPosition()]["name"]
                try:
                    c.execute('''UPDATE lalist SET musicbrainz_artistid="%s", name="%s" WHERE local_id=%s''' % ( artist_musicbrainzid, artist_name, self.artist_menu["local_id"] ) )
                except:
                    xbmc.log( "[script.cdartmanager] - Error updating database", xbmc.LOGERROR )
                    print_exc()
                try:
                    c.execute('''UPDATE local_artists SET musicbrainz_artistid="%s", name="%s" WHERE local_id=%s''' % ( artist_musicbrainzid, artist_name, self.artist_menu["local_id"] ) )
                except:
                    xbmc.log( "[script.cdartmanager] - Error updating database", xbmc.LOGERROR )
                    print_exc()
                conn.commit()
                c.close()
                self.getControl( 145 ).reset()
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                if __addon__.getSetting("enable_all_artists") == "true":
                    self.local_artists = get_local_artists_db( "all_artists")
                else:
                    self.local_artists = get_local_artists_db( "album_artists")
                self.populate_artist_list_mbid( self.local_artists, self.selected_item )
            if self.menu_mode in ( 11, 12 ):
                artist_name = self.albums[self.getControl( 161 ).getSelectedPosition()]["artist"]
                album_title = self.albums[self.getControl( 161 ).getSelectedPosition()]["title"]
                artist_musicbrainzid = self.albums[self.getControl( 161 ).getSelectedPosition()]["artist_id"]
                album_musicbrainzid = self.albums[self.getControl( 161 ).getSelectedPosition()]["id"]
                try:
                    c.execute('''UPDATE alblist SET artist="%s", title="%s", musicbrainz_albumid="%s", musicbrainz_artistid="%s" WHERE album_id=%s and path="%s"''' % ( artist_name, album_title, album_musicbrainzid, artist_musicbrainzid, self.album_menu["local_id"], self.album_menu["path"] ) )
                except:
                    xbmc.log( "[script.cdartmanager] - Error updating database", xbmc.LOGERROR )
                    print_exc()
                conn.commit()
                c.close()
                self.getControl( 145 ).reset()
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                if self.menu_mode == 12:
                    self.local_albums = get_local_albums_db( "all artists" )
                    self.populate_album_list_mbid( self.local_albums, self.selected_item )
                else:
                    self.local_albums = get_local_albums_db( self.artist_menu["name"] )
                    self.populate_album_list_mbid( self.local_albums, self.selected_item )
                    
    def onFocus( self, controlId ):
        if not controlId in( 122, 140, 160, 167, 199 ):
            xbmcgui.Window(10001).clearProperty( "artwork" )
        if controlId == 140:
            self.cdart_icon()
        if controlId in ( 100, 101, 152, 103, 104, 111):
            xbmcgui.Window(10001).clearProperty( "artwork" )
            self.menu_mode = 0

    def onAction( self, action ):
        if self.menu_mode == 8:
            self.cdart_icon()
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        if (buttonCode == KEY_BUTTON_BACK or buttonCode == KEY_KEYBOARD_ESC):
            self.close()
            empty_tempxml_folder()
            if __addon__.getSetting("enable_missing") == "true":
                self.missing_list()
        if actionID == 10:
            xbmc.log( "[script.cdartmanager] - Closing", xbmc.LOGNOTICE )
            try:
                pDialog.close()
            except:
                pass
            empty_tempxml_folder()
            if __addon__.getSetting("enable_missing") == "true":
                self.missing_list()
            self.close()

def onAction( self, action ):
    if (buttonCode == KEY_BUTTON_BACK or buttonCode == KEY_KEYBOARD_ESC):
            empty_tempxml_folder()
            if __addon__.getSetting("enable_missing") == "true":
                self.missing_list()
            self.close()
    if ( action.getButtonCode() in CANCEL_DIALOG ):
        xbmc.log( "[script.cdartmanager] - Closing", xbmc.LOGNOTICE )
        empty_tempxml_folder()
        if __addon__.getSetting("enable_missing") == "true":
            self.missing_list()
        self.close()

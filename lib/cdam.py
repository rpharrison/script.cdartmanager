import xbmc
import xbmcaddon


class CDAM:

    # this is shared between all instances
    __addon = None

    def __init__(self):
        if self.__addon is None:
            self.reload()

    @classmethod
    def reload(cls):
        cls.__addon = xbmcaddon.Addon(id="script.cdartmanager")

    def getAddon(self):
        """:rtype : xbmcaddon.Addon"""
        return self.__addon

    # info

    def __getAddonInfo__(self, info):
        return self.getAddon().getAddonInfo(info)

    def getLocalizedString(self, string):
        return self.getAddon().getLocalizedString(string)

    def name(self):
        return self.__getAddonInfo__('name')

    def id(self):
        return self.__getAddonInfo__('id')

    def author(self):
        return self.__getAddonInfo__('author')

    def version(self):
        return self.__getAddonInfo__('version')

    def path(self):
        return self.__getAddonInfo__('path')

    def icon(self):
        return self.__getAddonInfo__('icon')

    def fanart(self):
        return self.__getAddonInfo__('fanart')

    def profile(self):
        return self.__getAddonInfo__('profile')

    # strings

    def credits(self):
        return [
            self.name(),
            "%s by %s - Branch NG / v%s" % (self.id(), self.author(), self.version()),
            "This addon is yet another fork of the original",
            "cdART Manager by giftie, thanks to all contributors!"
        ]

    def user_agent(self):
        return "%s\\%s (%s)" % (self.name(), self.version(), Constants.useragent_base())

    # files and folders

    @staticmethod
    def __aspath__(path):
        return xbmc.translatePath(path)

    def file_icon(self):
        return self.__aspath__(self.icon())


    # more

    def log(self, text, severity=xbmc.LOGDEBUG):
        if type(text).__name__ == 'unicode':
            text = text.encode('utf-8')
        message = ('[%s] - %s' % (self.name(), text.__str__()))
        xbmc.log(msg=message, level=severity)


class Settings:
    # this is shared between all instances
    __addon = None

    def __init__(self):
        if self.__addon is None:
            self.reload()

    @classmethod
    def reload(cls):
        cls.__addon = xbmcaddon.Addon(id=Constants.script_id())

    def getAddon(self):
        """:rtype : xbmcaddon.Addon"""
        return self.__addon

    def __getSetting__(self, setting):
        return self.getAddon().getSetting(setting)

    def __getSettingString__(self, setting):
        return self.__getSetting__(setting).decode("utf-8")

    def __getSettingBool__(self, setting):
        return self.__getSetting__(setting) == "true"

    def __getSettingList__(self, setting):
        return list(self.__getSetting__(setting))

    def __getSettingInt__(self, setting):
        try:
            return int(float(self.__getSetting__(setting)))
        except ValueError:
            return -1

    def mbid_match_number(self):
        return self.__getSettingInt__("mbid_match_number")

    def use_musicbrainz(self):
        return self.__getSettingBool__("use_musicbrainz")

    def musicbrainz_server(self):
        return self.__getSettingString__("musicbrainz_server")

    def mb_delay(self):
        return self.__getSettingInt__("mb_delay")

    def illegal_characters(self):
        return self.__getSettingList__("illegal_characters")

    def replace_character(self):
        return self.__getSetting__("replace_character")

    def enable_replace_illegal(self):
        return self.__getSettingBool__("enable_replace_illegal")

    def change_period_atend(self):
        return self.__getSettingBool__("change_period_atend")

    def update_musicbrainz(self):
        return self.__getSettingBool__("update_musicbrainz")

    def check_mbid(self):
        return self.__getSettingBool__("check_mbid")

    def enable_all_artists(self):
        return self.__getSettingBool__("enable_all_artists")

    def notify_in_background(self):
        return self.__getSettingBool__("notify_in_background")

    def enablecustom(self):
        return self.__getSettingBool__("enablecustom")

    def backup_during_update(self):
        return self.__getSettingBool__("backup_during_update")

    def enable_missing(self):
        return self.__getSettingBool__("enable_missing")

    def enable_fanart_limit(self):
        return self.__getSettingBool__("enable_fanart_limit")

    def fanart_limit(self):
        return self.__getSettingInt__("fanart_limit")

    def color_recognized(self):
        return self.__getSettingInt__("recognized")

    def color_unrecognized(self):
        return self.__getSettingInt__("unrecognized")

    def color_remote(self):
        return self.__getSettingInt__("remote")

    def color_local(self):
        return self.__getSettingInt__("local")

    def color_remotelocal(self):
        return self.__getSettingInt__("remotelocal")

    def color_unmatched(self):
        return self.__getSettingInt__("unmatched")

    def color_localcdart(self):
        return self.__getSettingInt__("localcdart")


class Constants:
    def __init__(self):
        pass

    @staticmethod
    def script_id():
        return "script.cdartmanager"

    @staticmethod
    def useragent_base():
        return "https://github.com/stefansielaff/script.cdartmanager"

    @staticmethod
    def db_version():
        return "3.0.3"

    @staticmethod
    def db_version_old():
        return "2.7.8"

    @staticmethod
    def db_version_ancient():
        return "1.5.3"

    @staticmethod
    def fanarttv_api_key():
        return "65169f993d552483391ca10c1ae7fb03"

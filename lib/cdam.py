import xbmc
import xbmcaddon


class Settings:

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

    def getAddonInfo(self, info):
        return self.getAddon().getAddonInfo(info)

    def getLocalizedString(self, string):
        return self.getAddon().getLocalizedString(string)

    def getName(self):
        return self.getAddonInfo('name')

    def getId(self):
        return self.getAddonInfo('id')

    def getAuthor(self):
        return self.getAddonInfo('author')

    def getVersion(self):
        return self.getAddonInfo('version')

    def getPath(self):
        return self.getAddonInfo('path')

    def getIcon(self):
        return self.getAddonInfo('icon')

    def getFanart(self):
        return self.getAddonInfo('fanart')

    def getProfile(self):
        return self.getAddonInfo('profile')

    # settings

    def getSetting(self, setting):
        return self.getAddon().getSetting(setting)

    def getSettingString(self, setting):
        return self.getAddon().getSetting(setting).decode("utf-8")

    def getSettingBool(self, setting):
        return self.getSetting(setting) == "true"

    def getSettingInt(self, setting):
        try:
            return int(self.getSetting(setting))
        except ValueError:
            return -1

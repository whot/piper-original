#!/usr/bin/python3
# vim: set expandtab shiftwidth=4 tabstop=4

from gi.repository import GLib
from gi.repository import Gio

class Ratbag(object):
    """
    Represents a libratbag instance over dbus.
    """
    def __init__(self):
        self._dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._dbus_proxy = Gio.DBusProxy.new_sync(self._dbus,
                                                  Gio.DBusProxyFlags.NONE,
                                                  None,
                                                  'org.freedesktop.ratbag1',
                                                  '/org/freedesktop/ratbag1',
                                                  'org.freedesktop.ratbag1.Manager',
                                                 None)
        self._devices = []
        result = self._dbus_proxy.get_cached_property("Devices")
        if result != None:
            self._devices = [RatbagDevice(objpath) for objpath in result.unpack() or None]

    @property
    def devices(self):
        return self._devices

class RatbagDevice(object):
    """
    Represents a libratbag device
    """
    def __init__(self, object_path):
        self._dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._dbus_proxy = Gio.DBusProxy.new_sync(self._dbus,
                                                  Gio.DBusProxyFlags.NONE,
                                                  None,
                                                  'org.freedesktop.ratbag1',
                                                  object_path,
                                                  'org.freedesktop.ratbag1.Device',
                                                  None)
        self._devnode = self._dbus_proxy.get_cached_property("Id").unpack()
        self._description = self._dbus_proxy.get_cached_property("Description").unpack()
        self._svg = self._dbus_proxy.get_cached_property("Svg").unpack()

        self._profiles = []
        self._active_profile = -1
        result = self._dbus_proxy.get_cached_property("Profiles")
        if result != None:
            self._profiles = [RatbagProfile(objpath) for objpath in result.unpack()]
            self._active_profile = self._dbus_proxy.get_cached_property("ActiveProfile").unpack()

    @property
    def profiles(self):
        return self._profiles

    @property
    def buttons(self):
        return range(1, 14)

    @property
    def description(self):
        return self._description

    @property
    def svg(self):
        return self._svg

    @property
    def devnode(self):
        return self._devnode

    @property
    def active_profile(self):
        if self._active_profile == -1:
            return None
        return self._profiles[self._active_profile]

    def __eq__(self, other):
        return self._objpath == other._objpath

class RatbagProfile(object):
    """
    Represents a ratbag profile
    """
    def __init__(self, object_path):
        self._dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._dbus_proxy = Gio.DBusProxy.new_sync(self._dbus,
                                                  Gio.DBusProxyFlags.NONE,
                                                  None,
                                                  'org.freedesktop.ratbag1',
                                                  object_path,
                                                  'org.freedesktop.ratbag1.Profile',
                                                  None)
        self._objpath = object_path
        self._index = self._dbus_proxy.get_cached_property("Index").unpack()

        self._resolutions = []
        self._active_resolution_idx = -1
        self._default_resolution_idx = -1

        result = self._dbus_proxy.get_cached_property("Resolutions")
        if result != None:
            self._resolutions = [RatbagResolution(objpath) for objpath in result.unpack()]
            self._active_resolution_idx = self._dbus_proxy.get_cached_property("ActiveResolution").unpack()
            self._default_resolution_idx = self._dbus_proxy.get_cached_property("DefaultResolution").unpack()

    @property
    def index(self):
        return self._index

    @property
    def resolutions(self):
        return self._resolutions

    @property
    def active_resolution(self):
        if self._active_resolution_idx == -1:
            return None
        return self._resolutions[self._active_resolution_idx]

    @property
    def default_resolution(self):
        if self._default_resolution_idx == -1:
            return None
        return self._resolutions[self._default_resolution_idx]

    def __eq__(self, other):
        return self._objpath == other._objpath

class RatbagResolution(object):
    """
    Represents a libratbag resolution
    """
    def __init__(self, object_path):
        self._dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._dbus_proxy = Gio.DBusProxy.new_sync(self._dbus,
                                                  Gio.DBusProxyFlags.NONE,
                                                  None,
                                                  'org.freedesktop.ratbag1',
                                                  object_path,
                                                  'org.freedesktop.ratbag1.Resolution',
                                                  None)
        self._index = self._dbus_proxy.get_cached_property("Index").unpack()
        self._xres = self._dbus_proxy.get_cached_property("XResolution").unpack()
        self._yres = self._dbus_proxy.get_cached_property("YResolution").unpack()
        self._rate = self._dbus_proxy.get_cached_property("ReportRate").unpack()

    @property
    def resolution(self):
        """Returns the tuple (xres, yres) with each resolution in DPI"""
        return (self._xres, self._yres)

    @property
    def report_rate(self):
        return self._rate

    def __eq__(self, other):
        return self._objpath == other._objpath

def print_all_devices(ratbag):
    for d in ratbag.devices:
        print("Device on {}: {}".format(d.devnode, d.description))
        for i, p in enumerate(d.profiles):
            print(" Profile {}:".format(i))
            for j, r in enumerate(p.resolutions):
                print("    Resolution {}: {}x{}dpi at {}Hz".format(j,
                    r.resolution[0], r.resolution[1], r.report_rate))


def main():
    r = Ratbag()
    print_all_devices(r)

if __name__ == '__main__':
    main()

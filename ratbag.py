#!/usr/bin/python3
# vim: set expandtab shiftwidth=4 tabstop=4

from gi.repository import GLib
from gi.repository import Gio

class RatbagDBusUnavailable(BaseException):
    pass

class RatbagDBus(object):
    def __init__(self, interface, object_path):
        self._dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._proxy = Gio.DBusProxy.new_sync(self._dbus,
                                             Gio.DBusProxyFlags.NONE,
                                             None,
                                             'org.freedesktop.ratbag1',
                                             object_path,
                                             'org.freedesktop.ratbag1.{}'.format(interface),
                                             None)
        if self._proxy.get_name_owner() == None:
            raise RatbagDBusUnavailable()

    def property(self, property):
        p = self._proxy.get_cached_property(property)
        if p != None:
            return p.unpack()
        return p

    def call(self, method, type, *value):
        val = GLib.Variant("({})".format(type), value )
        self._proxy.call_sync(method, val, Gio.DBusCallFlags.NO_AUTO_START, 500, None)

class Ratbag(object):
    """
    Represents a libratbag instance over dbus.
    """
    def __init__(self):
        self._dbus = RatbagDBus("Manager", '/org/freedesktop/ratbag1')
        self._devices = []
        result = self._dbus.property("Devices")
        if result != None:
            self._devices = [RatbagDevice(objpath) for objpath in result]

    @property
    def devices(self):
        return self._devices

class RatbagDevice(object):
    """
    Represents a libratbag device
    """
    def __init__(self, object_path):
        self._dbus = RatbagDBus("Device", object_path)
        self._devnode = self._dbus.property("Id")
        self._description = self._dbus.property("Description")
        self._svg = self._dbus.property("Svg")

        self._profiles = []
        self._active_profile = -1
        result = self._dbus.property("Profiles")
        if result != None:
            self._profiles = [RatbagProfile(objpath) for objpath in result]
            self._active_profile = self._dbus.property("ActiveProfile")

        self._caps = { "CapSwitchableResolution" : False,
                       "CapSwitchableProfile" : False,
                       "CapButtonKeys" : False,
                       "CapButtonMacros" : False,
                       "CapDefaultProfile" : False,
                       }
        for k in self._caps.keys():
            self._caps[k] = self._dbus.property(k)

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

    @property
    def has_cap_switchable_resolution(self):
        return self._caps["CapSwitchableResolution"]

    @property
    def has_cap_switchable_profile(self):
        return self._caps["CapSwitchableProfile"]

    @property
    def has_cap_button_keys(self):
        return self._caps["CapButtonKeys"]

    @property
    def has_cap_button_macros(self):
        return self._caps["CapButtonMacros"]

    @property
    def has_cap_default_macros(self):
        return self._caps["CapDefaultProfile"]

    def __eq__(self, other):
        return other and self._objpath == other._objpath

class RatbagProfile(object):
    """
    Represents a ratbag profile
    """
    def __init__(self, object_path):
        self._dbus = RatbagDBus("Profile", object_path)
        self._objpath = object_path
        self._index = self._dbus.property("Index")

        self._resolutions = []
        self._active_resolution_idx = -1
        self._default_resolution_idx = -1

        result = self._dbus.property("Resolutions")
        if result != None:
            self._resolutions = [RatbagResolution(objpath) for objpath in result]
            self._active_resolution_idx = self._dbus.property("ActiveResolution")
            self._default_resolution_idx = self._dbus.property("DefaultResolution")

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
        self._dbus = RatbagDBus("Resolution", object_path)
        self._index = self._dbus.property("Index")
        self._xres = self._dbus.property("XResolution")
        self._yres = self._dbus.property("YResolution")
        self._rate = self._dbus.property("ReportRate")

        self._caps = { "CapIndividualReportRate" : False,
                       "CapSeparateXYResolution" : False,
                       }
        for k in self._caps.keys():
            self._caps[k] = self._dbus.property(k)

    @property
    def resolution(self):
        """Returns the tuple (xres, yres) with each resolution in DPI"""
        return (self._xres, self._yres)

    @resolution.setter
    def resolution(self, res):
        return self._dbus.call("SetResolution", "uu", *res)

    @property
    def report_rate(self):
        return self._rate

    @report_rate.setter
    def report_rate(self, rate):
        return self._dbus.call("SetReportRate", "u", rate)

    @property
    def has_cap_individual_report_rate(self):
        return self._caps["CapIndividualReportRate"]

    @property
    def has_cap_separate_xy_resolution(self):
        return self._caps["CapSeparateXYResolution"]

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

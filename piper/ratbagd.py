# vim: set expandtab shiftwidth=4 tabstop=4:
#
# Copyright 2016 Red Hat, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from gi.repository import Gio, GLib, GObject


class RatbagdDBusUnavailable(BaseException):
    """Signals DBus is unavailable or the ratbagd daemon is not available."""
    pass


class _RatbagdDBus(GObject.GObject):
    def __init__(self, interface, object_path):
        GObject.GObject.__init__(self)

        self._dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        if self._dbus is None:
            raise RatbagdDBusUnavailable()

        try:
            self._proxy = Gio.DBusProxy.new_sync(self._dbus,
                                                 Gio.DBusProxyFlags.NONE,
                                                 None,
                                                 "org.freedesktop.ratbag1",
                                                 object_path,
                                                 "org.freedesktop.ratbag1.{}".format(interface),
                                                 None)
        except GLib.GError:
            raise RatbagdDBusUnavailable()

        if self._proxy.get_name_owner() is None:
            raise RatbagdDBusUnavailable()

    def dbus_property(self, property):
        p = self._proxy.get_cached_property(property)
        if p is not None:
            return p.unpack()
        return p

    def dbus_call(self, method, type, *value):
        val = GLib.Variant("({})".format(type), value)
        res = self._proxy.call_sync(method, val,
                                    Gio.DBusCallFlags.NO_AUTO_START, 500, None)
        if res is not None:
            return res.unpack()
        return res


class Ratbagd(_RatbagdDBus):
    """The ratbagd top-level object. Provides a list of devices available
    through ratbagd; actual interaction with the devices is via the
    RatbagdDevice, RatbagdProfile, RatbagdResolution and RatbagdButton objects.

    Throws RatbagdDBusUnavailable when the DBus service is not available.
    """

    __gsignals__ = {
        "device-added":
            (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [str]),
        "device-removed":
            (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [str]),
    }

    def __init__(self):
        _RatbagdDBus.__init__(self, "Manager", "/org/freedesktop/ratbag1")
        self._proxy.connect("g-signal", self._on_g_signal)
        self._devices = []
        result = self.dbus_property("Devices")
        if result is not None:
            self._devices = [RatbagdDevice(objpath) for objpath in result]

    def _on_g_signal(self, proxy, sender, signal, params):
        params = params.unpack()
        if signal == "DeviceNew":
            self.emit("device-added", params[0])
        elif signal == "DeviceRemoved":
            self.emit("device-removed", params[0])

    @GObject.Property
    def devices(self):
        """A list of RatbagdDevice objects supported by ratbagd."""
        return self._devices


class RatbagdDevice(_RatbagdDBus):
    """Represents a ratbagd device."""

    CAP_NONE = 0
    CAP_QUERY_CONFIGURATION = 1
    CAP_RESOLUTION = 100
    CAP_SWITCHABLE_RESOLUTION = 101
    CAP_PROFILE = 200
    CAP_SWITCHABLE_PROFILE = 201
    CAP_DISABLE_PROFILE = 202
    CAP_DEFAULT_PROFILE = 203
    CAP_BUTTON = 300
    CAP_BUTTON_KEY = 301
    CAP_BUTTON_MACROS = 302
    CAP_LED = 400

    def __init__(self, object_path):
        _RatbagdDBus.__init__(self, "Device", object_path)
        self._objpath = object_path
        self._devnode = self.dbus_property("Id")
        self._caps = self.dbus_property("Capabilities")
        self._name = self.dbus_property("Name")
        self._svg = self.dbus_property("Svg")
        self._svg_path = self.dbus_property("SvgPath")

        self._profiles = []
        self._active_profile = -1
        result = self.dbus_property("Profiles")
        if result is not None:
            self._profiles = [RatbagdProfile(objpath) for objpath in result]
            self._active_profile = self.dbus_property("ActiveProfile")

    @GObject.Property
    def id(self):
        """The unique identifier of this device."""
        return self._devnode

    @GObject.Property
    def capabilities(self):
        """The capabilities of this device as an array. Capabilities not
        present on the device are not in the list. Thus use e.g.

        if RatbagdDevice.CAP_SWITCHABLE_RESOLUTION is in device.capabilities:
            do something
        """
        return self._caps

    @GObject.Property
    def name(self):
        """The device name, usually provided by the kernel."""
        return self._name

    @GObject.Property
    def svg(self):
        """The SVG file name. This function returns the file name only, not the
        absolute path to the file."""
        return self._svg

    @GObject.Property
    def svg_path(self):
        """The full, absolute path to the SVG."""
        return self._svg_path

    @GObject.Property
    def profiles(self):
        """A list of RatbagdProfile objects provided by this device."""
        return self._profiles

    @GObject.Property
    def active_profile(self):
        """The currently active profile. This function returns a RatbagdProfile
        or None if no active profile was found."""
        if self._active_profile == -1:
            return None
        return self._profiles[self._active_profile]

    def get_profile_by_index(self, index):
        """Returns the profile found at the given index, or None if no profile
        was found.

        @param index The index to find the profile at, as int
        """
        return self.dbus_call("GetProfileByIndex", "u", index)

    def __eq__(self, other):
        return other and self._objpath == other._objpath


class RatbagdProfile(_RatbagdDBus):
    """Represents a ratbagd profile."""

    __gsignals__ = {
        "active-profile-changed":
            (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [int]),
    }

    def __init__(self, object_path):
        _RatbagdDBus.__init__(self, "Profile", object_path)
        self._proxy.connect("g-signal", self._on_g_signal)
        self._objpath = object_path
        self._index = self.dbus_property("Index")
        self._resolutions = []
        self._buttons = []
        self._leds = []
        self._active_resolution_index = -1
        self._default_resolution_index = -1

        result = self.dbus_property("Resolutions")
        if result is not None:
            self._resolutions = [RatbagdResolution(objpath) for objpath in result]
            self._active_resolution_index = self.dbus_property("ActiveResolution")
            self._default_resolution_index = self.dbus_property("DefaultResolution")

        result = self.dbus_property("Buttons")
        if result is not None:
            self._buttons = [RatbagdButton(objpath) for objpath in result]

        result = self.dbus_property("Leds")
        if result is not None:
            self._leds = [RatbagdLed(objpath) for objpath in result]

    def _on_g_signal(self, proxy, sender, signal, params):
        params = params.unpack()
        if signal == "ActiveProfileChanged":
            self.emit("active-profile-changed", params[0])

    @GObject.Property
    def index(self):
        """The index of this profile."""
        return self._index

    @GObject.Property
    def resolutions(self):
        """A list of RatbagdResolution objects with this profile's resolutions.
        """
        return self._resolutions

    @GObject.Property
    def buttons(self):
        """A list of RatbagdButton objects with this profile's button mappings.
        Note that the list of buttons differs between profiles but the number
        of buttons is identical across profiles."""
        return self._buttons

    @GObject.Property
    def leds(self):
        """A list of RatbagdLed objects with this profile's leds."""
        return self._leds

    @GObject.Property
    def active_resolution(self):
        """The currently active resolution. This function returns a
        RatbagdResolution object or None."""
        if self._active_resolution_index == -1:
            return None
        return self._resolutions[self._active_resolution_index]

    @GObject.Property
    def default_resolution(self):
        """The default resolution. This function returns a RatbagdResolution
        object or None."""
        if self._default_resolution_index == -1:
            return None
        return self._resolutions[self._default_resolution_index]

    def set_active(self):
        """Set this profile to be the active profile."""
        return self.dbus_call("SetActive", "")

    def get_resolution_by_index(self, index):
        """Returns the resolution found at the given index. This function
        returns a RatbagdResolution or None if no resolution was found."""
        return self.dbus_call("GetResolutionByIndex", "u", index)

    def __eq__(self, other):
        return self._objpath == other._objpath


class RatbagdResolution(_RatbagdDBus):
    """Represents a ratbagd resolution."""

    CAP_INDIVIDUAL_REPORT_RATE = 1
    CAP_SEPARATE_XY_RESOLUTION = 2

    __gsignals__ = {
        "active-resolution-changed":
            (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [int]),
        "default-resolution-changed":
            (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [int]),
    }

    def __init__(self, object_path):
        _RatbagdDBus.__init__(self, "Resolution", object_path)
        self._proxy.connect("g-signal", self._on_g_signal)
        self._objpath = object_path
        self._index = self.dbus_property("Index")
        self._caps = self.dbus_property("Capabilities")
        self._xres = self.dbus_property("XResolution")
        self._yres = self.dbus_property("YResolution")
        self._rate = self.dbus_property("ReportRate")
        self._max_res = self.dbus_property("MaxRes")
        self._min_res = self.dbus_property("MinRes")

    def _on_g_signal(self, proxy, sender, signal, params):
        params = params.unpack()
        if signal == "ActiveResolutionChanged":
            self.emit("active-resolution-changed", params[0])
        elif signal == "DefaultResolutionChanged":
            self.emit("default-resolution-changed", params[0])

    @GObject.Property
    def index(self):
        """The index of this resolution."""
        return self._index

    @GObject.Property
    def capabilities(self):
        """The capabilities of this resolution as a list. Capabilities not
        present on the resolution are not in the list. Thus use e.g.

        if RatbagdResolution.CAP_SEPARATE_XY_RESOLUTION is in resolution.capabilities:
            do something
        """
        return self._caps

    @GObject.Property
    def resolution(self):
        """The tuple (xres, yres) with each resolution in DPI."""
        return (self._xres, self._yres)

    @resolution.setter
    def resolution(self, res):
        """Set the x- and y-resolution using the given (xres, yres) tuple.

        @param res The new resolution, as (int, int)
        """
        return self.dbus_call("SetResolution", "uu", *res)

    @GObject.Property
    def report_rate(self):
        """The report rate in Hz."""
        return self._rate

    @GObject.Property
    def max_res(self):
        """The maximum possible resolution."""
        return self._max_res

    @GObject.Property
    def min_res(self):
        """The minimum possible resolution."""
        return self._min_res

    @report_rate.setter
    def report_rate(self, rate):
        """Set the report rate in Hz.

        @param rate The new report rate, as int
        """
        return self.dbus_call("SetReportRate", "u", rate)

    def set_default(self):
        """Set this resolution to be the default."""
        return self.dbus_call("SetDefault", "")

    def __eq__(self, other):
        return self._objpath == other._objpath


class RatbagdButton(_RatbagdDBus):
    """Represents a ratbagd button."""

    def __init__(self, object_path):
        _RatbagdDBus.__init__(self, "Button", object_path)
        self._objpath = object_path
        self._index = self.dbus_property("Index")
        self._type = self.dbus_property("Type")
        self._button = self.dbus_property("ButtonMapping")
        self._special = self.dbus_property("SpecialMapping")
        self._key = self.dbus_property("KeyMapping")
        self._action = self.dbus_property("ActionType")
        self._types = self.dbus_property("ActionTypes")

    @GObject.Property
    def index(self):
        """The index of this button."""
        return self._index

    @GObject.Property
    def button_type(self):
        """A string describing this button's type."""
        return self._type

    @GObject.Property
    def button_mapping(self):
        """An integer of the current button mapping, if mapping to a button."""
        return self._button

    @button_mapping.setter
    def button_mapping(self, button):
        """Set the button mapping to the given button.

        @param button The button to map to, as int
        """
        return self.dbus_call("SetButtonMapping", "u", button)

    @GObject.Property
    def special(self):
        """A string of the current special mapping, if mapped to special."""
        return self._special

    @special.setter
    def special(self, special):
        """Set the button mapping to the given special entry.

        @param special The special entry, as str
        """
        return self.dbus_call("SetSpecialMapping", "s", special)

    @GObject.Property
    def key(self):
        """An array of integers, the first being the keycode and the other
        entries, if any, are modifiers (if mapped to key)."""
        return self._key

    @key.setter
    def key(self, key, modifiers):
        """Set the key mapping.

        @param key The keycode, as int
        @param modifiers Modifier keycodes, as [int]
        """
        return self.dbus_call("SetKeyMapping", "au", [key].append(modifiers))

    @GObject.Property
    def action_type(self):
        """A string describing the action type of the button. One of "none",
        "button", "key", "special", "macro" or "unknown". This decides which
        *Mapping property has a value.
        """
        return self._action

    @GObject.Property
    def action_types(self):
        """An array of possible values for ActionType."""
        return self._types

    def disable(self):
        """Disables this button."""
        return self.dbus_call("Disable", "")


class RatbagdLed(_RatbagdDBus):
    """Represents a ratbagd led."""

    LED_MODE_OFF = 0
    LED_MODE_ON = 1
    LED_MODE_CYCLE = 2
    LED_MODE_BREATHING = 3

    def __init__(self, object_path):
        _RatbagdDBus.__init__(self, "Led", object_path)
        self._objpath = object_path
        self._index = self.dbus_property("Index")
        self._mode = self.dbus_property("Mode")
        self._type = self.dbus_property("Type")
        self._color = self.dbus_property("Color")
        self._effect_rate = self.dbus_property("EffectRate")
        self._brightness = self.dbus_property("Brightness")

    @GObject.Property
    def index(self):
        """The index of this led."""
        return self._index

    @GObject.Property
    def mode(self):
        """This led's mode, one of LED_MODE_OFF, LED_MODE_ON, LED_MODE_CYCLE and
        LED_MODE_BREATHING."""
        return self._mode

    @mode.setter
    def mode(self, mode):
        """Set the led's mode to the given mode.

        @param mode The new mode, as one of LED_MODE_OFF, LED_MODE_ON,
                                  LED_MODE_CYCLE and LED_MODE_BREATHING.
        """
        return self.dbus_call("SetMode", "u", mode)

    @GObject.Property
    def type(self):
        """A string describing this led's type."""
        return self._type

    @GObject.Property
    def color(self):
        """An integer triple of the current LED color."""
        return self._color

    @color.setter
    def color(self, color):
        """Set the led color to the given color.

        @param color An RGB color, as an integer triplet.
        """
        return self.dbus_call("SetColor", "(uuu)", color)

    @GObject.Property
    def effect_rate(self):
        """The LED's effect rate in Hz, values range from 100 to 20000."""
        return self._effect_rate

    @effect_rate.setter
    def effect_rate(self, effect_rate):
        """Set the effect rate in Hz. Allowed values range from 100 to 20000.

        @param effect_rate The new effect rate, as int
        """
        return self.dbus_call("SetEffectRate", "u", effect_rate)

    @GObject.Property
    def brightness(self):
        """The LED's brightness, values range from 0 to 255."""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        """Set the brightness. Allowed values range from 0 to 255.

        @param brightness The new brightness, as int
        """
        return self.dbus_call("SetBrightness", "i", brightness)

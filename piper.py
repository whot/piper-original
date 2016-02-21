#!/usr/bin/python3
# vim: set expandtab shiftwidth=4 tabstop=4

from ratbag import *

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Piper(Gtk.Window):

    def _show_error(self, message):
        box = self._builder.get_object("piper-error-box")

        btn = self._builder.get_object("piper-error-button")
        btn.connect("clicked", Gtk.main_quit)

        error = self._builder.get_object("piper-error-body-label")
        error.set_text(message)

        self.add(box)

    def __init__(self):
        Gtk.Window.__init__(self, title="Piper")
        main_window = Gtk.Builder()
        main_window.add_from_file("piper.ui")
        self._builder = main_window;

        self._ratbag = self._init_ratbag()
        if self._ratbag == None:
            self._show_error("Can't connect to ratbagd on DBus. That's quite unfortunate.")
            return
        if len(self._ratbag.devices) == 0:
            self._show_error("Could not find any devices. Do you have anything vaguely mouse-looking plugged in?")
            return

        if len(self._ratbag.devices) > 1:
            print("Ooops, can't deal with more than one device. My bad.")
            for d in self._ratbag.devices[1:]:
                print("Ignoring device {}".format(d.description))

        self._ratbag_device = self._ratbag.devices[0]


        self._profile_buttons = []
        self._current_profile = self._ratbag_device.active_profile

        grid = main_window.get_object("piper-grid")
        self._init_header(self._ratbag_device)
        self.add(grid)

        # load the right image
        # FIXME: libratbag images need to be scaled into the available
        # space, disable for now
        # svg = self._ratbag_device.svg
        # svg = "/opt/libratbag/share/libratbag/{}".format(svg)
        # img = main_window.get_object("piper-image-device")
        # img.set_from_file(svg)

        # init the current profile's data
        p = self._current_profile
        self._init_report_rate(main_window, p)
        self._init_resolution(main_window, p)
        self._init_buttons(main_window, self._ratbag_device)

    def _init_ratbag(self):
        try:
            return Ratbag()
        except RatbagDBusUnavailable:
            return None

    def  _init_header(self, device):
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "{}".format(device.description)
        self.set_titlebar(hb)

        # apply/reset buttons
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="edit-undo-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_button_reset_clicked)
        box.add(button)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-save-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.on_button_save_clicked)
        box.add(button)

        hb.pack_end(box)

        # Profile buttons
        profiles = device.profiles
        if len(profiles) > 1:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            Gtk.StyleContext.add_class(box.get_style_context(), "linked")

            for i, p in enumerate(profiles):
                button = Gtk.ToggleButton("Profile {}".format(i))
                button.connect("toggled", self.on_button_profile_toggled, p)
                button.set_active(p == device.active_profile)
                box.add(button)
                self._profile_buttons.append(button)
            hb.pack_start(box)

        hb.show_all()

    def _init_resolution(self, builder, profile):
        res = profile.resolutions
        nres = len(profile.resolutions)

        for i in range(0, 5):
            sb = builder.get_object("piper-xres-spinbutton{}".format(i + 1))
            if i >= nres:
                continue

            xres = res[i].resolution[0]
            sb.set_value(xres)
            sb.connect("value-changed", self.on_resolutions_changed)

        nres_spin = builder.get_object("piper-nresolutions-spin")
        nres_spin.connect("value-changed", self.on_nresolutions_changed, builder)
        nres_spin.set_value(nres)

    def _init_report_rate(self, builder, profile):
        # Note: we simplify here, the UI only allows one report rate and it
        # will be applied to all resolutions
        rate = profile.active_resolution.report_rate
        r500 = builder.get_object("piper-report-rate-500")
        r1000 = builder.get_object("piper-report-rate-1000")
        r500.connect("toggled", self.on_resolution_rate_changed, 500)
        r1000.connect("toggled", self.on_resolution_rate_changed, 1000)
        if rate == 500:
            r500.set_active(True)
        if rate == 1000:
            r1000.set_active(True)
        if rate != 500 and rate != 1000:
            print("Ooops, rate is {} and I don't know how to deal with that.".format(rate))
            r500.set_sensitive(False)
            r1000.set_sensitive(False)

        c = builder.get_object("piper-resolutions-listbox").get_style_context()
        c.set_junction_sides(Gtk.JunctionSides.BOTTOM)
        c.set_junction_sides(Gtk.JunctionSides.TOP)

    def _init_buttons(self, builder, device):
        lb = builder.get_object("piper-buttons-listbox")
        lb.remove(builder.get_object("piper-button-listboxrow"))

        for i, b in enumerate(device.buttons):
            lbr = self._init_button_row(i)
            lb.add(lbr)

        lb.show_all()

    def _init_button_row(self, button):
        # FIXME: can't I duplicate this from builder?
        lbr = Gtk.ListBoxRow()
        lbr.height_request = 80
        lbr.width_request = 100
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        l1 = Gtk.Label("Button {}".format(button))
        l1.set_margin_left(12)
        l1.set_margin_top(8)
        l1.set_margin_bottom(8)
        l1.height_request = 32
        box.add(l1)

        l2 = Gtk.Label()
        l2.set_markup("<b>Button 1 click</b>")
        l2.set_hexpand(True)
        box.add(l2)

        btn = Gtk.Button("...")
        btn.connect("clicked", self.on_button_click, button)
        box.add(btn)
        lbr.add(box)
        return lbr

    def on_resolution_rate_changed(self, widget, new_rate):
        if not widget.get_active():
            return

        print("FIXME: set the report rate for all resolutions to {}".format(new_rate))

    def on_nresolutions_changed(self, widget, builder):
        nres = widget.get_value_as_int()
        for i in range(0, 5):
            sb = builder.get_object("piper-xres-spinbutton{}".format(i + 1))
            sb.set_sensitive(nres > i)

        self._adjust_sensitivity_ranges()

    def on_resolutions_changed(self, widget):
        self._adjust_sensitivity_ranges()

    def on_button_save_clicked(self, widget):
        print("FIXME: I should save this to the device now")

    def on_button_reset_clicked(self, widget):
        print("FIXME: I should reload from device now")

    def on_button_profile_toggled(self, widget, profile):
        print("FIXME: I should switch profiles now")
        if not widget.get_active():
            return

        for b in self._profile_buttons:
            if b != widget:
                b.set_active(False)

    def on_button_click(self, widget, button):
        print("FIXME: I should pop down the button config window now")

    def _adjust_sensitivity_ranges(self):
        """
        Align the five sensitivity ranges so that the right-most one can
        go to 1200, the left-most one to 200. In between they're bound by
        the previous/next one so the order is always ascending
        """
        builder = self._builder
        widget = builder.get_object("piper-nresolutions-spin")
        nres = widget.get_value_as_int()

        min, max = 200, 12000

        while nres > 0:
            a1 = builder.get_object("piper-xres-adjustment{}".format(nres))
            a1.set_upper(max)
            max = int(a1.get_value())

            a2 = builder.get_object("piper-xres-adjustment{}".format(nres - 1))
            if a2:
                a1.set_lower(a2.get_value())
            nres -= 1


class PiperImage(Gtk.EventBox):
    def __init__(self, path):
        Gtk.EventBox.__init__(self)
        self._image = Gtk.Image()
        self._image.set_from_file(path)
        self.add(self._image)
        self.connect("button-press-event", self.on_button_clicked)

    def on_button_clicked(self, widget, event):
        print(event.x)

def main():
    win = Piper()
    win.connect("delete-event", Gtk.main_quit)
    win.show()
    Gtk.main()

if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

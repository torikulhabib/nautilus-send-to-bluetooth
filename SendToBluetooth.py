#!/usr/bin/env python3

import os, subprocess

from gi import require_version
require_version('Gtk', '4.0')
require_version('Nautilus', '4.0')

from urllib.parse import unquote, urlparse

import gi
from gi.repository import GObject, Nautilus

import dbus

def uri_to_path(file):
    p = urlparse(file.get_activation_uri())
    return os.path.abspath(os.path.join(p.netloc, unquote(p.path)))


class SendToBluetoothExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        GObject.Object.__init__(self)

    def send_action(self, menu, files, properties):
        paths = []
        for file in files:
            paths.append(uri_to_path(file))
        subprocess.Popen(["/usr/bin/bluetooth-sendto"] + ['--device='+ properties] + paths)

    def get_file_items(self, *args):
        files = args[-1]
        if len(files) < 1:
            return

        for file in files:
            if file.is_directory():
                return

        listdevice = []
        bus = dbus.SystemBus()

        manager = dbus.Interface(bus.get_object("org.bluez", "/"),
					        "org.freedesktop.DBus.ObjectManager")

        objects = manager.GetManagedObjects()

        all_devices = (str(path) for path, interfaces in objects.items() if
					        "org.bluez.Device1" in interfaces.keys())

        for path, interfaces in objects.items():
	        if "org.bluez.Adapter1" not in interfaces.keys():
		        continue

	        device_list = [d for d in all_devices if d.startswith(path + "/")]
	        for dev_path in device_list:
		        btdevice = []
		        devp = objects[dev_path]["org.bluez.Device1"]
		        btdevice.append (devp["Alias"])
		        btdevice.append (devp["Address"])
		        listdevice.append (btdevice)

        if len (listdevice) < 1:
            return
        submenu = Nautilus.Menu()
        item = Nautilus.MenuItem(
            name="SendToBluetooth::MenuItem",
            label="Send to bluetooth device",
            tip="Send to bluetooth device",
        )
        item.set_submenu(submenu)

        for btmenu in listdevice:
            item_two = Nautilus.MenuItem(
                name=btmenu[1] + "::MenuItem",
                label=btmenu[0],
                tip=btmenu[1],
            )
            submenu.append_item(item_two)
            item_two.connect("activate", self.send_action, files, btmenu[1])
        return [item]

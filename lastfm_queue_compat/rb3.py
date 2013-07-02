# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# IMPORTANT - WHILST THIS MODULE IS USED BY SEVERAL OTHER PLUGINS
# THE MASTER AND MOST UP-TO-DATE IS FOUND IN THE COVERART BROWSER
# PLUGIN - https://github.com/fossfreedom/coverart-browser
# PLEASE SUBMIT CHANGES BACK TO HELP EXPAND THIS API
#
# Copyright (C) 2012 - fossfreedom
# Copyright (C) 2012 - Agustin Carrasco
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from gi.repository import Gio, GLib, GObject
import lxml.etree as ET


class ApplicationShell(object):
    ACTION_PREFIX = 'app'
    POPUP_MAPPING = {
        'QueuePlaylistViewPopup': 'queue-popup',
        'BrowserSourceViewPopup': 'browser-popup',
        'PlaylistViewPopup': 'playlist-popup',
        'PodcastViewPopup': 'podcast-episode-popup',
    }

    def __init__(self, shell, group_name):
        super(ApplicationShell, self).__init__()

        self.app = shell.props.application
        self._items = {}

    def _get_action_name(self, action):
        return '{0}.{1}'.format(action.name, self.ACTION_PREFIX)

    def lookup_action(self, action_name):
        return self.app.lookup_action(action_name)

    def add_action(self, action):
        self.app.add_action(action)

    def add_action_with_accel(self, action, accel):
        self.add_action(action)
        self.app.add_accelerator(accel, self._get_action_name(action), None)

    def remove_action(self, action_name):
        self.app.remove_action(action_name)

    def add_app_menuitems(self, ui_string, menu='tools'):
        root = ET.fromstring(ui_string)

        for elem in root.findall('.//menuitem'):
            action_name = elem.attrib['action']

            action = self.lookup_action(action_name)

            item = Gio.MenuItem()
            item.set_detailed_action(self._get_action_name(action))
            item.set_label(action.label)

            index = '{0}_{1}'.format(menu, action.get_name())
            self.app.add_plugin_menu_item(menu, index, item)

            self._items[index] = menu

    def add_browser_menuitems(self, ui_string):
        root = ET.fromstring(ui_string)

        for elem in root.findall('./popup'):
            popup_name = elem.attrib['name']

            menuelem = elem.find('.//menuitem')
            action_name = menuelem.attrib['action']

            action = self.lookup_action(action_name)

            item = Gio.MenuItem()
            item.set_detailed_action(self._get_action_name(action))
            item.set_label(action.label)

            try:
                plugin_type = self.POPUP_MAPPING[popup_name]
            except KeyError:
                raise ValueError(
                    'Unknown plugin popup: {0}'.format(popup_name))

            index = '{0}_{1}'.format(plugin_type, action.get_name())
            self.app.add_plugin_menu_item(plugin_type, index, item)
            self._items[index] = plugin_type

    def cleanup(self):
        for item in self._items:
            self.app.remove_plugin_menu_item(self._items[item], item)


class Action(Gio.SimpleAction):
    label = GObject.property(type=str, default='')

    def __init__(self, name, label, *args):
        super(ToggleAction, self).__init__(
            name=name,
            label=label,
            parameter_type=None,
            state=GLib.Variant.new_boolean(False))

    def get_sensitive(self):
        return self.action.get_enabled()


class ToggleAction(Gio.SimpleAction):
    def __init__(self, name, label, *args):
        super(ToggleAction, self).__init__(name, label, *args)

        self.connect('activate', self._toggle)

    def _change_state(self, value):
        self.set_state(GLib.Variant.new_boolean(value))

    def _toggle(self, *args):
        self._change_state(not self.get_active())

    def set_active(self, value):
        self._change_state(value)

    def get_active(self):
        return self.get_state().get_boolean()

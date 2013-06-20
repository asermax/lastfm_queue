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

from gi.repository import Gtk, Gio, GLib, GObject
import rb
import lxml.etree as ET

from lastfm_queue_compat import BaseMenu


class Menu(BaseMenu):
    '''
    Menu object used to create window popup menus
    '''

    def insert_menu_item(self, menubar, section_name, position, action):
        '''
        add a new menu item to the popup
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param section_name: `str` is the name of the section to add the item to (RB2.99+)
        :param position: `int` position to add to GtkMenu (ignored for RB2.99+)
        :param action: `Action`  to associate with the menu item
        '''
        label = action.label
        app = self.shell.props.application
        item = Gio.MenuItem()
        action.associate_menuitem(item)
        item.set_label(label)

        if not section_name in self._rbmenu_items:
            self._rbmenu_items[section_name] = []

        self._rbmenu_items[section_name].append(label)
        app.add_plugin_menu_item(section_name, label, item)

        return item

    def insert_separator(self, menubar, at_position):
        '''
        add a separator to the popup (only required for RB2.98 and earlier)
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param position: `int` position to add to GtkMenu (ignored for RB2.99+)
        '''
        pass

    def remove_menu_items(self, menubar, section_name):
        '''
        utility function to remove all menuitems associated with the menu section
        :param menubar: `str` is the name of the GtkMenu containing the menu items (ignored for RB2.99+)
        :param section_name: `str` is the name of the section containing the menu items (for RB2.99+ only)
        '''
        if not section_name in self._rbmenu_items:
            return

        app = self.shell.props.application

        for menu_item in self._rbmenu_items[section_name]:
            app.remove_plugin_menu_item(section_name, menu_item)

        if self._rbmenu_items[section_name]:
            del self._rbmenu_items[section_name][:]

    def load_from_file(self, rb2_ui_filename, rb3_ui_filename):
        '''
        utility function to load the menu structure
        :param rb2_ui_filename: `str` RB2.98 and below UI file
        :param rb3_ui_filename: `str` RB2.99 and higher UI file
        '''
        ui_filename = rb3_ui_filename

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            rb.find_plugin_file(self.plugin, ui_filename))

    def connect_signals(self, signals):
        def _menu_connect(action_name, func):
            action = Gio.SimpleAction(name=action_name)
            action.connect('activate', func)
            action.set_enabled(True)
            self.shell.props.window.add_action(action)

        for key, value in signals.items():
            _menu_connect(key, value)

    def get_gtkmenu(self, source, popup_name):
        '''
        utility function to obtain the GtkMenu from the menu UI file
        :param popup_name: `str` is the name menu-id in the UI file
        '''
        item = self.builder.get_object(popup_name)

        app = self.shell.props.application
        app.link_shared_menus(item)
        popup_menu = Gtk.Menu.new_from_model(item)
        popup_menu.attach_to_widget(source, None)

        return popup_menu

    def get_menu_object(self, menu_name_or_link):
        '''
        utility function returns the GtkMenuItem/Gio.MenuItem
        :param menu_name_or_link: `str` to search for in the UI file
        '''
        item = self.builder.get_object(menu_name_or_link)

        if item:
            popup_menu = item
        else:
            app = self.shell.props.application
            popup_menu = app.get_plugin_menu(menu_name_or_link)

        return popup_menu

    def set_sensitive(self, menu_or_action_item, enable):
        '''
        utility function to enable/disable a menu-item
        :param menu_or_action_item: `GtkMenuItem` or `Gio.SimpleAction`
           that is to be enabled/disabled
        :param enable: `bool` value to enable/disable
        '''
        item = self.shell.props.window.lookup_action(menu_or_action_item)
        item.set_enabled(enable)


class ApplicationShell(object):
    def __init__(self, shell, group_name):
        super(ApplicationShell, self).__init__()

        self.app = shell.props.application
        self._items = {}

    def lookup_action(self, action_name):
        return self.app.lookup_action(action_name)

    def add_action(self, action):
        self.app.add_action(action)

    def remove_action(self, action_name):
        self.app.remove_action(action_name)

    def add_app_menuitems(self, ui_string, menu='tools'):
        root = ET.fromstring(ui_string)

        for elem in root.findall('.//menuitem'):
            action_name = elem.attrib['action']

            action = self.lookup_action(action_name)

            item = Gio.MenuItem()
            item.set_detailed_action('app.' + action.get_name())
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
            item.set_detailed_action('app.' + action.get_name())
            item.set_label(action.label)

            if popup_name == 'QueuePlaylistViewPopup':
                plugin_type = 'queue-popup'
            elif popup_name == 'BrowserSourceViewPopup':
                plugin_type = 'browser-popup'
            elif popup_name == 'PlaylistViewPopup':
                plugin_type = 'playlist-popup'
            elif popup_name == 'PodcastViewPopup':
                plugin_type = 'podcast-episode-popup'
            else:
                print 'unknown type %s' % plugin_type

            index = '{0}_{1}'.format(plugin_type, action.get_name())
            self.app.add_plugin_menu_item(plugin_type, index, item)
            self._items[index] = plugin_type

    def cleanup(self):
        for item in self._items:
            Gio.Application.get_default().remove_plugin_menu_item(
                self._items[item], item)


class ToggleAction(Gio.SimpleAction):
    label = GObject.property(type=str, default='')

    def __init__(self, name, label, *args):
        super(ToggleAction, self).__init__(
            name=name,
            label=label,
            parameter_type=None,
            state=GLib.Variant.new_boolean(False))

        self.connect('activate', self._toggle)

    def _change_state(self, value):
        self.set_state(GLib.Variant.new_boolean(value))

    def _toggle(self, *args):
        self._change_state(not self.get_active())

    def get_sensitive(self):
        return self.action.get_enabled()

    def set_active(self, value):
        self._change_state(value)

    def get_active(self):
        return self.get_state().get_boolean()

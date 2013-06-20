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

from gi.repository import Gtk
import rb

from lastfm_queue_compat import BaseMenu


class Menu(BaseMenu):

    def insert_menu_item(self, menubar, section_name, position, action):
        '''
        add a new menu item to the popup
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param section_name: `str` is the name of the section to add the
            item to (RB2.99+)
        :param position: `int` position to add to GtkMenu (ignored for RB2.99+)
        :param action: `Action`  to associate with the menu item
        '''
        label = action.label
        item = Gtk.MenuItem(label=label)
        action.associate_menuitem(item)
        self._rbmenu_items[label] = item
        bar = self.get_menu_object(menubar)

        if position == -1:
            bar.append(item)
        else:
            bar.insert(item, position)

        bar.show_all()
        uim = self.shell.props.ui_manager
        uim.ensure_update()

        return item

    def insert_separator(self, menubar, at_position):
        '''
        add a separator to the popup (only required for RB2.98 and earlier)
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param position: `int` position to add to GtkMenu (ignored for RB2.99+)
        '''
        menu_item = Gtk.SeparatorMenuItem().new()
        menu_item.set_visible(True)
        self._rbmenu_items['separator' + str(self._unique_num)] = menu_item
        self._unique_num = self._unique_num + 1
        bar = self.get_menu_object(menubar)
        bar.insert(menu_item, at_position)
        bar.show_all()
        uim = self.shell.props.ui_manager
        uim.ensure_update()

    def remove_menu_items(self, menubar, section_name):
        '''
        utility function to remove all menuitems associated with the menu section
        :param menubar: `str` is the name of the GtkMenu containing the menu items (ignored for RB2.99+)
        :param section_name: `str` is the name of the section containing the menu items (for RB2.99+ only)
        '''
        if not self._rbmenu_items:
            return

        uim = self.shell.props.ui_manager
        bar = self.get_menu_object(menubar)

        for menu_item in self._rbmenu_items:
            bar.remove(self._rbmenu_items[menu_item])

        bar.show_all()
        uim.ensure_update()

    def load_from_file(self, rb2_ui_filename, rb3_ui_filename):
        '''
        utility function to load the menu structure
        :param rb2_ui_filename: `str` RB2.98 and below UI file
        :param rb3_ui_filename: `str` RB2.99 and higher UI file
        '''
        ui_filename = rb2_ui_filename

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            rb.find_plugin_file(self.plugin, ui_filename))

    def connect_signals(self, signals):
        '''
        connect all signal handlers with their menuitem counterparts
        :param signals: `dict` key is the name of the menuitem
             and value is the function callback when the menu is activated
        '''
        def _menu_connect(menu_item_name, func):
            menu_item = self.builder.get_object(menu_item_name)
            menu_item.connect('activate', func)

        for key, value in signals.items():
            _menu_connect(key, value)

    def get_gtkmenu(self, source, popup_name):
        '''
        utility function to obtain the GtkMenu from the menu UI file
        :param popup_name: `str` is the name menu-id in the UI file
        '''
        item = self.builder.get_object(popup_name)

        return item

    def get_menu_object(self, menu_name_or_link):
        '''
        utility function returns the GtkMenuItem/Gio.MenuItem
        :param menu_name_or_link: `str` to search for in the UI file
        '''
        item = self.builder.get_object(menu_name_or_link)

        return item

    def set_sensitive(self, menu_or_action_item, enable):
        '''
        utility function to enable/disable a menu-item
        :param menu_or_action_item: `GtkMenuItem` or `Gio.SimpleAction`
           that is to be enabled/disabled
        :param enable: `bool` value to enable/disable
        '''
        item = self.builder.get_object(menu_or_action_item)
        item.set_sensitive(enable)


class ApplicationShell(object):
    def __init__(self, shell, group_name):
        super(ApplicationShell, self).__init__()

        self.uim = shell.props.ui_manager

        if not group_name:
            raise ValueError('You must define a group_name')

        self.action_group = Gtk.ActionGroup(group_name)
        self.uim.insert_action_group(self.action_group)

        self._uids = []

    def lookup_action(self, action_name):
        return self.action_group.get_action(action_name)

    def add_action(self, action):
        self.action_group.add_action(action)

    def add_action_with_accel(self, action, accel):
        self.action_group.add_action(action, accel)

    def remove_action(self, action_name):
        self.action_group.remove(self.lookup_action(action_name))

    def _add_menuitems(self, ui_string):
        self._uids.append(self.uim.add_ui_from_string(ui_string))
        self.uim.ensure_update()

    def add_app_menuitems(self, ui_string):
        self._add_menuitems(ui_string)
        
    def add_browser_menuitems(self, ui_string):
        self._add_menuitems(ui_string)

    def cleanup(self):
        for uid in self._uids:
            self.uim.remove_ui(uid)
        self.uim.ensure_update()


Action = Gtk.Action
ToggleAction = Gtk.ToggleAction

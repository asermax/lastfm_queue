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
from gi.repository import Gio
from gi.repository import GLib
import rb
import lxml.etree as ET

from lastfm_queue_compat import BaseAction, BaseActionGroup,\
    BaseApplicationShell, BaseMenu


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


class ActionGroup(BaseActionGroup):
    '''
    container for all Actions used to associate with menu items
    '''

    def __init__(self, shell, group_name):
        '''
        constructor
        :param shell: `RBShell`
        :param group_name: `str` unique name for the object to create
        '''
        super(ActionGroup, self).__init__(shell, group_name)
        self.actiongroup = Gio.SimpleActionGroup()

    def _build_action(self, callback, action_name, label, accel, action_type,
                      action_state):
        '''
        Creates an Action and adds it to the ActionGroup

        :param func: function callback used when user activates the action
        :param action_name: `str` unique name to associate with an action
        :param args: dict of arguments - this is passed to the function callback

        Notes:
        key value of "label" is the visual menu label to display
        key value of "action_type" is the RB2.99 Gio.Action type ("win" or "app")
           by default it assumes all actions are "win" type
        key value of "action_state" determines what action state to create
        '''
        app = Gio.Application.get_default()

        if action_state == ActionGroup.TOGGLE:
            action = Gio.SimpleAction.new_stateful(
                action_name, None, GLib.Variant.new_boolean(False))
        else:
            action = Gio.SimpleAction.new(action_name, None)

        if action_type == 'app':
            app.add_action(action)
        else:
            self.shell.props.window.add_action(action)
            self.actiongroup.add_action(action)

        if accel:
            app.add_accelerator(accel, action_type + "." + action_name, None)

        return Action(self.shell, action, label, accel)


class ApplicationShell(BaseApplicationShell):
    '''
    Unique class that mirrors RB.Application & RB.Shell menu functionality
    '''

    def __init__(self, shell):
        super(ApplicationShell, self).__init__(shell)
        self._uids = {}

    def lookup_action(self, action_group_name, action_name, action_type='app'):
        '''
        looks up (finds) an action created by another plugin.  If found returns
        an Action or None if no matching Action.

        :param action_group_name: `str` is the Gtk.ActionGroup name (ignored for RB2.99+)
        :param action_name: `str` unique name for the action to look for
        :param action_type: `str` RB2.99+ action type ("win" or "app")
        '''

        if action_type == 'app':
            action = self.shell.props.application.lookup_action(action_name)
        else:
            action = self.shell.props.window.lookup_action(action_name)

        if action:
            return Action(self.shell, action)
        else:
            return None

    def add_app_menuitems(self, ui_string, group_name, menu='tools'):
        '''
        utility function to add application menu items.

        For RB2.99 all application menu items are added to the "tools" section of the
        application menu. All Actions are assumed to be of action_type "app".

        For RB2.98 or less, it is added however the UI_MANAGER string
        is defined.

        :param ui_string: `str` is the Gtk UI definition.  There is not an
        equivalent UI definition in RB2.99 but we can parse out menu items since
        this string is in XML format

        :param group_name: `str` unique name of the ActionGroup to add menu items to
        :param menu: `str` RB2.99 menu section to add to - nominally either
          'tools' or 'view'
        '''
        root = ET.fromstring(ui_string)
        for elem in root.findall(".//menuitem"):
            action_name = elem.attrib['action']

            group = self._action_groups[group_name]
            act = group.get_action(action_name)

            item = Gio.MenuItem()
            item.set_detailed_action('app.' + action_name)
            item.set_label(act.label)
            item.set_attribute_value("accel", GLib.Variant("s", act.accel))
            app = Gio.Application.get_default()
            index = menu + action_name
            app.add_plugin_menu_item(menu,
                                     index, item)
            self._uids[index] = menu

    def add_browser_menuitems(self, ui_string, group_name):
        '''
        utility function to add popup menu items to existing browser popups

        For RB2.99 all menu items are are assumed to be of action_type "win".

        For RB2.98 or less, it is added however the UI_MANAGER string
        is defined.

        :param ui_string: `str` is the Gtk UI definition.  There is not an
        equivalent UI definition in RB2.99 but we can parse out menu items since
        this string is in XML format

        :param group_name: `str` unique name of the ActionGroup to add menu items to
        '''
        root = ET.fromstring(ui_string)
        for elem in root.findall("./popup"):
            popup_name = elem.attrib['name']

            menuelem = elem.find('.//menuitem')
            action_name = menuelem.attrib['action']

            group = self._action_groups[group_name]
            act = group.get_action(action_name)

            item = Gio.MenuItem()
            item.set_detailed_action('win.' + action_name)
            item.set_label(act.label)
            app = Gio.Application.get_default()

            if popup_name == 'QueuePlaylistViewPopup':
                plugin_type = 'queue-popup'
            elif popup_name == 'BrowserSourceViewPopup':
                plugin_type = 'browser-popup'
            elif popup_name == 'PlaylistViewPopup':
                plugin_type = 'playlist-popup'
            elif popup_name == 'PodcastViewPopup':
                plugin_type = 'podcast-episode-popup'
            else:
                print "unknown type %s" % plugin_type

            index = plugin_type + action_name
            app.add_plugin_menu_item(plugin_type, index, item)
            self._uids[index] = plugin_type

    def cleanup(self):
        '''
        utility remove any menuitems created.
        '''
        for uid in self._uids:
            Gio.Application.get_default().remove_plugin_menu_item(
                self._uids[uid], uid)


class Action(BaseAction):
    '''
    class that wraps around either a Gio.Action or a Gtk.Action
    '''

    def _connect(self, address, func, args):
        self.action.connect(address, func, args)

    def get_sensitive(self):
        '''
        get the sensitivity (enabled/disabled) state of the Action

        returns boolean
        '''
        return self.action.get_enabled()

    def activate(self):
        '''
        invokes the activate signal for the action
        '''
        self.action.activate(None)

    def set_active(self, value):
        '''
        activate or deactivate a stateful action signal

        :param value: `boolean` state value
        '''
        self.action.change_state(GLib.Variant.new_boolean(value))

    def get_active(self):
        '''
        get the state of the action

        returns `boolean` state value
        '''
        return self.action.get_state().get_boolean()

    def associate_menuitem(self, menuitem):
        '''
        links a menu with the action

        '''
        menuitem.set_detailed_action('win.' + self.action.get_name())

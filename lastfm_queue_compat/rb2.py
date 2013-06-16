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

from lastfm_queue_compat import BaseAction, BaseActionGroup,\
    BaseApplicationShell, BaseMenu


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

        self.actiongroup = Gtk.ActionGroup(group_name)
        uim = self.shell.props.ui_manager
        uim.insert_action_group(self.actiongroup)

    def _build_action(self, callback, action_name, label, accel, action_type,
                      action_state):
        '''
        Creates an Action and adds it to the ActionGroup

        :param func: function callback used when user activates the action
        :param action_name: `str` unique name to associate with an action
        :param args: dict of arguments - this is passed to the function callback

        Notes:
        key value of "label" is the visual menu label to display
        key value of "action_type" is the RB2.99 Gio.Action type
            ("win" or "app") by default it assumes all actions are "win" type
        key value of "action_state" determines what action state to create
        '''
        if action_state == ActionGroup.TOGGLE:
            action = Gtk.ToggleAction(
                label=label,
                name=action_name,
                tooltip='',
                stock_id=Gtk.STOCK_CLEAR)
        else:
            action = Gtk.Action(
                label=label,
                name=action_name,
                tooltip='',
                stock_id=Gtk.STOCK_CLEAR)

        if accel:
            self.actiongroup.add_action_with_accel(action, accel)
        else:
            self.actiongroup.add_action(action)

        return Action(self.shell, action, label, accel)


class ApplicationShell(BaseApplicationShell):
    '''
    Unique class that mirrors RB.Application & RB.Shell menu functionality
    '''
    """ Implementation of the singleton interface """

    def __init__(self, shell):
        super(ApplicationShell, self).__init__(shell)
        self._uids = []

    def lookup_action(self, action_group_name, action_name, action_type='app'):
        '''
        looks up (finds) an action created by another plugin.  If found returns
        an Action or None if no matching Action.

        :param action_group_name: `str` is the Gtk.ActionGroup name (ignored for RB2.99+)
        :param action_name: `str` unique name for the action to look for
        :param action_type: `str` RB2.99+ action type ("win" or "app")
        '''

        uim = self.shell.props.ui_manager
        ui_actiongroups = uim.get_action_groups()

        actiongroup = None
        for actiongroup in ui_actiongroups:
            if actiongroup.get_name() == action_group_name:
                break

        action = None
        if actiongroup:
            action = actiongroup.get_action(action_name)

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
        uim = self.shell.props.ui_manager
        self._uids.append(uim.add_ui_from_string(ui_string))
        uim.ensure_update()

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
        uim = self.shell.props.ui_manager
        self._uids.append(uim.add_ui_from_string(ui_string))
        uim.ensure_update()

    def cleanup(self):
        '''
        utility remove any menuitems created.
        '''
        uim = self.shell.props.ui_manager
        for uid in self._uids:
            uim.remove_ui(uid)
        uim.ensure_update()


class Action(BaseAction):
    '''
    class that wraps around either a Gio.Action or a Gtk.Action
    '''

    def _connect(self, address, func, args):
        self.action.connect(address, func, None, args)

    def get_sensitive(self):
        '''
        get the sensitivity (enabled/disabled) state of the Action

        returns boolean
        '''
        return self.action.get_sensitive()

    def activate(self):
        '''
        invokes the activate signal for the action
        '''
        self.action.activate()

    def set_active(self, value):
        '''
        activate or deactivate a stateful action signal

        :param value: `boolean` state value
        '''
        self.action.set_active(value)

    def get_active(self):
        '''
        get the state of the action

        returns `boolean` state value
        '''
        return self.action.get_active()

    def associate_menuitem(self, menuitem):
        '''
        links a menu with the action

        '''
        menuitem.set_related_action(self.action)

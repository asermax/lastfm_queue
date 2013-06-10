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
from urlparse import urlparse as rb2urlparse
import rb
import lxml.etree as ET
import httplib
import urllib

from lastfm_queue_compat import BaseAction, BaseActionGroup,\
    BaseApplicationShell, BaseMenu


def responses():
    return httplib.responses


def unicodestr(param, charset):
    return unicode(param, charset)


def unicodeencode(param, charset):
    return unicode(param).encode(charset)


def urlparse(uri):
    return rb2urlparse(uri)


def url2pathname(url):
    return urllib.url2pathname(url)


def urlopen(filename):
    return urllib.urlopen(filename)


def pathname2url(filename):
    return urllib.pathname2url(filename)


def unquote(uri):
    return urllib.unquote(uri)


def quote(uri, safe=None):
    return urllib.quote(uri, safe=safe)


def quote_plus(uri):
    return urllib.quote_plus(uri)


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
        self.ui_filename = rb2_ui_filename

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

    # action_state
    STANDARD = 0
    TOGGLE = 1

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


    def add_action(self, callback, action_name, label=None, accel=None,
            action_type=None, action_state=None):
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
        if not label:
            label = action_name

        if not action_state:
            action_state = ActionGroup.STANDARD

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

        act = Action(self.shell, action, label, accel)
        act.connect('activate', callback)

        self._actions[action_name] = act

        return act


class ApplicationShell(BaseApplicationShell):
    '''
    Unique class that mirrors RB.Application & RB.Shell menu functionality
    '''
    # storage for the instance reference
    __instance = None

    class __impl:
        """ Implementation of the singleton interface """
        def __init__(self, shell):
            self.shell = shell

            if is_rb3(self.shell):
                self._uids = {}
            else:
                self._uids = []

            self._action_groups = {}

        def insert_action_group(self, action_group):
            '''
            Adds an ActionGroup to the ApplicationShell

            :param action_group: `ActionGroup` to add
            '''
            self._action_groups[action_group.name] = action_group

        def lookup_action(self, action_group_name, action_name, action_type='app'):
            '''
            looks up (finds) an action created by another plugin.  If found returns
            an Action or None if no matching Action.

            :param action_group_name: `str` is the Gtk.ActionGroup name (ignored for RB2.99+)
            :param action_name: `str` unique name for the action to look for
            :param action_type: `str` RB2.99+ action type ("win" or "app")
            '''

            if is_rb3(self.shell):
                if action_type == "app":
                    action = self.shell.props.application.lookup_action(action_name)
                else:
                    action = self.shell.props.window.lookup_action(action_name)
            else:
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
            if is_rb3(self.shell):
                root = ET.fromstring(ui_string)
                for elem in root.findall(".//menuitem"):
                    action_name = elem.attrib['action']
                    item_name = elem.attrib['name']

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
            else:
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
            if is_rb3(self.shell):
                root = ET.fromstring(ui_string)
                for elem in root.findall("./popup"):
                    popup_name = elem.attrib['name']

                    menuelem = elem.find('.//menuitem')
                    action_name = menuelem.attrib['action']
                    item_name = menuelem.attrib['name']

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
            else:
                uim = self.shell.props.ui_manager
                self._uids.append(uim.add_ui_from_string(ui_string))
                uim.ensure_update()

        def cleanup(self):
            '''
            utility remove any menuitems created.
            '''
            if is_rb3(self.shell):
                for uid in self._uids:

                    Gio.Application.get_default().remove_plugin_menu_item(self._uids[uid],
                                                                          uid)
            else:
                uim = self.shell.props.ui_manager
                for uid in self._uids:
                    uim.remove_ui(uid)
                uim.ensure_update()

    def __init__(self, shell):
        """ Create singleton instance """
        # Check whether we already have an instance
        if ApplicationShell.__instance is None:
            # Create and remember instance
            ApplicationShell.__instance = ApplicationShell.__impl(shell)

        # Store instance reference as the only member in the handle
        self.__dict__['_ApplicationShell__instance'] = ApplicationShell.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


class Action(object):
    '''
    class that wraps around either a Gio.Action or a Gtk.Action
    '''

    def __init__(self, shell, action):
        '''
        constructor.

        :param shell: `RBShell`
        :param action: `Gio.Action` or `Gtk.Action`
        '''
        self.shell = shell
        self.action = action

        self._label = ''
        self._accel = ''
        self._current_state = False
        self._do_update_state = True

    def connect(self, address, func, args):
        self._connect_func = func
        self._connect_args = args

        if address == 'activate':
            func = self._activate

        if is_rb3(self.shell):
            self.action.connect(address, func, args)
        else:
            self.action.connect(address, func, None, args)

    def _activate(self, action, *args):
        if self._do_update_state:
            self._current_state = not self._current_state

        self._connect_func(action, None, self._connect_args)

    @property
    def label(self):
        '''
        get the menu label associated with the Action

        for RB2.99+ actions dont have menu labels so this is managed
        manually
        '''
        if not is_rb3(self.shell):
            return self.action.get_label()
        else:
            return self._label

    @label.setter
    def label(self, new_label):
        if not is_rb3(self.shell):
            self.action.set_label(new_label)

        self._label = new_label

    @property
    def accel(self):
        '''
        get the accelerator associated with the Action
        '''
        return self._accel

    @accel.setter
    def accel(self, new_accelerator):
        if new_accelerator:
            self._accel = new_accelerator
        else:
            self._accel = ''

    def get_sensitive(self):
        '''
        get the sensitivity (enabled/disabled) state of the Action

        returns boolean
        '''
        if is_rb3(self.shell):
            return self.action.get_enabled()
        else:
            return self.action.get_sensitive()

    def activate(self):
        '''
        invokes the activate signal for the action
        '''
        if is_rb3(self.shell):
            self.action.activate(None)
        else:
            self.action.activate()

    def set_active(self, value):
        '''
        activate or deactivate a stateful action signal
        For consistency with earlier RB versions, this will fire the
        activate signal for the action

        :param value: `boolean` state value
        '''

        if is_rb3(self.shell):
            self.action.change_state(GLib.Variant('b', value))
            self._current_state = value
            self._do_update_state = False
            self.activate()
            self._do_update_state = True
        else:
            self.action.set_active(value)

    def get_active(self):
        '''
        get the state of the action

        returns `boolean` state value
        '''
        if is_rb3(self.shell):
            returnval = self._current_state
        else:
            returnval = self.action.get_active()

        return returnval

    def associate_menuitem(self, menuitem):
        '''
        links a menu with the action

        '''
        if is_rb3(self.shell):
            menuitem.set_detailed_action('win.' + self.action.get_name())
        else:
            menuitem.set_related_action(self.action)

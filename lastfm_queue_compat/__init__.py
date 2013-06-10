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

import sys


class BaseMenu(object):
    '''
    Menu object used to create window popup menus
    '''

    def __init__(self, plugin, shell):
        '''
        Initializes the menu.
        '''
        self.plugin = plugin
        self.shell = shell
        self._unique_num = 0

        self._rbmenu_items = {}

    def add_menu_item(self, menubar, section_name, action):
        '''
        add a new menu item to the popup
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param section_name: `str` is the name of the section to add the item to (RB2.99+)
        :param action: `Action`  to associate with the menu item
        '''
        return self.insert_menu_item(menubar, section_name, -1, action)


class BaseActionGroup(object):
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
        self.group_name = group_name
        self.shell = shell

        self._actions = {}

    @property
    def name(self):
        return self.group_name

    def remove_actions(self):
        '''
        utility function to remove all actions associated with the ActionGroup
        '''
        for action in self.actiongroup.list_actions():
            self.actiongroup.remove_action(action)

    def get_action(self, action_name):
        '''
        utility function to obtain the Action from the ActionGroup

        :param action_name: `str` is the Action unique name
        '''
        return self._actions[action_name]

    def add_action_with_accel(self, func, action_name, accel, **args):
        '''
        Creates an Action with an accelerator and adds it to the ActionGroup

        :param func: function callback used when user activates the action
        :param action_name: `str` unique name to associate with an action
        :param accel: `str` accelerator
        :param args: dict of arguments - this is passed to the function callback

        Notes:
        see notes for add_action
        '''
        args['accel'] = accel
        return self.add_action(func, action_name, **args)


class BaseApplicationShell(object):
    '''
    Unique class that mirrors RB.Application & RB.Shell menu functionality
    '''

    def __init__(self, shell):
        self.shell = shell

        self._action_groups = {}

    def insert_action_group(self, action_group):
        '''
        Adds an ActionGroup to the ApplicationShell

        :param action_group: `ActionGroup` to add
        '''
        self._action_groups[action_group.name] = action_group


class BaseAction(object):
    '''
    class that wraps around either a Gio.Action or a Gtk.Action
    '''

    def __init__(self, shell, action, label='', accel=''):
        '''
        constructor.

        :param shell: `RBShell`
        :param action: `Gio.Action` or `Gtk.Action`
        '''
        self.shell = shell
        self.action = action

        self.label = label
        self.accel = accel


def init(shell):
    if hasattr(shell.props.window, 'add_action'):
        import lastfm_queue_compat.rb3 as compat_module
    else:
        import lastfm_queue_compat.rb2 as compat_module

    sys.modules[__name__] = compat_module

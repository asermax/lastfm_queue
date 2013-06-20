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

import inspect


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


def init(shell):
    if hasattr(shell.props.window, 'add_action'):
        import lastfm_queue_compat.rb3 as compat_module
    else:
        import lastfm_queue_compat.rb2 as compat_module

    for name, obj in inspect.getmembers(compat_module):
        globals()[name] = obj

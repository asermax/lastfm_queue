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

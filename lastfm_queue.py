# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
#
# Copyright (C) 2012 - Agustin Carrasco
# Copyright (C) 2007 - Alexandre Rosenfeld
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

from gi.repository import GObject, Gio, Peas, RB, GLib, Gtk
import lastfm_queue_compat as compat
import rb
import random

try:
    from urllib import parse
except:
    import urllib as parse
from xml.dom import minidom

import gettext
gettext.install('rhythmbox', RB.locale_dir(), unicode=True)

ui_str = \
    """<ui>
    <menubar name="MenuBar">
        <menu name="ControlMenu" action="Control">
            <menuitem name="LastFM Queue" action="LastFMQueueAction"/>
        </menu>
    </menubar>
    </ui>"""

PATH = 'org.gnome.rhythmbox.plugins.lastfm_queue'
ACTIVE_KEY = 'active'


class LastFmQueuePlugin (GObject.Object, Peas.Activatable):
    __gtype_name = 'LastFMQueue'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)

        # init the pluggins settings backend
        self.settings = Gio.Settings.new(PATH)

        # load saved state
        self.active = self.settings[ACTIVE_KEY]

    def do_activate(self):
        self.shell = self.object

        # init the compat module
        compat.init(self.shell)

        action = compat.ToggleAction(
            'LastFMQueueAction',
            _('LastFM Queue'),
            _("Toggle Last.fm recommendations"),
            Gtk.STOCK_EXECUTE)

        action.set_active(self.active)
        action.connect('activate', self.toggle_dynamic)

        self._appshell = compat.ApplicationShell(
            self.shell, 'LastFMQueueActionGroup')
        self._appshell.add_action(action)
        self._appshell.add_app_menuitems(ui_str)

        self.db = self.shell.get_property('db')

        sp = self.shell.props.shell_player
        self.pec_id = sp.connect(
            'playing-song-changed', self.playing_entry_changed)
        self.sc_id = sp.connect('playing-source-changed', self.source_changed)
        self.past_entries = []
        self.current_entry = None
        self.orig_source = None
        self.similar_data = None

    def do_deactivate(self):
        self._appshell.cleanup()

        self.db = None
        sp = self.shell.props.shell_player
        self.shell = None
        sp.disconnect(self.pec_id)
        sp.disconnect(self.sc_id)

    def toggle_dynamic(self, action, *args):
        self.active = action.get_active()

        self.settings[ACTIVE_KEY] = self.active
        self.past_entries = []

    def source_changed(self, sp, source):
        if not source:
            return
        # We don't want to forget our past songs if we change to the Queue
        if source.get_name() == 'RBPlayQueueSource':
            return
        # Or if we get back to our original source
        if source.get_name() == self.orig_source:
            return

        self.orig_source = source.get_name()

        # Forget past entries when changing sources
        self.past_entries = []

    def playing_changed(self, sp, playing):
        if self.active:
            self.set_entry(sp.get_playing_entry())

    def playing_entry_changed(self, sp, entry):
        if self.active:
            self.set_entry(entry)

    def set_entry(self, entry):
        if entry == self.current_entry or not entry:
            return
        self.current_entry = entry
        title = unicode(entry.get_string(RB.RhythmDBPropType.TITLE), 'utf-8')
        artist = unicode(entry.get_string(RB.RhythmDBPropType.ARTIST), 'utf-8')
        try:
            self.past_entries.pop(self.past_entries.index((artist, title)))
        except ValueError:
            pass
        self.past_entries.append((artist, title))
        loader = rb.Loader()
        url = 'http://ws.audioscrobbler.com/2.0/?method=track.getsimilar' \
            '&api_key=4353df7956417de92999306424bc9395' \
            '&artist={0}&track={1}'.format(
                parse.quote(artist.encode('utf-8')),
                parse.quote(title.encode('utf-8')))

        loader.get_url(url, self.load_list)

    def load_list(self, data):
        if not data:
            return
        self.similar_data = data
        dom = minidom.parseString(data)
        tracks = dom.getElementsByTagName('track')
        random.shuffle(tracks)

        for track in tracks:
            names = track.getElementsByTagName('name')
            title = names[0].firstChild.data.encode('utf-8')
            artist = names[1].firstChild.data.encode('utf-8')

            if self.find_track(artist, title):
                break

    def find_track(self, artist, title):
        query_model = RB.RhythmDBQueryModel.new_empty(self.db)
        query = GLib.PtrArray()
        self.db.query_append_params(
            query,
            RB.RhythmDBQueryType.EQUALS,
            RB.RhythmDBPropType.ARTIST,
            artist)
        self.db.query_append_params(
            query,
            RB.RhythmDBQueryType.EQUALS,
            RB.RhythmDBPropType.TITLE,
            title)
        self.db.do_full_query_parsed(query_model, query)

        for row in query_model:
            if self.past_entries.count((artist, title)) > 0:
                continue
            self.shell.get_property('queue_source').add_entry(row[0], -1)
            self.past_entries.append((artist, title))
            if len(self.past_entries) > 200:
                del self.past_entries[0]
            return True
        else:
            return False

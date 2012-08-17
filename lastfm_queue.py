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

import string
import sys
import re
import traceback
from gi.repository import GObject, Gio, Gtk, Peas, RB, GLib

import rb
import urllib
from xml.dom import minidom
from random import *

import gettext
gettext.install('rhythmbox', RB.locale_dir(), unicode=True)

ui_str = """
<ui>
  <toolbar name="ToolBar">
    <placeholder name="ToolBarPluginPlaceholder">
      <toolitem name="DynamicToggle" action="DynamicToggle"/>
    </placeholder>
  </toolbar>
</ui>
"""

PATH = 'org.gnome.rhythmbox.plugins.lastfm_queue'
ACTIVE_KEY = 'active'

class LastFmQueuePlugin (GObject.Object, Peas.Activatable):
	__gtype_name = 'LastFMQueue'
	object = GObject.property(type=GObject.Object)

	def __init__(self):
		GObject.Object.__init__(self)
		self.settings = Gio.Settings.new(PATH)
		self.active = self.settings[ACTIVE_KEY] 
		
	def do_activate(self):
		shell = self.object
		
		
		data = dict()
		manager = shell.props.ui_manager

		data['action_group'] = Gtk.ActionGroup('LastFmDynamicActions')

		action = Gtk.ToggleAction('DynamicToggle', _('_DynamicQ'),
		                    _("Toggle Last.fm recommendations"),
		                    Gtk.STOCK_EXECUTE)
		action.connect('activate', self.toggle_dynamic, shell)
		data['action_group'].add_action(action)
		action.set_active(self.active)

		manager.insert_action_group(data['action_group'], 0)
		data['ui_id'] = manager.add_ui_from_string(ui_str)
		manager.ensure_update()

		shell.set_data('LastFmDynamicPluginInfo', data)

		self.shell = shell
		self.db = shell.get_property('db')
		sp = shell.props.shell_player
		self.pec_id = sp.connect ('playing-song-changed', self.playing_entry_changed)
		self.pc_id = sp.connect ('playing-changed', self.playing_changed)
		self.sc_id = sp.connect ('playing-source-changed', self.source_changed)
		self.past_entries = []
		self.current_entry = None
		self.orig_source = None
		self.similar_data = None
	def do_deactivate(self):
		data = self.shell.get_data('LastFmDynamicPluginInfo')

		manager = self.shell.props.ui_manager
		manager.remove_ui(data['ui_id'])
		manager.remove_action_group(data['action_group'])
		manager.ensure_update()

		self.shell.set_data('LastFmDynamicPluginInfo', None)
		
		self.db = None
		sp = self.shell.props.shell_player
		self.shell = None
		sp.disconnect (self.pec_id)
		sp.disconnect (self.pc_id)
		sp.disconnect (self.sc_id)

	def toggle_dynamic(self, action, shell):
		self.active = action.get_active()
		self.settings[ACTIVE_KEY] = self.active
		self.past_entries = []

	def source_changed(self, sp, source):
		if not source:
			return
		#We don't want to forget our past songs if we change to the Queue
		if source.get_name() == 'RBPlayQueueSource':
			return
		#Or if we get back to our original source
		if source.get_name() == self.orig_source:
			return
		orig_source = source.get_name()
		#Forget past entries when changing sourcesS
		self.past_entries = []

	def playing_changed (self, sp, playing):
		if self.active:
			self.set_entry(sp.get_playing_entry ())

	def playing_entry_changed (self, sp, entry):
		if self.active:
			self.set_entry(entry)

	def set_entry (self, entry):
		if entry == self.current_entry or not entry:
			return
		self.current_entry = entry
		title = unicode( entry.get_string(RB.RhythmDBPropType.TITLE ), 'utf-8' )
		artist = unicode( entry.get_string(RB.RhythmDBPropType.ARTIST ), 'utf-8' )
		try:
			self.past_entries.pop(self.past_entries.index((artist, title)))
		except ValueError:
			pass
		self.past_entries.append((artist, title))
		loader = rb.Loader()
		url = "http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist=%s&track=%s&api_key=4353df7956417de92999306424bc9395" % \
		       	(urllib.quote(artist.encode('utf-8')), urllib.quote(title.encode('utf-8')))		                              
		           
		loader.get_url( url, self.load_list)

	def load_list(self, data):
		if not data:
			return
		self.similar_data = data
		dom = minidom.parseString(data)
		tracks = dom.getElementsByTagName('track')
		shuffle(tracks)
		for track in tracks:
			names = track.getElementsByTagName('name')
			title = names[0].firstChild.data.encode( 'utf-8' )
			artist = names[1].firstChild.data.encode( 'utf-8' )
			
			if self.find_track(artist, title):
				break

	def find_track(self, artist, title):
		query_model = RB.RhythmDBQueryModel.new_empty(self.db)
		query = GLib.PtrArray()
		self.db.query_append_params( query, 
				     RB.RhythmDBQueryType.EQUALS, 
				     RB.RhythmDBPropType.ARTIST, artist )
		self.db.query_append_params( query, 
				      RB.RhythmDBQueryType.EQUALS, 
				      RB.RhythmDBPropType.TITLE, title)		
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

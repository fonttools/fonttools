#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import gtk

import fontTools.ttx

class FontTreeStoreBuilder:

	def __init__(self, treestore):
		self.ts = treestore

	def add_object(self, parent, key, value):
		# Make sure item is decompiled
		try:
			getattr(value, "asdf")
		except AttributeError:
			pass
		if value.__class__ == fontTools.ttLib.getTableModule('glyf').Glyph:
			# Glyph type needs explicit expanding to be useful
			value.expand(self.font['glyf'])

		item = self.ts.append(parent, [key, '%s' % value.__class__.__name__])
		for k,v in sorted(value.__dict__.items()):
			if k[0] == '_':
				continue
			self.add_thing (item, k, v)

	def add_dict(self, parent, key, value):
		item = self.ts.append(parent, [key, '%s of %d items' %
						    (value.__class__.__name__, len(value))])
		for k,v in sorted(value.items()):
			self.add_thing (item, k, v)

	def add_list(self, parent, key, value):
		item = self.ts.append(parent, [key, '%s of %d items' %
						    (value.__class__.__name__, len(value))])
		for k,v in enumerate(value):
			self.add_thing (item, k, v)

	def add_thing(self, parent, key, value):
		if value == self.font:
			return
		if key == 'reader':
			return
		if not isinstance(value, basestring):
			# Sequences
			try:
				len(value)
				iter(value)
				# It's hard to differentiate list-type sequences
				# from dict-type ones.  Try fetching item 0.
				value[0]
				self.add_list(parent, key, value)
				return
			except TypeError:
				pass
			except AttributeError:
				pass
			except KeyError:
				pass
			except IndexError:
				pass
		if hasattr(value, '__dict__'):
			self.add_object(parent, key, value)
			return
		if hasattr(value, 'items'):
			self.add_dict(parent, key, value)
			return

		# Everything else
		item = self.ts.append(parent, [key, value])

	def add_font(self, font):
		self.font = font
		for tag in font.keys():
			self.add_thing (None, tag, font[tag])
		self.font = None

class PyFontView:

    def delete_event(self, widget, event, data=None):
	gtk.main_quit()
	return False

    def __init__(self):

	self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	self.window.set_title("PyFontView")
	self.window.connect("delete_event", self.delete_event)
	self.window.set_size_request(400, 600)

	self.scrolled_window = gtk.ScrolledWindow()
	self.window.add(self.scrolled_window)

	self.treestore = gtk.TreeStore(str, str)
	self.treeview = gtk.TreeView(self.treestore)
	#self.treeview.set_reorderable(True)

	font = fontTools.ttx.TTFont("abc.woff")
	#font = fontTools.ttx.TTFont("IranNastaliq2.ttf")
	builder = FontTreeStoreBuilder(self.treestore)
	builder.add_font (font)

	for i in range(2):

		col = gtk.TreeViewColumn('Column %d' % i)

		self.treeview.append_column(col)

		cell = gtk.CellRendererText()
		col.pack_start(cell, True)

		col.add_attribute(cell, 'text', i)

		self.treeview.set_search_column(i)
		col.set_sort_column_id(i)

	self.scrolled_window.add(self.treeview)
	self.window.show_all()

def main():
    gtk.main()

if __name__ == "__main__":
    viewer = PyFontView()
    main()

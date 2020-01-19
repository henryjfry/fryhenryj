import os, re, csv, sys, time, json, urllib, string, random, shutil, logging, urlparse, datetime, functools, threading, collections
try:
	import cPickle as pickle
except ImportError:
	import pickle
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

VIEW_MODES = {
	'thumbnail': {
		'skin.confluence': 500,
		'skin.aeon.nox': 551,
		'skin.confluence-vertical': 500,
		'skin.jx720': 52,
		'skin.pm3-hd': 53,
		'skin.rapier': 50,
		'skin.simplicity': 500,
		'skin.slik': 53,
		'skin.touched': 500,
		'skin.transparency': 53,
		'skin.xeebo': 55
	}}

class _PersistentDictMixin(object):
	def __init__(self, filename, flag='c', mode=None, file_format='pickle'):
#		xbmc.log(str('def __init__(self, filename, flag=c, mode=None, file_format=pickle):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.lock = threading.RLock()
		self.flag = flag
		self.mode = mode
		self.file_format = file_format
		self.filename = filename
		if flag != 'n' and os.access(filename, os.R_OK):
			fileobj = open(filename, 'rb' if file_format == 'pickle' else 'r')
			with fileobj:
				self.load(fileobj)

	def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
#		xbmc.log(str('def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return ''.join(random.choice(chars) for _ in range(size))

	def sync(self):
#		xbmc.log(str('def sync(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		with self.lock:
			self._sync()
			
	def _sync(self):
#		xbmc.log(str('def _sync(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if self.flag == 'r':
			return
		filename = self.filename
		tempname = filename + '.' + self.id_generator()   + '.tmp'
		fileobj = open(tempname, 'wb' if self.file_format == 'pickle' else 'w')
		try:
			self.dump(fileobj)
		except Exception as e:
			os.remove(tempname)
			raise
		finally:
			fileobj.close()
		shutil.move(tempname, self.filename)
		if self.mode is not None:
			os.chmod(self.filename, self.mode)

	def close(self):
#		xbmc.log(str('def close(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.sync()

	def __enter__(self):
#		xbmc.log(str('def __enter__(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self

	def __exit__(self, *exc_info):
#		xbmc.log(str('def __exit__(self, *exc_info):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.close()

	def dump(self, fileobj):
#		xbmc.log(str('def dump(self, fileobj):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if self.file_format == 'csv':
			csv.writer(fileobj).writerows(self.raw_dict().items())
		elif self.file_format == 'json':
			json.dump(self.raw_dict(), fileobj, separators=(',', ':'))
		elif self.file_format == 'pickle':
			pickle.dump(dict(self.raw_dict()), fileobj, 2)
		else:
			raise NotImplementedError('Unknown format: ' + repr(self.file_format))

	def load(self, fileobj):
#		xbmc.log(str('def load(self, fileobj):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		for loader in (pickle.load, json.load, csv.reader):
			fileobj.seek(0)
			try:
				return self.initial_update(loader(fileobj))
			except Exception as e:
				pass
		raise ValueError('File not in a supported format')

	def raw_dict(self):
#		xbmc.log(str('def raw_dict(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		raise NotImplementedError

class _Storage(collections.MutableMapping, _PersistentDictMixin):
	def __init__(self, filename, file_format='pickle'):
#		xbmc.log(str('def __init__(self, filename, file_format=pickle):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._items = {}
		_PersistentDictMixin.__init__(self, filename, file_format=file_format)

	def __setitem__(self, key, val):
#		xbmc.log(str('def __setitem__(self, key, val):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._items.__setitem__(key, val)

	def __getitem__(self, key):
#		xbmc.log(str('def __getitem__(self, key):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._items.__getitem__(key)

	def __delitem__(self, key):
#		xbmc.log(str('def __delitem__(self, key):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._items.__delitem__(key)

	def __iter__(self):
#		xbmc.log(str('def __iter__(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return iter(self._items)

	def __len__(self):
#		xbmc.log(str('def __len__(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._items.__len__

	def raw_dict(self):
#		xbmc.log(str('def raw_dict(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._items

	initial_update = collections.MutableMapping.update

	def clear(self):
#		xbmc.log(str('def clear(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		super(_Storage, self).clear()
		self.sync()

class TimedStorage(_Storage):
	def __init__(self, filename, file_format='pickle', TTL=None):
#		xbmc.log(str('def __init__(self, filename, file_format=pickle, TTL=None):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.TTL = TTL
		_Storage.__init__(self, filename, file_format=file_format)

	def __setitem__(self, key, val, raw=False):
#		xbmc.log(str('def __setitem__(self, key, val, raw=False):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if raw:
			self._items[key] = val
		else:
			self._items[key] = (val, time.time())

	def __getitem__(self, key):
#		xbmc.log(str('def __getitem__(self, key):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		val, timestamp = self._items[key]
		if self.TTL and (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(timestamp) > self.TTL):
			del self._items[key]
			return self._items[key][0]
		return val

	def initial_update(self, mapping):
#		xbmc.log(str('def initial_update(self, mapping):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		for key, val in mapping.items():
			_, timestamp = val
			if not self.TTL or (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(timestamp) < self.TTL):
				self.__setitem__(key, val, raw=True)

class ListItem(object):
	def __init__(self, label=None, label2=None, icon=None, thumbnail=None, path=None):
#		xbmc.log(str('def __init__(self, label=None, label2=None, icon=None, thumbnail=None, path=None)')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._listitem = xbmcgui.ListItem(label=label, label2=label2, path=path)
		self._art = {'icon': icon, 'thumb': thumbnail}
		self._icon = icon
		self._path = path
		self._thumbnail = thumbnail
		self._context_menu_items = []
		self._played = False
		self._playable = False
		self.is_folder = True

	def __repr__(self):
#		xbmc.log(str('def __repr__(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return ("<ListItem '%s'>" % self.label).encode('utf-8')

	def __str__(self):
#		xbmc.log(str('def __str__(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return ('%s (%s)' % (self.label, self.path)).encode('utf-8')

	def get_context_menu_items(self):
#		xbmc.log(str('def get_context_menu_items(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._context_menu_items

	def add_context_menu_items(self, items, replace_items=False):
#		xbmc.log(str('def add_context_menu_items(self, items, replace_items=False):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		for label, action in items:
			assert isinstance(label, basestring)
			assert isinstance(action, basestring)
		if replace_items:
			self._context_menu_items = []
		self._context_menu_items.extend(items)
		self._listitem.addContextMenuItems(items, replace_items)

	def as_tuple(self):
#		xbmc.log(str('def as_tuple(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self.path, self._listitem, self.is_folder

	def as_xbmc_listitem(self):
#		xbmc.log(str('def as_xbmc_listitem(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem

	def set_info(self, info_type, info_labels):
#		xbmc.log(str('def set_info(self, info_type, info_labels):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.setInfo(info_type, info_labels)

	def get_property(self, key):
#		xbmc.log(str('def get_property(self, key):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.getProperty(key)

	def set_property(self, key, value):
#		xbmc.log(str('def set_property(self, key, value):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.setProperty(key, value)

	def add_stream_info(self, stream_type, stream_values):
#		xbmc.log(str('def add_stream_info(self, stream_type, stream_values):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.addStreamInfo(stream_type, stream_values)

	@property
	def selected(self):
#		xbmc.log(str('def selected(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.isSelected()

	@selected.setter
	def selected(self, value):
#		xbmc.log(str('def selected(self, value):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._listitem.select(value)

	@property
	def label(self):
#		xbmc.log(str('def label(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.getLabel()

	@label.setter
	def label(self, value):
#		xbmc.log(str('def label(self, value):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._listitem.setLabel(value)

	@property
	def label2(self):
#		xbmc.log(str('def label2(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._listitem.getLabel2()

	@label2.setter
	def label2(self, value):
#		xbmc.log(str('def label2(self, value):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._listitem.setLabel2(value)

	@property
	def icon(self):
#		xbmc.log(str('def icon(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._art.get('icon')

	@icon.setter
	def icon(self, value):
#		xbmc.log(str('def icon(self, value):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._art['icon'] = value
		self._listitem.setArt(self._art)

	@property
	def thumbnail(self):
#		xbmc.log(str(' def thumbnail(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._art.get('thumb')

	@thumbnail.setter
	def thumbnail(self, value):
#		xbmc.log(str(' def thumbnail(self, value): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._art['thumb'] = value
		self._listitem.setArt(self._art)

	@property
	def poster(self):
#		xbmc.log(str('  def poster(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._art.get('poster')

	@poster.setter
	def poster(self, value):
#		xbmc.log(str(' def poster(self, value): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._art['poster'] = value
		self._listitem.setArt(self._art)

	@property
	def art(self):
#		xbmc.log(str(' def art(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._art

	@art.setter
	def art(self, value):
#		xbmc.log(str('def art(self, value):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._art = value
		self._listitem.setArt(value)

	def set_art(self, value):
#		xbmc.log(str('def set_art(self, value):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._art = value
		self._listitem.setArt(value)

	@property
	def path(self):
#		xbmc.log(str('def path(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._path

	@path.setter
	def path(self, value):
#		xbmc.log(str('def path(self, value):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._path = value
		self._listitem.setPath(value)

	@property
	def playable(self):
#		xbmc.log(str('def playable(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._playable

	@playable.setter
	def playable(self, value):
#		xbmc.log(str('def playable(self, value):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._playable = value
		if value:
			self.is_folder = False
		is_playable = 'true' if self._playable else 'false'
		self.set_property('isPlayable', is_playable)

	@property
	def played(self):
#		xbmc.log(str('def played(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._played

	@played.setter
	def played(self, value):
#		xbmc.log(str('def played(self, value):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._played = value

	def set_played(self, was_played):
#		xbmc.log(str('  def set_played(self, was_played):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._played = was_played

	@classmethod
	def from_dict(cls, label=None, label2=None, icon=None, thumbnail=None, path=None, selected=None,
					info=None, properties=None, context_menu=None, replace_context_menu=False,
					is_playable=None, info_type='video', stream_info=None, **kwargs):
#		xbmc.log(str(' def from_dict(cls, label=None, label2=None, icon=None, thumbnail=None, path=None, selected=None, ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		listitem = cls(label, label2, path=path)
		listitem.art = {
			'icon': icon,
			'thumb': thumbnail,
			'poster': kwargs.get('poster'),
			'banner': kwargs.get('banner'),
			'fanart': kwargs.get('fanart'),
			'clearlogo': kwargs.get('clearlogo'),
			'clearart': kwargs.get('clearart'),
			'landscape': kwargs.get('landscape')
			}

		if selected is not None:
			listitem.selected = selected
		if info:
			listitem.set_info(info_type, listitem.clean_info(info))
		if is_playable:
			listitem.playable = True
			listitem.is_folder = False
		if properties:
			if hasattr(properties, 'items'):
				properties = properties.items()
			for key, val in properties:
				if not isinstance(val, (str, unicode)):
					val = str(val)
				listitem.set_property(key, val)
		if stream_info:
			for stream_type, stream_values in stream_info.items():
				listitem.add_stream_info(stream_type, stream_values)
		if context_menu:
			listitem.add_context_menu_items(context_menu, replace_context_menu)
		return listitem

	def clean_info(self, info):
#		xbmc.log(str('def clean_info(self, info):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		keys_to_pop = ['fanart', 'imdb_id', 'name', 'poster', 'tmdb', 'trakt_id', 'tvdb_id']

		for i in keys_to_pop:
			try:
				info.pop(i, None)
			except:
				pass

		return info

class SortMethod(object):

	@classmethod
	def from_string(cls, sort_method):
#		xbmc.log(str('def from_string(cls, sort_method):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return getattr(cls, sort_method.upper())
	
class XBMCMixin(object):

	_function_cache_name = '.functions'
	_lock = threading.Lock()

	def cached(self, TTL=60*24, cache=None):
#		xbmc.log(str(' def cached(self, TTL=60*24, cache=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		cachename = cache
		if cachename is None:
			cachename = self._function_cache_name
		if not hasattr(self, '_unsynced_storages'):
			self._unsynced_storages = {}
		unsynced_storages = self._unsynced_storages
		storage_path = self.storage_path

		def decorating_function(function):

			@functools.wraps(function)
			def wrapper(*args, **kwargs):
				storage = XBMCMixin.get_storage_s(unsynced_storages, storage_path, cachename, file_format='pickle', TTL=TTL)
				kwd_mark = 'f35c2d973e1bbbc61ca60fc6d7ae4eb3'
				key = (function.__name__, kwd_mark,) + args
				if kwargs:
					key += (kwd_mark,) + tuple(sorted(kwargs.items()))
				try:
					result = storage[key]
				except KeyError:
					result = function(*args, **kwargs)
					if result:
						storage[key] = result
						storage.sync()
				return result
			return wrapper
		return decorating_function

	def clear_function_cache(self):
#		xbmc.log(str(' def clear_function_cache(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.get_storage(self._function_cache_name).clear()

	def list_storages(self):
#		xbmc.log(str('def list_storages(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return [name for name in os.listdir(self.storage_path) if not name.startswith('.')]

	@staticmethod
	def get_storage_s(unsynced_storages, storage_path, name='main', file_format='pickle', TTL=None):
#		xbmc.log(str(' def get_storage_s(unsynced_storages, storage_path, name=main, file_format=pickle, TTL=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		filename = os.path.join(storage_path, name)
		storage = unsynced_storages.get(filename)
		if storage is None:
			with XBMCMixin._lock:
				storage = unsynced_storages.get(filename)
				if storage is None:
					if TTL:
						TTL = datetime.timedelta(minutes=TTL)
					try:
						storage = TimedStorage(filename, file_format, TTL)
					except ValueError:
						os.remove(filename)
						storage = TimedStorage(filename, file_format, TTL)
					unsynced_storages[filename] = storage
		return storage
				
	def get_storage(self, name='main', file_format='pickle', TTL=None):
#		xbmc.log(str(' def get_storage(self, name=main, file_format=pickle, TTL=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if not hasattr(self, '_unsynced_storages'):
			self._unsynced_storages = {}
		return XBMCMixin.get_storage_s(self._unsynced_storages, self.storage_path, name, file_format, TTL)
		
	def temp_fn(self, path):
#		xbmc.log(str('def temp_fn(self, path):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return os.path.join(xbmc.translatePath('special://temp/'), path)

	def get_string(self, stringid):
#		xbmc.log(str('  def get_string(self, stringid):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		stringid = int(stringid)
		if not hasattr(self, '_strings'):
			self._strings = {}
		if not stringid in self._strings:
			self._strings[stringid] = self.addon.getLocalizedString(stringid)
		return self._strings[stringid]

	def set_content(self, content):
#		xbmc.log(str('def set_content(self, content):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		contents = [
			'actors',
			'addons',
			'countries',
			'directors',
			'episodes',
			'files',
			'genres',
			'images',
			'movies',
			'playlists',
			'roles',
			'seasons',
			'sets',
			'studios',
			'tags',
			'tvshows',
			'videos',
			'years'
			]
		xbmcplugin.setContent(self.handle, content)

	def get_setting(self, key, converter=None, choices=None):
#		xbmc.log(str(' def get_setting(self, key, converter=None, choices=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		value = self.addon.getSetting(key)
		if converter is str:
			return value
		elif converter is unicode:
			return value.decode('utf-8')
		elif converter is bool:
			return value == 'true'
		elif converter is int:
			return int(value)
		elif isinstance(choices, (list, tuple)):
			return choices[int(value)]
		elif converter is None:
			try:
				return json.loads(value)
			except:
				return value
		else:
			raise TypeError('Acceptable converters are str, unicode, bool and int. Acceptable choices are instances of list  or tuple.')

	def set_setting(self, key, val):
#		xbmc.log(str(' def set_setting(self, key, val): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if isinstance(val, list) or isinstance(val, dict):
			val = json.dumps(val)
		return self.addon.setSetting(id=key, value=val)

	def open_settings(self):
#		xbmc.log(str('def open_settings(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.addon.openSettings()

	@staticmethod
	def add_to_playlist(items, playlist='video'):
#		xbmc.log(str(' def add_to_playlist(items, playlist=video): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		playlists = {'music': 0, 'video': 1}
		if playlist not in playlists:
			raise ValueError('Playlist "%s" is invalid.' % playlist)
		selected_playlist = xbmc.PlayList(playlists[playlist])
		_items = []
		for item in items:
			if not hasattr(item, 'as_xbmc_listitem'):
				item['info_type'] = playlist
				item = ListItem.from_dict(**item)
			_items.append(item)
			selected_playlist.add(item._path, item.as_xbmc_listitem())
		return _items

	def get_view_mode_id(self, view_mode):
#		xbmc.log(str(' def get_view_mode_id(self, view_mode): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		view_mode_ids = VIEW_MODES.get(view_mode.lower())
		if view_mode_ids:
			return view_mode_ids.get(xbmc.getSkinDir())
		return None

	def set_view_mode(self, view_mode_id):
#		xbmc.log(str(' def set_view_mode(self, view_mode_id): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		xbmc.executebuiltin('Container.SetViewMode(%d)' % view_mode_id)

	def keyboard(self, default=None, heading=None, hidden=False):
#		xbmc.log(str(' def keyboard(self, default=None, heading=None, hidden=False): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if heading is None:
			heading = self.addon.getAddonInfo('name')
		if default is None:
			default = ''
		keyboard = xbmc.Keyboard(default, heading, hidden)
		keyboard.doModal()
		if keyboard.isConfirmed():
			return keyboard.getText()

	def notify(self, heading, message, icon, time, sound=False):
#		xbmc.log(str('def notify(self, heading, message, icon, time, sound=False):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if heading is None:
			heading = self.addon.getAddonInfo('name')
		return xbmcgui.Dialog().notification(heading, message, icon, time, sound)

	def ok(self, heading, line1, line2='', line3=''):
#		xbmc.log(str(' def ok(self, heading, line1, line2='', line3=''): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return xbmcgui.Dialog().ok(heading, line1, line2, line3)

	def select(self, heading, list):
#		xbmc.log(str(' def select(self, heading, list): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return xbmcgui.Dialog().select(heading, list)

	def yesno(self, heading, line1, line2='', line3='', nolabel='No', yeslabel='Yes'):
#		xbmc.log(str('def yesno(self, heading, line1, line2=, line3=, nolabel=No, yeslabel=Yes):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel)

	def setProperty(self, key, value):
#		xbmc.log(str(' def setProperty(self, key, value): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		xbmcgui.Window(10000).setProperty(key, str(value))

	def getProperty(self, key):
#		xbmc.log(str(' def getProperty(self, key): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return xbmcgui.Window(10000).getProperty(key)

	def clearProperty(self, key):
#		xbmc.log(str('def clearProperty(self, key):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		xbmcgui.Window(10000).clearProperty(key)

	def get_addon_icon(self):   
#		xbmc.log(str('def get_addon_icon(self):   ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self.addon.getAddonInfo('icon')

	def get_addon_fanart(self):
#		xbmc.log(str(' def get_addon_fanart(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self.addon.getAddonInfo('fanart')

	def get_media_icon(self, icon):
#		xbmc.log(str('def get_media_icon(self, icon):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		addon_path = self.addon.getAddonInfo('path')	
		return os.path.join(addon_path, 'resources', 'media', icon + '.png')

	def _listitemify(self, item):
#		xbmc.log(str(' def _listitemify(self, item): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		info_type = self.info_type if hasattr(self, 'info_type') else 'video'
		if not hasattr(item, 'as_tuple') and hasattr(item, 'keys'):
			if 'info_type' not in item:
				item['info_type'] = info_type
			item = ListItem.from_dict(**item)
		return item

	def _add_subtitles(self, subtitles):
#		xbmc.log(str('  def _add_subtitles(self, subtitles):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		player = xbmc.Player()
		for _ in xrange(30):
			if player.isPlaying():
				break
			time.sleep(1)
		else:
			raise Exception('No video playing. Aborted after 30 seconds.')
		player.setSubtitles(subtitles)

	def set_resolved_url(self, item=None, subtitles=None):
#		xbmc.log(str('def set_resolved_url(self, item=None, subtitles=None)  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if self._end_of_directory:
			raise Exception('Current Kodi handle has been removed. Either set_resolved_url(), end_of_directory(), or finish() has already been called.')
		self._end_of_directory = True
		succeeded = True
		if item is None:
			item = {}
			succeeded = False
		if isinstance(item, basestring):
			item = {'path': item}
		item = self._listitemify(item)
		item.set_played(True)
		xbmcplugin.setResolvedUrl(self.handle, succeeded, item.as_xbmc_listitem())
		if subtitles:
			self._add_subtitles(subtitles)
		return [item]

	def play_video(self, item, player=None):
#		xbmc.log(str('def play_video(self, item, player=None):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if isinstance(item, dict):
			item['info_type'] = 'video'
		item = self._listitemify(item)
		item.set_played(True)
		if player:
			_player = xbmc.Player(player)
		else:
			_player = xbmc.Player()
		_player.play(item._path, item.as_xbmc_listitem())
		return [item]

	def play_audio(self, item, player=None):
#		xbmc.log(str(' def play_audio(self, item, player=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		try:
			item['info_type'] = 'audio'
		except TypeError:
			pass
		item = self._listitemify(item)
		item.set_played(True)
		if player:
			_player = xbmc.Player(player)
		else:
			_player = xbmc.Player()
		_player.play(item._path, item.as_xbmc_listitem())
		return [item]

	def add_items(self, items):
#		xbmc.log(str(' def add_items(self, items): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		_items = [self._listitemify(item) for item in items]
		tuples = [item.as_tuple() for item in _items if hasattr(item, 'as_tuple')]
		xbmcplugin.addDirectoryItems(self.handle, tuples, len(tuples))
		self.added_items.extend(_items)
		return _items

	def add_sort_method(self, sort_method, label2_mask=None):
#		xbmc.log(str(' def add_sort_method(self, sort_method, label2_mask=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		try:
			sort_method = SortMethod.from_string(sort_method)
		except AttributeError:
			pass
		if label2_mask:
			xbmcplugin.addSortMethod(self.handle, sort_method, label2_mask)
		else:
			xbmcplugin.addSortMethod(self.handle, sort_method)

	def end_of_directory(self, succeeded=True, update_listing=False, cache_to_disc=True):
#		xbmc.log(str('def end_of_directory(self, succeeded=True, update_listing=False, cache_to_disc=True):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._update_listing = update_listing
		if not self._end_of_directory:
			self._end_of_directory = True
			return xbmcplugin.endOfDirectory(self.handle, succeeded, update_listing, cache_to_disc)
		else:
			raise Exception('Already called endOfDirectory.')

	def finish(self, items=None, sort_methods=None, succeeded=True, update_listing=False, cache_to_disc=True, view_mode=None):
#		xbmc.log(str('def finish(self, items=None, sort_methods=None, succeeded=True, update_listing=False, cache_to_disc=True, view_mode=None):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if items:
			self.add_items(items)
		if sort_methods:
			for sort_method in sort_methods:
				if isinstance(sort_method, (list, tuple)):
					self.add_sort_method(*sort_method)
				else:
					self.add_sort_method(sort_method)
		if view_mode is not None:
			try:
				view_mode_id = int(view_mode)
			except ValueError:
				view_mode_id = None
			if view_mode_id is not None:
				self.set_view_mode(view_mode_id)
		self.end_of_directory(succeeded, update_listing, cache_to_disc)
		return self.added_items

class Request(object):
	def __init__(self, url, handle):
#		xbmc.log(str(' def __init__(self, url, handle): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self.url = url
		self.handle = int(handle)
		self.scheme, remainder = url.split(':', 1)
		parts = urlparse.urlparse(remainder)
		self.netloc, self.path, self.query_string = (parts[1], parts[2], parts[4])
		self.args = unpickle_args(urlparse.parse_qs(self.query_string))

def unpickle_args(items):
#	xbmc.log(str('def unpickle_args(items):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
	pickled= items.pop('_pickled', None)
	if pickled is None:
		return items
	pickled_keys = pickled[0].split(',')
	ret = {}
	for key, vals in items.items():
		if key in pickled_keys:
			ret[key] = [pickle.loads(val) for val in vals]
		else:
			ret[key] = vals
	return ret

def pickle_dict(items):
#	xbmc.log(str(' def pickle_dict(items): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
	ret = {}
	pickled_keys = []
	for key, val in items.items():
		if isinstance(val, basestring):
			ret[key] = val
		else:
			pickled_keys.append(key)
			ret[key] = pickle.dumps(val)
	if pickled_keys:
		ret['_pickled'] = ','.join(pickled_keys)
	return ret

def unpickle_dict(items):
#	xbmc.log(str(' def unpickle_dict(items): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
	pickled_keys = items.pop('_pickled', '').split(',')
	ret = {}
	for key, val in items.items():
		if key in pickled_keys:
			ret[key] = pickle.loads(val)
		else:
			ret[key] = val
	return ret

class AmbiguousUrlException(Exception):
#	xbmc.log(str(' class AmbiguousUrlException(Exception): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
	pass

class NotFoundException(Exception):
#	xbmc.log(str('class NotFoundException(Exception):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
	pass

class UrlRule(object):
	def __init__(self, url_rule, view_func, name, options):
#		xbmc.log(str(' def __init__(self, url_rule, view_func, name, options): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._name = name
		self._url_rule = url_rule
		self._view_func = view_func
		self._options = options or {}
		self._keywords = re.findall(r'<(.+?)>', url_rule)
		self._url_format = self._url_rule.replace('<', '{').replace('>', '}')
		rule = self._url_rule
		if rule != '/':
			rule = self._url_rule.rstrip('/') + '/?'
		p = rule.replace('<', '(?P<').replace('>', '>[^/]+?)')
		try:
			self._regex = re.compile('^' + p + '$')
		except re.error:
			raise ValueError('There was a problem creating this URL rule. Ensure you do not have any unpaired angle brackets: "<" or ">"')

	def __eq__(self, other):
#		xbmc.log(str(' def __eq__(self, other): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if isinstance(other, UrlRule):
			return ((self._name, self._url_rule, self._view_func, self._options) == (other._name, other._url_rule, other._view_func, other._options))
		else:
			raise NotImplementedError

	def __ne__(self, other):
#		xbmc.log(str(' def __ne__(self, other): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return not self == other

	def match(self, path):
#		xbmc.log(str('def match(self, path):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		m = self._regex.search(path)
		if not m:
			raise NotFoundException
		items = dict((key, urllib.unquote_plus(val)) for key, val in m.groupdict().items())
		items = unpickle_dict(items)
		[items.setdefault(key, val) for key, val in self._options.items()]
		return self._view_func, items

	def _make_path(self, items):
#		xbmc.log(str(' def _make_path(self, items): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		for key, val in items.items():
			if not isinstance(val, basestring):
				raise TypeError('Value "%s" for key "%s" must be an instance of basestring' % (val, key))
			items[key] = urllib.quote_plus(val)
		try:
			path = self._url_format.format(**items)
		except AttributeError:
			path = self._url_format
			for key, val in items.items():
				path = path.replace('{%s}' % key, val)
		return path

	def _make_qs(self, items):
#		xbmc.log(str('def _make_qs(self, items):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return urllib.urlencode(pickle_dict(items))

	def make_path_qs(self, items):
#		xbmc.log(str(' def make_path_qs(self, items): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		for key, val in items.items():
			if isinstance(val, (int, long)):
				items[key] = str(val)
		url_items = dict((key, val) for key, val in self._options.items() if key in self._keywords)
		url_items.update((key, val) for key, val in items.items() if key in self._keywords)
		path = self._make_path(url_items)
		qs_items = dict((key, val) for key, val in items.items() if key not in self._keywords)
		qs = self._make_qs(qs_items)
		if qs:
			return '?'.join([path, qs])
		return path

	@property
	def regex(self):
#		xbmc.log(str(' def regex(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._regex

	@property
	def view_func(self):
#		xbmc.log(str(' def view_func(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._view_func

	@property
	def url_format(self):
#		xbmc.log(str(' def url_format(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._url_format

	@property
	def name(self):
#		xbmc.log(str(' def name(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._name

	@property
	def keywords(self):
#		xbmc.log(str('  def keywords(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._keywords

def setup_log(name):
#	xbmc.log(str(' def setup_log(name): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
	_log = logging.getLogger(name)
	GLOBAL_LOG_LEVEL = logging.DEBUG
	_log.setLevel(GLOBAL_LOG_LEVEL)
	handler = logging.StreamHandler()
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
	handler.setFormatter(formatter)
	_log.addHandler(handler)
	return _log

log = setup_log('xswift2')

class Plugin(XBMCMixin):
	def __init__(self, name=None, addon_id=None, info_type=None):
#		xbmc.log(str(' def __init__(self, name=None, addon_id=None, info_type=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)		
		self._name = name
		self._routes = []
		self._view_functions = {}
		self._addon = xbmcaddon.Addon()
		self._addon_id = addon_id or self._addon.getAddonInfo('id')
		self._name = name or self._addon.getAddonInfo('name')
		self._info_type = info_type
		if not self._info_type:
			types = {
				'video': 'video',
				'audio': 'music',
				'image': 'pictures',
				}
			self._info_type = types.get(self._addon_id.split('.')[1], 'video')
		self._current_items = []
		self._request = None
		self._end_of_directory = False
		self._update_listing = False
		self._log = setup_log(self._addon_id)
		self._storage_path = xbmc.translatePath('special://profile/addon_data/%s/.storage/' % self._addon_id)
		if not os.path.isdir(self._storage_path):
			os.makedirs(self._storage_path)

	@property
	def info_type(self):
#		xbmc.log(str(' def info_type(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._info_type

	@property
	def log(self):
#		xbmc.log(str(' def log(self):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._log

	@property
	def id(self):
#		xbmc.log(str(' def id(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._addon_id

	@property
	def storage_path(self):
#		xbmc.log(str('def storage_path(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._storage_path

	@property
	def addon(self):
#		xbmc.log(str('def addon(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._addon

	@property
	def added_items(self):
#		xbmc.log(str('def added_items(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._current_items

	def clear_added_items(self):
#		xbmc.log(str(' def clear_added_items(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._current_items = []

	@property
	def handle(self):
#		xbmc.log(str(' def handle(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self.request.handle

	@property
	def request(self):
#		xbmc.log(str(' def request(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if self._request is None:
			raise Exception('Please ensure that `plugin.run()` has been called before attempting to access the current request.')
		return self._request

	@property
	def name(self):
#		xbmc.log(str(' def name(self): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		return self._name

	@staticmethod
	def _parse_request(url=None, handle=None):
#		xbmc.log(str(' def _parse_request(url=None, handle=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		if url is None:
			url = sys.argv[0]
			if len(sys.argv) == 3:
				url += sys.argv[2]
		if handle is None:
			handle = sys.argv[1]
		return Request(url, handle)

	def cached_route(self, url_rule, name=None, options=None, TTL=None, cache=None):
#		xbmc.log(str('def cached_route(self, url_rule, name=None, options=None, TTL=None, cache=None):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		route_decorator = self.route(url_rule, name=name, options=options)
		if TTL:
			cache_decorator = self.cached(TTL, cache=cache)
		else:
			cache_decorator = self.cached(cache=cache)
		def new_decorator(func):
			return route_decorator(cache_decorator(func))
		return new_decorator

	def route(self, url_rule=None, name=None, root=False, options=None):
#		xbmc.log(str('  def route(self, url_rule=None, name=None, root=False, options=None):')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		def decorator(f):
			view_name = name or f.__name__
			if root:
				url = '/'
			elif not url_rule:
				url = '/' + view_name + '/'
				args = inspect.getargspec(f)[0]
				if args:
					url += '/'.join('%s/<%s>' % (p, p) for p in args)
			else:
				url = url_rule
			self.add_url_rule(url, f, name=view_name, options=options)
			return f
		return decorator

	def add_url_rule(self, url_rule, view_func, name, options=None):
#		xbmc.log(str(' def add_url_rule(self, url_rule, view_func, name, options=None): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		rule = UrlRule(url_rule, view_func, name, options)
		if name in self._view_functions.keys():
			self._view_functions[name] = None
		else:
			self._view_functions[name] = rule
		self._routes.append(rule)

	def url_for(self, endpoint, **items):
#		xbmc.log(str(' def url_for(self, endpoint, **items): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		try:
			rule = self._view_functions[endpoint]
		except KeyError:
			try:
				rule = (rule for rule in self._view_functions.values() if rule.view_func == endpoint).next()
			except StopIteration:
				raise NotFoundException("%s does not match any known patterns." % endpoint)
		if not rule:
			raise AmbiguousUrlException
		path_qs = rule.make_path_qs(items)
		return 'plugin://plugin.video.openmeta%s' % path_qs

	def redirect(self, url):
#		xbmc.log(str(' def redirect(self, url): ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		new_request = self._parse_request(url=url, handle=self.request.handle)
		log.debug('Redirecting %s to %s', self.request.path, new_request.path)
		self._request = new_request
		return self._dispatch(new_request.path)

	def run(self):
#		xbmc.log(str('def run(self):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		self._request = self._parse_request()
		items = self._dispatch(self.request.path)
		if hasattr(self, '_unsynced_storages'):
			for storage in self._unsynced_storages.values():
				storage.close()
		return items

	def _dispatch(self, path):
#		xbmc.log(str('def _dispatch(self, path):  ')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		for rule in self._routes:
			try:
				view_func, items = rule.match(path)
			except NotFoundException:
				continue
			resp = view_func(**items)
			if not self._end_of_directory and self.handle >= 0:
				if isinstance(resp, dict):
					resp['items'] = self.finish(**resp)
				elif isinstance(resp, collections.Iterable):
					resp = self.finish(items=resp)
			return resp
		raise NotFoundException('No matching view found for %s' % path)

plugin = Plugin()
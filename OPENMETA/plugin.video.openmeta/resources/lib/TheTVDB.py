# vi: set noet ff=dos :
import os, io, time, urllib, zipfile, requests_cache
from xml.etree import ElementTree
from resources.lib import text
from resources.lib.xswift2 import xbmc, plugin

ext_key = plugin.get_setting('tvdb_api', str)

def create_tvdb(language=xbmc.getLanguage(xbmc.ISO_639_1,)):
	return Tvdb(language=language)

API_key = ''
if len(ext_key) == 16:
	API_key = ext_key
else:
	API_key = 'AB2ED64C9BE51811'

def to_bytes(text):
	if isinstance(text, unicode):
		text = text.encode('utf-8')
	return text

class Show(dict):
	def __init__(self):
		dict.__init__(self)
		self.data = {}

	def __repr__(self):
		return '<Show %r (containing %s seasons)>' % (self.data.get(u'seriesname', 'instance'), len(self))

	def get(self, key, default=None):
		try:
			return self[key]
		except:
			pass
		return default

	def __getitem__(self, key):
		if key in self:
			return dict.__getitem__(self, key)
		if key in self.data:
			
			try:
				return dict.__getitem__(self.data, key)
				message = '%s not found' % key
			except:
				return
		raise KeyError('%s not found'  % key)

	def get_poster(self, language=None, default=None):
		try:
			posters = self['_banners']['poster'].values()
			posters = [poster for poster in posters if poster['season'] == str(self.num)]
			posters.sort(key=lambda k: float(k.get('rating',0)), reverse=True)
			if language:
				posters.sort(key=lambda k: k['language']!=language)
			return posters[0]['_bannerpath']
		except:
			return default

class Season(dict):
	def __init__(self, show=None, num=0):
		self.show = show
		self.num = num

	def __repr__(self):
		return '<Season %d instance (containing %s episodes)>' % (self.num, len(self.keys()))

	def __getitem__(self, episode_number):
		return dict.__getitem__(self, episode_number)

	def has_aired(self, flexible=False):
		if len(self.keys()) > 0 and self.values()[0].has_aired(flexible):
			return True
		return False

	def get_poster(self, language=None, default=None):
		try:
			posters = self.show['_banners']['season']['season'].values()
			posters = [poster for poster in posters if poster['season'] == str(self.num)]
			posters.sort(key=lambda k: float(k.get('rating',0)), reverse=True)
			if language:
				posters.sort(key=lambda k: k['language']!=language)
			return posters[0]['_bannerpath']
		except:
			return default

class Episode(dict):
	def __init__(self, season=None):
		self.season = season

	def __repr__(self):
		seasno = int(self.get(u'seasonnumber', 0))
		epno = int(self.get(u'episodenumber', 0))
		epname = self.get(u'episodename')
		if epname is not None:
			return '<Episode %02dx%02d - %r>' % (seasno, epno, epname)
		else:
			return '<Episode %02dx%02d>' % (seasno, epno)

	def __getitem__(self, key):
		return dict.__getitem__(self, key)

	def get_air_time(self):
		firstaired = self.get('firstaired', None)
		if firstaired and '-' in firstaired:
			try:
				return text.date_to_timestamp(firstaired)
			except:
				pass
		return -1

	def get_imdb(self):
		firstaired = self.get('imdb_id')
		if firstaired and firstaired not in ('', None):
			try:
				return firstaired
			except:
				pass
		return '0'

	def has_aired(self, flexible=False):
		if not self.get('firstaired', None):
			return flexible
		return self.get_air_time() <= time.time()

class Tvdb:
	def __init__(self, language='en'):
#		xbmc.log(str('/tv_genres')+'===>OPENMETA', level=xbmc.LOGNOTICE)
		languages = ['da', 'fi', 'nl', 'de', 'it', 'es', 'fr', 'pl', 'hu',
					'el', 'tr', 'ru', 'he', 'ja', 'pt', 'zh', 'cs', 'sl',
					'hr', 'ko', 'sv', 'no']
		config = {}
		config['apikey'] = API_key
		if language in languages:
			config['language'] = language
		else:
			config['language'] = 'en'
		config['url_search'] = u'https://thetvdb.com/api/GetSeries.php?seriesname=%%s&language=%%s' % config
		config['url_search_by_imdb'] = u'https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%%s&language=%%s' % config
		config['url_sid_full'] = u'https://thetvdb.com/api/%(apikey)s/series/%%s/all/%%s.zip' %  config
		config['url_sid_base'] = u'https://thetvdb.com/api/%(apikey)s/series/%%s/%%s.xml' % config
		config['url_artwork_prefix'] = u'https://thetvdb.com/banners/%%s' % config
		self.config = config
		self.session = requests_cache.CachedSession(expire_after=21600, backend='sqlite', cache_name=os.path.join(plugin.storage_path, 'TheTVDB'))
		self.shows = {}

	def clear_cache(self):
		try:
			self.session.cache.clear()
		except:
			pass

	def search(self, series, year=None, language='en'):
		series = urllib.quote(to_bytes(series))
		result = self._loadUrl(self.config['url_search'] % (series, language))
		seriesEt = self._parseXML(result)
		allSeries = []
		for series in seriesEt:
			result = {elem.tag.lower(): elem.text
						for elem in series.getchildren() if elem.text}
			result['id'] = int(result['id'])
			if 'aliasnames' in result:
				result['aliasnames'] = result['aliasnames'].split('|')
			if year:
				try:
					year = int(year)
					aired_year = int(result['firstaired'].split('-')[0].strip())
					if aired_year != year:
						continue
				except:
					continue
			allSeries.append(result)
		return allSeries

	def search_by_imdb(self, imdb_id, year=None):
		language = 'en'
		result = self._loadUrl(self.config['url_search_by_imdb'] % (imdb_id, language))
		pre_tvdb = str(result).split('<seriesid>')
		if len(pre_tvdb) > 1:
			tvdb = str(pre_tvdb[1]).split('</seriesid>')
			return tvdb[0]
		else:
			return None

	def url_sid_full(self, sid, language):
		return self.config['url_sid_full'] % (sid, language)

	def get_show(self, sid, language=None, full=False):
		if language is None:
			language = self.config['language']
		if full:
			url = self.url_sid_full(sid, language)
			response = self._loadZip(url)
			for fname in ('%s.xml', '%s.zip.xml'):
				xml_fname = fname % language
				if xml_fname in response:
					break
			else:
				raise KeyError("Show XML not found in zip from API")
			fullDataEt = self._parseXML(response[xml_fname])
			self._parseSeriesData(sid, fullDataEt)
			self._parseEpisodesData(sid, fullDataEt)
			bannersEt = self._parseXML(response['banners.xml'])
			self._parseBanners(sid, bannersEt)
		else:
			url = self.config['url_sid_base'] % (sid, language)
			response = self._loadUrl(url)
			if '404 Not Found' in str(response):
				return None
			else:
				seriesInfoEt = self._parseXML(response)
				self._parseSeriesData(sid, seriesInfoEt)
		return self.shows[sid]

	def __getitem__(self, key):
		key = int(key)
		if key not in self.shows:
			self.shows[key] = self.get_show(key, full=True)
		return self.shows[key]

	def _loadZip(self, url):
		resp = self.session.get(url)
		if 'application/zip' in resp.headers.get('Content-Type', ''):
			myzipfile = zipfile.ZipFile(io.BytesIO(resp.content))
			files = myzipfile.namelist()
			return dict([(file, myzipfile.read(file)) for file in files])
		return None

	def _loadUrl(self, url):
		resp = None
		for i in xrange(3):
			try:
				resp = self.session.get(url)
				break
			except:
				time.sleep(0.5)
		if resp is None:
			raise
		return resp.content

	def _parseXML(self, content):
		content = content.rstrip('\r')
		try:
			return ElementTree.fromstring(content)
		except ParseError:
			xbmc.log("An error occured when parsing data from TVDB.", level=xbmc.LOGERROR)
			return

	def _cleanData(self, data):
		data = data.replace(u'&amp;', u'&')
		data = data.strip()
		return data

	def _setShowData(self, sid, key, value):
		if sid not in self.shows:
			self.shows[sid] = Show()
		self.shows[sid].data[key] = value

	def _setItem(self, sid, seas, ep, attrib, value):
		if sid not in self.shows:
			self.shows[sid] = Show()
		if seas not in self.shows[sid]:
			self.shows[sid][seas] = Season(show = self.shows[sid], num=seas)
		if ep not in self.shows[sid][seas]:
			self.shows[sid][seas][ep] = Episode(season = self.shows[sid][seas])
		self.shows[sid][seas][ep][attrib] = value

	def _parseEpisodesData(self, sid, et):
		for cur_ep in et.findall('Episode'):
			elem_seasnum, elem_epno = cur_ep.find('SeasonNumber'), cur_ep.find('EpisodeNumber')
			if elem_seasnum is None or elem_epno is None:
				continue
			seas_no = int(float(elem_seasnum.text))
			ep_no = int(float(elem_epno.text))
			for cur_item in cur_ep.getchildren():
				tag = cur_item.tag.lower()
				value = cur_item.text
				if value is not None:
					if tag == 'filename':
						value = self.config['url_artwork_prefix'] % (value)
					else:
						value = self._cleanData(value)
					self._setItem(sid, seas_no, ep_no, tag, value)

	def _parseSeriesData(self, sid, et):
		for curInfo in et.findall('Series')[0]:
			tag = curInfo.tag.lower()
			value = curInfo.text
			if value is not None:
				if tag in ['banner', 'fanart', 'poster']:
					value = self.config['url_artwork_prefix'] % (value)
				else:
					value = self._cleanData(value)
				self._setShowData(sid, tag, value)
				if tag == 'firstaired':
					try:
						self._setShowData(sid, 'year', int(value.split('-')[0].strip()))
					except:
						pass

	def _parseBanners(self, sid, bannersEt):
		banners = {}
		for cur_banner in bannersEt.findall('Banner'):
			bid = cur_banner.find('id').text
			btype = cur_banner.find('BannerType')
			btype2 = cur_banner.find('BannerType2')
			if btype is None or btype2 is None:
				continue
			btype, btype2 = btype.text, btype2.text
			if not btype in banners:
				banners[btype] = {}
			if not btype2 in banners[btype]:
				banners[btype][btype2] = {}
			if not bid in banners[btype][btype2]:
				banners[btype][btype2][bid] = {}
			for cur_element in cur_banner.getchildren():
				tag = cur_element.tag.lower()
				value = cur_element.text
				if tag is None or value is None:
					continue
				tag, value = tag.lower(), value.lower()
				banners[btype][btype2][bid][tag] = value
			for k, v in list(banners[btype][btype2][bid].items()):
				if k.endswith('path'):
					new_key = '_%s' % (k)
					new_url = self.config['url_artwork_prefix'] % (v)
					banners[btype][btype2][bid][new_key] = new_url
		self._setShowData(sid, '_banners', banners)

TVDB = Tvdb()

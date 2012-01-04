# -*- coding: utf-8 -*-


###
# Copyright (c) 2010, MrLoom
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###


import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.schedule as schedule
import supybot.ircmsgs as ircmsgs

import supybot.log as log

import urllib
import urllib2
import json
import time, datetime

class Radio(callbacks.Plugin):
	"""RfK-Plugin"""

	threaded = True

	def __init__(self, irc):
		self.__parent = super(Radio, self)
		self.__parent.__init__(irc)

		self.lastTrackId = 0
		self.lastDJId = 0
		self.lastDJ = None
		
		self.monitorList = None
		self._updateMonitorList(irc)

		def pollRadio():

			try:
				result = self._radioQuery('track,listener,dj', { 'ltid' : self.lastTrackId })

				# dj stopped streaming

				if ((result['djid'] == None) and (self.lastDJ != None)):
					announce = u'%s strömt nicht mehr' % (self.lastDJ)
					
					if(self.registryValue('autovoice')):
						self._undoAutoVoice(irc)

					self._radioStatusAnnounce(irc, announce)

				# dj changed

				elif ((result['djid'] != None) and (self.lastDJ != None) and
					 (result['djid'] != self.lastDJId)):
					announce = u'Statt %s strömt jetzt %s' % (
						self.lastDJ, result['dj'])
						
					if(self.registryValue('autovoice')):
						self._undoAutoVoice(irc)
						ircname = self._isIRC(result['djid'])
						if (ircname):
							self._doAutoVoice(irc, ircname)

					self._radioStatusAnnounce(irc, announce)

				# dj started streaming

				elif ((result['djid'] != None) and (self.lastDJ == None)):
					announce = u'%s strömt jetzt' % (result['dj'])
					
					if(self.registryValue('autovoice')):
						ircname = self._isIRC(result['djid'])
						if (ircname):
							self._doAutoVoice(irc, ircname)

					self._radioStatusAnnounce(irc, announce)

				# track changed

				if (('trackid' in result) and (result['trackid'] != self.lastTrackId)):
					#announce = u'[%s] %s - %s' % (result['dj'],
					#	result['artist'], result['title'])
					announce = u'%s - %s' % (result['artist'], result['title'])

					self._radioStatusAnnounce(irc, announce)

				# remember current status

				if ('trackid' in result):
					self.lastTrackId = result['trackid']

				if ('djid' in result):
					self.lastDJ = result['dj']
					self.lastDJId = result['djid']

				else:
					self.lastDJ = None
					self.lastDJId = 0

			except Exception, e:
				log.error('Error polling radio status: %s' % repr(e))

		if ("Radio.pollStatus" in schedule.schedule.events):
			schedule.removePeriodicEvent("Radio.pollStatus")

		if (self.registryValue('enablePolling')):
			schedule.addPeriodicEvent(pollRadio,
				self.registryValue('pollingInterval'),
				name="Radio.pollStatus")

	def tracklist(self, irc, msg, args, num):
		"""[<anzahl>]

		Zeigt die letzten gespielten Tracks an. Ohne Parameter werden die
		letzten 3 angezeigt.
		"""
		
		tracks = []

		if (num == None):
			num = 3

		if (num > 50):
			num = 50

		if (num <= 0):
			irc.reply('-.-')
			return

		result = self._radioQuery('tracks', { 'c': num })

		for track in result['history']:
			tracks.append('[%s - %s]' % (track['artist'], track['title']))

		irc.reply(', '.join(tracks).encode('utf-8'))

	tracklist = wrap(tracklist, [optional('int')])

	def show(self, irc, msg, args):
		"""
		Zeigt die aktuelle Sendung an.
		"""

		result = self._radioQuery('show,listener');
		

		if (not 'showname' in result and not 'status' in result):
			reply = u'Momentan läuft nichts'

		else:
			
			if (result['status'] == 'OVERLAP'):
				reply = u'Eigentlich sollte seit %s "%s" mit %s laufen, aber stattdessen läuft "%s" mit %s. Da hat wohl jemand episch versagt!' % (
				formatTimespan(int(time.time()) - result['ushowbegin']), result['ushowname'], result['ushowdj'], result['showname'], result['showdj'])
			elif (result['status'] == 'NOT_CONNECTED'):
				reply = u'Eigentlich sollte seit %s "%s" mit %s laufen, aber es strömt niemand. Da hat wohl jemand episch versagt!' % (
				formatTimespan(int(time.time()) - result['showbegin']), result['showname'], result['showdj'])
			else:
				reply = u'Momentan läuft %s (%s) mit %s' % (result['showname'],
					result['showdescription'], result['showdj'])

				if (result['showtype'] == 'PLANNED'):
					reply += u', noch %s' % (
						formatTimespan(result['showend'] - int(time.time())))

				else:
					reply += u', seit %s' % (
						formatTimespan(int(time.time()) - result['showbegin']))
			
			if(irc.nested):
				reply = u"%s" % result['showid']

		irc.reply(reply.replace('\n',' ').encode('utf-8'))

	def nextshow(self, irc, msg, args, djname):
		"""[<djname>]
		
		Zeigt die naechste geplante Sendung an.
		"""
		if(djname):
			result = self._radioQuery('nextshows', {'djname' : djname})
		else:
			result = self._radioQuery('nextshows')
			

		if (len(result['shows']) == 0):
			reply = u'Es sind keine Sendungen geplant'

		else:
			result = result['shows'][0]
			reply = u'Nächste geplante Sendung ist %s von %s (%s) [%s] - noch %s' % (
				result['showname'], result['showdj'], result['showdescription'],
				formatShowtime(result['showbegin'], result['showend']),
				formatTimespan(result['showbegin'] - int(time.time())))
			
			if(irc.nested):
				reply = u"%s" % result['showid']

		irc.reply(reply.replace('\n',' ').encode('utf-8'))
	nextshow = wrap(nextshow, [optional('text')])

	def lastshow(self, irc, msg, args, djname):
		"""[<djname>]
		
		Zeigt die letzte geplante Sendung an.
		"""
		if(djname):
			result = self._radioQuery('lastshows', {'djname' : djname})
		else:
			result = self._radioQuery('lastshows')
			

		if (len(result['shows']) == 0):
			reply = u'Es fand keine Sendung statt'

		else:
			result = result['shows'][0]
			reply = u'Letzte geplante Sendung war %s von %s (%s) [%s] - vor %s' % (
				result['showname'], result['showdj'], result['showdescription'],
				formatShowtime(result['showbegin'], result['showend']),
				formatTimespan(int(time.time()) - result['showend']))
				
			if(irc.nested):
				reply = u"%s" % result['showid']

		irc.reply(reply.replace('\n',' ').encode('utf-8'))
	lastshow = wrap(lastshow, [optional('text')])
	
	def dj(self, irc, msg, args):
		"""
		Zeigt den aktuellen DJ an.
		"""

		result = self._radioQuery('dj,listener')

		if (result['dj'] == None):
			reply = u'Momentan strömt niemand'

		else:
			#reply = u'Momentan strömt %s (%s)' % (result['dj'], formatListeners(result))
			reply = u'Momentan strömt %s' % (result['dj'])
			
		irc.reply(reply.encode('utf-8'))
		
	def kickdj(self, irc, msg, args):
		"""
		Kickt den aktuellen DJ.
		"""

		result = self._radioQuery('dj,kickdj')

		if (result['dj'] == None):
			reply = u'Momentan strömt niemand'

		else:
			if (result['status'] == 0):
				reply = u'%s wurde entfernt und für 2 Minuten gesperrt' % (result['dj'])
			else:
				reply = u'Hafensäuberung nicht möglich'
				
		irc.reply(reply.encode('utf-8'))
	kickdj = wrap(kickdj,['admin'])

	def track(self, irc, msg, args):
		"""
		Zeigt den aktuellen Track an.
		"""

		result = self._radioQuery('track,listener,dj', {'ltid' : 0})

		if (result['dj'] == None):
			reply = u'Momentan strömt niemand'

		else:
			#reply = u'%s - %s (%s)' % (result['artist'],
			#	result['title'], formatListeners(result))
			reply = u'%s - %s' % (result['artist'], result['title'],)

		irc.reply(reply.encode('utf-8'))
	
	def rtraffic(self, irc, msg, args):
		"""
		Zeigt den aktuellen Traffic an.
		"""
		
		result = self._radioQuery('traffic')

		sum = 0
		master = 0
		slaves = []
				
		for relay in result['traffic']:
			if relay['out'] == None:
				relay['out'] = 0
			
			if relay['hostname'] == 'radio.krautchan.net':
				# Masterserver
				master = int(relay['out'])
				sum += master
			else:
				# Slaves
				slaves.append('%i kB/s via Relay #%i' % (int(relay['out']), int(relay['relay'])))
				sum += int(relay['out'])
		
		reply = u"%i kB/s ( %i kB/s via Master | %s )" % (sum, master, ' | '.join(slaves))				
		irc.reply(reply.encode('utf-8'))
				
	def listeners(self, irc, msg, args):
		"""
		Zeigt die Anzahl der momentanen Zuhoerer an.
		"""
		
		foreign = 0
		sum = 0
		tmp = 0

		result = self._radioQuery('listener')
		mounts = formatListeners(result)

		result = self._radioQuery('countries')
		countries = []
		
		for country in result['countries']:
			countries.append('%s: %i' % (country['country'], country['count']))
			sum += country['count']
			if ((country['country'] != 'DE') and (country['country'] != 'BAY')):
				foreign += country['count']
			
			tmp = float(foreign) / float(sum)
			tmp = tmp * 100
			
		reply =  u"%s )( %s )( %i%% Ausländer )" % (mounts, ' | '.join(countries), int(tmp))
		irc.reply(reply.encode('utf-8'))
		
	def relays(self, irc, msg, args):
		"""
		Zeigt die Anzahl der Zuhoerer pro Relay
		"""
		
		sum = 0
		master = 0
		slaves = []
		
		result = self._radioQuery('relay')
		
		for relay in result['relay']:
			if relay['hostname'] == 'radio.krautchan.net':
				# Masterserver
				master = int(relay['c'])
				sum += master
			else:
				# Slaves
				slaves.append('%i via Relay #%i' % (int(relay['c']), int(relay['relay'])))
				sum += int(relay['c'])
		
		if slaves:
			reply = u"%i Zuhörer ( %i via Master | %s )" % (sum, master, ' | '.join(slaves))
		else:
			reply = u"%i Zuhörer ( %i via Master )" % (sum, master)
			
		irc.reply(reply.encode('utf-8'))
		
	def streams(self, irc, msg, args):
		"""
		Sendet die URLs via Query.
		"""
		
		irc.queueMsg(ircmsgs.privmsg(msg.nick, 'http://radio.krautchan.net:8000/radio.mp3'))
		irc.queueMsg(ircmsgs.privmsg(msg.nick, 'http://radio.krautchan.net:8000/radio.ogg'))
		irc.queueMsg(ircmsgs.privmsg(msg.nick, 'http://radio.krautchan.net:8000/radiohq.ogg'))
		irc.queueMsg(ircmsgs.privmsg(msg.nick, 'http://radio.krautchan.net:8000/radio.aacp'))
		
		irc.noReply()
		
	def authtest(self, irc, msg, args):
		"""
		Test für IRC2Radio-Vietschers
		"""
		result = self._radioQuery('auth', { 'hostmask' : msg.prefix })
		
		if (result['auth']['status'] != 0):
			reply = u'Auth fehlgeschlagen'
			irc.reply(reply.encode('utf-8'))
		else:
			reply = u"IRC-Account '%s' ist mit Radioaccount '%s' verknüpft" % (msg.prefix, result['auth']['nick'])
			irc.reply(reply.encode('utf-8'))
			
	def authadd(self, irc, msg, args, username, password):
		"""<username> <streampassword>
		
		Verknüpft IRC-Account mit Radioaccount
		"""
		result = self._radioQuery('authadd', {'hostmask':msg.prefix, 'user':username, 'pass':password})
		
		if (result['auth']['status'] != 0):
			reply = u'Auth fehlgeschlagen'
			irc.reply(reply.encode('utf-8'))
		else:
			reply = u"IRC-Account '%s' wurde mit Radioaccount '%s' verknüpft" % (msg.prefix, result['auth']['nick'])
			result = self._radioQuery('authjoin', { 'hostmask' : msg.prefix })
			irc.reply(reply.encode('utf-8'))
	authadd = wrap(authadd, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])
		
	def doJoin(self, irc, msg):
		if(self.registryValue('monitor')):
			if(self.registryValue('monitorChannel') == msg.args[0]):
				self._updateMonitorList(irc)
				result = self._radioQuery('authjoin', { 'hostmask' : msg.prefix })
	def doPart(self, irc, msg):
		if(self.registryValue('monitor')):
			if(self.registryValue('monitorChannel') == msg.args[0]):
				self._updateMonitorList(irc)
				result = self._radioQuery('authpart', { 'hostmask' : msg.prefix })
	def doQuit(self, irc, msg):
		if(self.registryValue('monitor')):
			if(msg.nick in self.monitorList):
				self._updateMonitorList(irc)
				result = self._radioQuery('authpart', { 'hostmask' : msg.prefix })
	def doNick(self, irc, msg):
		if(self.registryValue('monitor')):
			if(msg.nick in self.monitorList):
				self._updateMonitorList(irc)
				result = self._radioQuery('authupdate', { 'hostmask' : msg.prefix , 'nick' : msg.args[0] })
						
	def isirc(self, irc, msg, args, nick):
		result = self._radioQuery('djinfo', { 'djname' : nick })
		if (result['djid'] == None):
			reply = u"DJ nicht gefunden"
		else:
			result = self._radioQuery('isirc', { 'djid' : result['djid'] })
			if (result['auth']['status'] != 0):
				reply = u"%s ist momentan nicht im IRC" % nick
			else:
				nickirc = result['auth']['hostmask'].split('!')[0]
				reply = u"%s ist mit folgendem Nick im IRC: %s" % (nick, nickirc)
		irc.reply(reply.encode('utf-8'))
	isirc = wrap(isirc, ['text'])
			
	def rsync(self, irc, msg, args):
		self._updateMonitorList(irc)
		
		count = 0
		result = self._radioQuery('areirc')
		for hostmask in result['hostmasks']:
			hostmask = hostmask.encode('ascii')
			if ircutils.nickFromHostmask(hostmask) not in self.monitorList:
				self._radioQuery('authpart', { 'hostmask' : hostmask })
				count += 1
			else:
				hostmaskIRC = irc.state.nickToHostmask(ircutils.nickFromHostmask(hostmask))
				if (hostmask.split('!')[1] != hostmaskIRC.split('!')[1]):
					self._radioQuery('authpart', { 'hostmask' : hostmask })
					count += 1
		reply = u"%i Benutzer entfernt" % count
		irc.reply(reply.encode('utf-8'))
	rsync = wrap(rsync, ['admin'])
	
	def rconf(self, irc, msg, args, key, value):
		"""<key> [<value>]
		
		Setzt <value> für <key>, oder gibt ihn aus
		"""
		if(key and value):
			result = self._radioQuery('auth,rconfig', { 'hostmask' : msg.prefix, 'key' : key, 'value' : value })
			if('errid' in result):
				if(result['errid'] == 21):
					reply = u"Auth fehlgeschlagen"
				elif(result['errid'] == 22):
					reply = u"Eingabe ungültig"
			elif(result['status'] == 0):
				reply = u"Eingabe wurde übernommen"
		elif(key):
			result = self._radioQuery('auth,rconfig', { 'hostmask' : msg.prefix, 'key' : key })
			if('errid' in result):
				if(result['errid'] == 21):
					reply = u"Auth fehlgeschlagen"
				elif(result['errid'] == 22):
					reply = u"Eingabe ungültig"
			elif(result['status'] == 0):
				reply = u"Key: %s - Value: %s" % (result['key'], result['value'])
		else:
			reply = u"Eingabe ungültig"
		irc.reply(reply.encode('utf-8'))
	rconf = wrap(rconf, ['somethingWithoutSpaces', optional('text')])
	
	def rthread(self, irc, msg, args, show, thread):
		"""<showid> [<threadid>]
		
		Setzt oder gibt <threadid> für <showid> aus
		"""
		if(show and thread):
			result = self._radioQuery('auth,rthread', { 'hostmask' : msg.prefix, 'show' : show, 'thread' : thread })
			if('errid' in result):
				if(result['errid'] == 21):
					reply = u"Auth fehlgeschlagen"
				elif(result['errid'] == 22):
					reply = u"Eingabe ungültig"
			elif(result['status'] == 0):
				reply = u"Eingabe wurde übernommen"
		elif(show):
			result = self._radioQuery('rthread', { 'show' : show })
			if('errid' in result):
				if(result['errid'] == 22):
					reply = u"Eingabe ungültig"
			elif(result['status'] == 0):
				if(result['thread'] is not None):
					reply = u"http://krautchan.net/resolve/rfk/%s" % result['thread']
				else:
					reply = u"Keinen Thread für die angegebene Sendung gefunden"
			
		else:
			reply = u"Eingabe ungültig"
		irc.reply(reply.encode('utf-8'))
	rthread = wrap(rthread, ['somethingWithoutSpaces', optional('text')])
				
	def _radioQuery(self, function, parameters={}):

		parameters['w'] = function

		log.debug('Radio.query: %s' % (repr(parameters)))

		if (self.registryValue('httpProxy') != ''):
			opener = urllib2.build_opener(
				urllib2.ProxyHandler({'http': self.registryValue('httpProxy')}))

		else:
			opener = urllib2.build_opener()

		response = opener.open(self.registryValue('queryURL') + '?'+
			'apikey=' + self.registryValue('queryPass') + '&' +
			urllib.urlencode(parameters))
		data = json.loads(response.read())

		# teddy cannot into integer :3

		if ('listener' in data):
			for stream in data['listener']:
				stream['c'] = int(stream['c'])

		def convertInteger(d, key):
			if ((key in d) and (d[key] != None)):
				d[key] = int(d[key])

		for key in ['trackid', 'showbegin', 'showend', 'showid', 'djid']:
			convertInteger(data, key)

		log.debug('Radio.reply: %s' % repr(data))

		return(data)

	def _radioStatusAnnounce(self, irc, message):

		message = u'[RfK] %s' % (message)

		for channel in irc.state.channels:
			if (self.registryValue('announce', channel)):
				irc.queueMsg(ircmsgs.privmsg(channel, message.encode('utf-8')))
				
	def _updateMonitorList(self, irc):
		if(self.registryValue('monitor')):
			self.monitorList = []
			self.monitorList.extend(irc.state.channels[self.registryValue('monitorChannel')].users)
			self._radioQuery('irccount', { 'c' : len(self.monitorList) })
		
		
	def _isIRC(self, djid):
		result = self._radioQuery('isirc', { 'djid' : djid})
		if result['auth']['status'] == 0:
			return result['auth']['hostmask'].split('!')[0]
		else:
			return 0
	
	def _doAutoVoice(self, irc, nick):
		if nick not in irc.state.channels[self.registryValue('monitorChannel')].ops:
			irc.queueMsg(ircmsgs.voice(self.registryValue('monitorChannel'), nick))
	
	def _undoAutoVoice(self, irc):
		for nick in irc.state.channels[self.registryValue('monitorChannel')].voices:
			irc.queueMsg(ircmsgs.devoice(self.registryValue('monitorChannel'), nick))
					
Class = Radio


def formatListeners(data):

	streamNames = { 'MP3': 'MP3', 'OGG': 'OGG', 'OGGHQ': 'OGG-HQ' }

	totalListeners = 0
	perStream = []

	for stream in data['listener']:

		if (stream['c'] > 0):
			totalListeners += stream['c']

			perStream.append(u'%d via %s' % (stream['c'],
				streamNames.get(stream['name'], stream['name'])))

	if (totalListeners == 0):
		return(u'Keine Zuhörer')

	else:
		return(u'%d Zuhörer: ( %s' % (totalListeners, ' | '.join(perStream)))

def formatShowtime(start, end):
	dstart = datetime.datetime.fromtimestamp(start)
	dend = datetime.datetime.fromtimestamp(end)

	return(u'%s-%s' % (dstart.strftime('%d.%m. %H:%M'), dend.strftime('%H:%M')))

def formatTimespan(timespan):
   return(_formatTimespan(timespan,
      { 'separator': ', ',
        'format_singular': '1 %s',
        'format_plural': '%d %s',
        'week_singular': 'Woche',
        'week_plural': 'Wochen',
        'day_singular': 'Tag',
        'day_plural': 'Tage',
        'hour_singular': 'Stunde',
        'hour_plural': 'Stunden',
        'minute_singular': 'Minute',
        'minute_plural': 'Minuten',
        'second_singular': 'Sekunde',
        'second_plural': 'Sekunden' }))

def formatTimespanShort(timespan):
   return(_formatTimespan(timespan,
      { 'separator': '',
        'format_singular': '1%s',
        'format_plural': '%d%s',
        'week_singular': 'w',
        'week_plural': 'w',
        'day_singular': 'd',
        'day_plural': 'd',
        'hour_singular': 'h',
        'hour_plural': 'h',
        'minute_singular': 'm',
        'minute_plural': 'm',
        'second_singular': 's',
        'second_plural': 's' }))

def _formatTimespan(timespan, m):

   if (timespan < 1):
      return(m['format_plural'] % (0, m['second_plural']))

   text = ''
   timespan = int(timespan)
   left = timespan

   weeks = left / (60**2 * 24 * 7)
   left -= weeks * (60**2 * 24 * 7)

   days = left / (60**2 * 24)
   left -= days * (60**2 * 24)

   hours = left / (60**2)
   left -= hours * (60**2)

   minutes = left / 60
   left -= minutes * 60

   seconds = left

   def append_part(text, value, singular, plural):

      if (value <= 0):
         return(text)

      if (len(text) > 0):
         text += m['separator']

      if (value == 1):
         text += m['format_singular'] % (singular)

      else:
         text += m['format_plural'] % (value, plural)

      return(text)

   # weeks (always include)

   text = append_part(text, weeks, m['week_singular'], m['week_plural'])

   # days (always include)

   text = append_part(text, days, m['day_singular'], m['day_plural'])

   # hours (if < 1 week)

   if (timespan < (60**2 * 24 * 7)):
      text = append_part(text, hours, m['hour_singular'], m['hour_plural'])

   # minutes (if < 1 day)

   if (timespan < (60**2 * 24)):
      text = append_part(text, minutes, m['minute_singular'], m['minute_plural'])

   # seconds (if < 1 hour)

   if (timespan < (60**2)):
      text = append_part(text, seconds, m['second_singular'], m['second_plural'])

   return(text)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

###
# Copyright (c) 2011, MrLoom
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
import supybot.ircdb as ircdb


import socket
import time
import pygeoip



class OHL(callbacks.Plugin):
	"""Oberste Heeresleitung"""
	
	threaded = True
	
	def doJoin(self, irc, msg):
		
		# mibbit onJoin detection
		if(self.registryValue('mibbitAnnounce',msg.args[0])):
			if(msg.host.find('mibbit.com') != -1):
				ip = self._numToDottedQuad(msg.user)
				record = self._record_by_addr(ip)
				if record:
					reply = u'%s benutzt mibbit (%s, %s)' % (msg.nick, ip, self._geoip_city_check(record))
					irc.queueMsg(ircmsgs.privmsg(msg.args[0], reply))


	def shoa(self, irc, msg, args):
		"""
		Shoa ist anberaumt
		"""
		
		if(self._checkCPO(irc, msg)):
			
			def unlimit():
				irc.queueMsg(ircmsgs.unlimit(msg.args[0], 0))
				
			irc.queueMsg(ircmsgs.limit(msg.args[0], 1))  
			schedule.addEvent(unlimit, time.time() + 60)
			
			for nick in irc.state.channels[msg.args[0]].users:
				if nick not in irc.state.channels[msg.args[0]].ops:
					irc.queueMsg(ircmsgs.kick(msg.args[0], nick, 'Sie wurden soeben Opfer eines Pogroms'))
					
			irc.noReply()
				
	def k(self, irc, msg, args, nicks):
		"""[user] ... [user]
		Kick mit Timeban
		"""

		if(self._checkCPO(irc, msg)):
			
			for nick in nicks:
				prefix = irc.state.nickToHostmask(nick)
				user = ircutils.userFromHostmask(prefix)
				host = ircutils.hostFromHostmask(prefix)
			
				hostmask = '*!*@%s' % host
				if(host.find('mibbit.com') != -1):
					hostmask = '*!%s@*.mibbit.com' % user
			
				def unban():
					irc.queueMsg(ircmsgs.unban(msg.args[0], hostmask))
				
				irc.queueMsg(ircmsgs.ban(msg.args[0], hostmask))
				irc.queueMsg(ircmsgs.kick(msg.args[0], nick, nick))
				schedule.addEvent(unban, time.time() + 900)
			
		irc.noReply()
			
	k = wrap(k, [many('nickInChannel')])
	
	
	#mibbit
	def mibbit(self, irc, msg, args, nick):
		"""<nick>
		Mibbit-Check auf <nick>
		"""
		
		prefix = irc.state.nickToHostmask(nick)
		user = ircutils.userFromHostmask(prefix)
		host = ircutils.hostFromHostmask(prefix)
		if(host.find('mibbit.com') != -1):
			ip = self._numToDottedQuad(user)
			record = self._record_by_addr(ip)
			if record:
				reply = u'%s (%s)' % (ip, self._geoip_city_check(record))
			else:
				reply = u'geoIP Fehler!'
		else:
			reply = u'%s benutzt kein mibbit' % nick
		irc.reply(reply.encode('utf-8'))
	mibbit = wrap(mibbit, ['nickInChannel'])
	
	def mibbits(self, irc, msg, args):
		"""
		Zeigt alle mibbit-Benutzer im Kanal an
		"""
		
		mibbits = []
		for nick in irc.state.channels[msg.args[0]].users:
			prefix = irc.state.nickToHostmask(nick)
			user = ircutils.userFromHostmask(prefix)
			host = ircutils.hostFromHostmask(prefix)
			if(host.find('mibbit.com') != -1):
				ip = self._numToDottedQuad(user)
				record = self._record_by_addr(ip)
				if record:
					mibbits.append(u'%s (%s, %s)' % (nick, ip, self._geoip_city_check(record)))
				else:
					mibbits.append('%s (geoIP Fehler)' % (nick))
		if len(mibbits) > 0:
			reply =  u'mibbits: %s' % (', '.join(mibbits))
		else:
			reply = u'Keine mibbits entdeckt!'
		irc.reply(reply.encode('utf-8'))
	
	#geoip
	def geoip(self, irc, msg, args, ip):
		"""<IP>
		Zeigt GeoIP Infos zu <IP> an
		"""
		
		record = self._record_by_addr(ip)
		if record:
			reply = u'%s (%s)' % (ip, self._geoip_city_check(record))
		else:
			reply = u'geoIP Fehler!'
		irc.reply(reply.encode('utf-8'))
	geoip = wrap(geoip, ['ip'])
	
	def hex2ip(self, irc, msg, args, iphex):
		"""<HexIP>
		Wandelt 8Bit-Hexstring in IP um und gibt GeoIP Infos aus
		"""
		
		ip = self._numToDottedQuad(iphex)
		if ip and len(iphex) == 8:
			record = self._record_by_addr(ip)
			if record:
				reply = u'%s (%s)' % (ip, self._geoip_city_check(record))
			else:
				reply = u'geoIP Fehler!'
		else:
			reply = u'Invalide Eingabe'
		irc.reply(reply.encode('utf-8'))
	hex2ip = wrap(hex2ip, ['text'])
	
	def host2ip(self, irc, msg, args, hostname):
		"""<hostname>
		Wandelt <hostname> in IP um und gibt GeoIP Infos aus
		"""
		
		try:
			ip = socket.gethostbyname(hostname)
			if ip:
				record = self._record_by_addr(ip)
				if record:
					reply = u'%s (%s)' % (ip, self._geoip_city_check(record))
				else:
					reply = u'geoIP Fehler!'
			
		except:
			reply = u'gethostbyname() Error'
			
		irc.reply(reply.encode('utf-8'))
	host2ip = wrap(host2ip, ['text'])
	
	def ip2host(self, irc, msg, args, ip):
		"""<ip>
		Wandelt <ip> in hostname um und gibt GeoIP Infos aus
		"""
		
		try:
			hostname = socket.gethostbyaddr(ip)
			hostname = hostname[0]
			if hostname:
				record = self._record_by_addr(ip)
				if record:
					reply = u'%s (%s)' % (hostname, self._geoip_city_check(record))
				else:
					reply = u'geoIP Fehler!'
		except:
			reply = u'gethostbyaddr() Error'
			
		irc.reply(reply.encode('utf-8'))
	ip2host = wrap(ip2host, ['ip'])
	
	
	def _record_by_addr(self, ip):
		gi = pygeoip.GeoIP(self.registryValue('geoipdb'))	
		try:
			return gi.record_by_addr(ip)
		except:
			return False
			
	def _geoip_city_check(self, record):
			if 'city' in record and 'country_code' in record:
				return u'%s, %s' % (record['country_code'], record['city'])
			else:
				return u'%s' % (record['country_code'])
				
	def _checkCPO(self, irc, msg):
		if not irc.isChannel(msg.args[0]):
			irc.reply('Muss in einem Kanal gesendet werden!')
			return False
		elif msg.nick not in irc.state.channels[msg.args[0]].ops and not ircdb.checkCapability(msg.prefix, 'admin'):
			irc.reply('Als ob!')
			return False
		elif irc.nick not in irc.state.channels[msg.args[0]].ops:
			irc.reply('%s braucht op ;_;' % irc.nick)
			return False
		else:
			return True
	
	def _numToDottedQuad(self, n):
		try:
			n = long(n,16)
			d = 256 * 256 * 256
			q = []
			while d > 0:
				m,n = divmod(n,d)
				q.append(str(m))
				d = d/256
			return '.'.join(q)
		except:
			return False

Class = OHL


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

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

import time
import pygeoip



class OHL(callbacks.Plugin):
	"""Oberste Heeresleitung"""
	
	threaded = True
	
	def doJoin(self, irc, msg):
		
		# mibbit onJoin detection
		if(msg.host.find('mibbit.com') != -1):
			ip = self._numToDottedQuad(long(msg.user,16))
			record = self._record_by_addr(ip)
			if record:
				if 'city' in record:
					reply = u'%s benutzt mibbit (%s, %s, %s)' % (msg.nick, ip, record['country_code'], record['city'])
				else:
					reply = u'%s benutzt mibbit (%s, %s)' % (msg.nick, ip, record['country_code'])
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
					irc.queueMsg(ircmsgs.kick(msg.args[0], nick, "Sie wurden soeben vernichtet"))
					
			irc.noReply()
				
	def k(self, irc, msg, args, nick):
		"""<user>
		Kick mit Timeban
		"""

		if(self._checkCPO(irc, msg)):
			
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
			
	k = wrap(k, ['nickInChannel'])
	
	def geoip(self, irc, msg, args, ip):
		record = self._record_by_addr(ip)
		if record:
			if 'city' in record:
				reply = u'%s (%s, %s)' % (ip, record['country_code'], record['city'])
			else:
				reply = u'%s (%s)' % (ip, record['country_code'])
		else:
			reply = 'Da stimmt etwas nicht!'
		irc.reply(reply)
		
	geoip = wrap(geoip, ['ip'])
	
	def _record_by_addr(self, ip):
		gi = pygeoip.GeoIP('/usr/share/rfk/var/GeoLiteCity.dat')
		
		try:
			return gi.record_by_addr(ip)
		except:
			return False
			
	def _checkCPO(self, irc, msg):
		if not irc.isChannel(msg.args[0]):
			irc.reply("Muss in einem Kanal gesendet werden!")
			return False
		elif msg.nick not in irc.state.channels[msg.args[0]].ops:
			irc.reply("Als ob!")
			return False
		elif irc.nick not in irc.state.channels[msg.args[0]].ops:
			irc.reply("%s braucht op ;_;" % irc.nick)
			return False
		else:
			return True
	
	def _numToDottedQuad(self, n):
		
		d = 256 * 256 * 256
		q = []
		while d > 0:
			m,n = divmod(n,d)
			q.append(str(m))
			d = d/256
		return '.'.join(q)

Class = OHL


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

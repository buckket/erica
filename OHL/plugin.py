###
# Copyright (c) 2011-2015, buckket
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

from random import randint

import socket
import time
import GeoIP


class OHL(callbacks.Plugin):
    """Oberste Heeresleitung."""
    
    threaded = True
    annoy = []
    annoyChannels = ['#krautchan']
    annoyText = [u'hai {0} :3',
        u'oh hai {0}, du hier? :3',
        u'hey {0} :3',
        u'hey {0}!',
        u'huhu {0} :3',
        u'harro {0} :3',
        u'moin {0} :3',
        u'auch: hai {0}',
        u'hai {0}',
        u'hi {0}',
        u'{0}!',
        u'oh, {0}!',
        u'Hallo, {0}. :3']
    
    def doJoin(self, irc, msg):
        
        # autoGhost onJoin
        if(self.registryValue('ownerNick') == msg.nick):
            self._autoGhost(irc, msg)

        if msg.args[0] in self.annoyChannels:
            if msg.nick in self.annoy:
                tmpl = self.annoyText[randint(0,len(self.annoyText)-1)]
                tmpl = tmpl.format(msg.nick)
                def annoy():
                    irc.queueMsg(ircmsgs.privmsg(msg.args[0], tmpl.encode('utf-8')))
                schedule.addEvent(annoy, time.time()+randint(1,30))
    
    def doNick(self, irc, msg):
        #autoGhost onNickchange
        if(self.registryValue('ownerNick') == msg.args[0]):
            self._autoGhost(irc, msg)

    def shoa(self, irc, msg, args):
        """

        Shoa ist anberaumt
        """
        
        if(self._checkCPO(irc, msg)):
            
            nicks = []
            nick4 = []
            
            def unlimit():
                irc.queueMsg(ircmsgs.unlimit(msg.args[0], 0))
                
            irc.queueMsg(ircmsgs.limit(msg.args[0], 1))  
            schedule.addEvent(unlimit, time.time() + 3*60)
            
            for nick in irc.state.channels[msg.args[0]].users:
                if nick not in irc.state.channels[msg.args[0]].ops:
                    nicks.append(nick)
            
            i = 0
            for nick in nicks:
                i = i+1
                nick4.append(nick)
                if (len(nick4) >= 4):
                    irc.queueMsg(ircmsgs.kicks(msg.args[0], nicks, 'Reichskristallnacht'))
                    nick4 = []
                elif ((len(nicks) - i) < 4):
                    irc.queueMsg(ircmsgs.kicks(msg.args[0], nicks, 'Reichskristallnacht'))
                
            irc.noReply()
                
    def k(self, irc, msg, args, nicks):
        """[user] ... [user]

        Rauswurf mit Zeitverbannung
        """

        if(self._checkCPO(irc, msg)):
            
            hostmasks = []
            
            for nick in nicks:
                prefix = irc.state.nickToHostmask(nick)
                user = ircutils.userFromHostmask(prefix)
                host = ircutils.hostFromHostmask(prefix)
            
                hostmask = '*!*@%s' % host
                hostmasks.append(hostmask)
            
            irc.queueMsg(ircmsgs.bans(msg.args[0], hostmasks))
            irc.queueMsg(ircmsgs.kicks(msg.args[0], nicks, 'Your behavior is not conducive to the desired environment.'))
            
            def unban():
                irc.queueMsg(ircmsgs.unbans(msg.args[0], hostmasks))
            
            schedule.addEvent(unban, time.time() + 900)
            
        irc.noReply()
            
    k = wrap(k, [many('nickInChannel')])

    #geoip
    def geoip(self, irc, msg, args, ip):
        """<IP>

        Zeigt GeoIP Informationen zu <IP> an
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

        Wandelt 8-Bit-Hexstring in IP um und gibt GeoIP Informationen aus
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

        Wandelt <hostname> in IP um und gibt GeoIP Informationen aus
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

        Wandelt <ip> in hostname um und gibt GeoIP Informationens aus
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
    
    
    def _autoGhost(self, irc, msg):
        if(msg.host != self.registryValue('ownerHost')):
            irc.queueMsg(ircmsgs.privmsg('NickServ', 'GHOST %s %s' % (self.registryValue('ownerNick'),self.registryValue('ownerPass'))))
    
    def _record_by_addr(self, ip):
        gi = GeoIP.open(self.registryValue('geoipdb'), GeoIP.GEOIP_STANDARD)
        try:
            return gi.record_by_addr(ip)
        except:
            return False
            
    def _geoip_city_check(self, record):
            if 'city' in record and 'country_code' in record:
                return u'%s, %s' % (unicode(record['country_code'].lower(), 'iso-8859-1'), unicode(record['city'], 'iso-8859-1'))
            else:
                return u'%s' % (unicode(record['country_code'], 'iso-8859-1'))
                
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

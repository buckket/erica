###
# Copyright (c) 2014-2016, buckket
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

import supybot.callbacks as callbacks
import supybot.ircutils as ircutils
import supybot.plugins as plugins
import supybot.schedule as schedule
import supybot.utils as utils
from supybot.commands import *

from pyquake3 import PyQuake3


class Quake(callbacks.Plugin):
    """Q3 Arena server information plugin."""

    def __init__(self, irc):
        self.__parent = super(Quake, self)
        self.__parent.__init__(irc)

        self.players = set()

        def poll_event():
            """Poll Q3 server for player information."""
            server = self._query_server()
            if server:
                players_new = set([player.name for player in server.players])
                players_connected = players_new - self.players
                if players_connected:
                    announce = u'%s: %s connected' % (
                        server.vars['sv_hostname'], self._natural_join(players_connected))
                    self._announce(irc, announce)
                players_disconnected = self.players - players_new
                if players_disconnected:
                    announce = u'%s: %s disconnected' % (
                        server.vars['sv_hostname'], self._natural_join(players_disconnected))
                    self._announce(irc, announce)
                self.players = players_new
            else:
                self.players = set()

        # remove any old events
        if 'Quake.pollStatus' in schedule.schedule.events:
            schedule.removePeriodicEvent('Quake.pollStatus')

        # register event
        if self.registryValue('enablePolling'):
            schedule.addPeriodicEvent(
                poll_event,
                self.registryValue('pollingInterval'),
                name='Quake.pollStatus'
            )

    # plugin destructor
    def die(self):
        # remove any old events
        if 'Quake.pollStatus' in schedule.schedule.events:
            schedule.removePeriodicEvent('Quake.pollStatus')
        self.__parent.die()

    @staticmethod
    def _natural_join(lst):
        l = len(lst)
        if l <= 2:
            return ' and '.join(lst)
        elif l > 2:
            first = ', '.join(lst[0:-1])
            return '%s %s %s' % (first, 'and', lst[-1])

    def _query_server(self):
        """Query Q3 server via pyquake3."""
        server = PyQuake3(self.registryValue('queryURL'))
        try:
            server.update()
        except Exception, e:
            log.error('Quake.query_server: %s' % repr(e))
            return None
        return server

    def _announce(self, irc, message):
        message = u'%s %s' % (self.registryValue('announcePrefix'), message)
        message = ircutils.safeArgument(message)
        for channel in irc.state.channels:
            if self.registryValue('announce', channel):
                irc.queueMsg(ircmsgs.privmsg(channel, message))

    def q3(self, irc, msg, args):
        """Returns Q3 Arena server information."""
        server = self._query_server()
        if server:
            reply = u'%s: running map %s with %s player(s)' % (server.vars['sv_hostname'],
                                                               server.vars['mapname'], len(server.players))
            if server.players:
                reply += u' [ %s ]' % self._natural_join(list(player.name for player in server.players))
            irc.reply(reply)
        else:
            irc.reply(u'Failed to query server.')

Class = Quake

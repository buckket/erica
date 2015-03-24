# -*- coding: utf-8 -*-

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

import time
import re


class Reminder(callbacks.Plugin):
    """Remind me, mighty Bot."""

    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(Reminder, self)
        self.__parent.__init__(irc)
        
        self.maxReminds = 10
        self.curReminds = 0
                
        self.maxTime = 60*60*24


    def remind(self, irc, msg, args, rtime, reason):
        """<time> [<reason>]

        Reminds user in <time>, because of <reason>
        """
        
        
        def rEvent():
            self.curReminds -= 1
            if reason:
                reply = u"[Reminder] %s! %s (%s)" % (msg.nick, unicode(reason, 'utf-8'), rtime)
            else:
                reply = u"[Reminder] %s! (%s)" % (msg.nick, rtime)
            irc.queueMsg(ircmsgs.privmsg(msg.args[0], reply.encode('utf-8')))
        
        rseconds = 0
        rtime = rtime.lower()
                
        # hours
        result = re.search(r"(\d{1,2})h", rtime)
        if result:
            rseconds += int(result.group(1)) * (60*60)
        #minutes
        result = re.search(r"(\d{1,2})m", rtime)
        if result:
            rseconds += int(result.group(1)) * 60
        #minutes
        result = re.search(r"(\d{1,2})s", rtime)
        if result:
            rseconds += int(result.group(1))
            
        if self.curReminds >= self.maxReminds:
            reply = u"Es sind bereits (%d/%d) Erinnerungen aktiv" % (self.curReminds, self.maxReminds)
        elif rseconds >= self.maxTime:
            reply = u"Die Erinnerung (%s) liegt zu weit in der Zukunft" % rtime
        elif rseconds == 0:
            reply = u"Ungültige Eingabe"
        else:
            rseconds = time.time() + rseconds
            schedule.addEvent(rEvent, rseconds)
            reply = u"Erinnerung hinzugefügt"
            self.curReminds += 1
            
        
        irc.reply(reply.encode('utf-8'))

    remind = wrap(remind, ['somethingWithoutSpaces', optional('text')])
        
        
Class = Reminder

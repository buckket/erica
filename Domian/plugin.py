# -*- coding: utf-8 -*-



###
# Copyright (c) 2012, MrLoom
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

from time import mktime
from datetime import datetime
import feedparser


class Domian(callbacks.Plugin):
    """Add the help for "@plugin help Domian" here
    This should describe *how* to use this plugin."""
    
    threaded = True

    def domian(self, irc, msg, args):
        now = datetime.now()
        feed = feedparser.parse('http://nachtlager.de/go/de/feed/week')
        nextshow = None
        
        for show in feed.entries:
            showStart = datetime.fromtimestamp(mktime(show.date_parsed)).replace(hour=1)
            showEnd = datetime.fromtimestamp(mktime(show.date_parsed)).replace(hour=2)
            show['showstart'] = showStart
            
            if showStart < now and showEnd > now:
                nextshow = show
                nextshow['onair'] = True
            else:
                if showStart > now:
                    if nextshow is None:
                        nextshow = show
                        nextshow['onair'] = False
                    else:
                        if showStart < nextshow['showstart']:
                            nextshow = show
                            nextshow['onair'] = False
        try:
            if nextshow['onair']:
                reply = u'Domian läuft gerade. (%s)' % nextshow.description
            else:
                reply = u'Nächste Sendung am %s (%s)' % (nextshow['showstart'].strftime('%d.%m.%Y um %H:%M'), nextshow.description)
        except:
            reply = u'Noch keine Daten vorhanden!'
            
        irc.reply(reply.encode('utf-8'))
        
    domian = wrap(domian)


Class = Domian


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

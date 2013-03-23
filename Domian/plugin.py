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

from time import mktime, time
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
            showStart = datetime.fromtimestamp(mktime(show.published_parsed)).replace(hour=1)
            showEnd = datetime.fromtimestamp(mktime(show.published_parsed)).replace(hour=2)
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
                reply = u'Domian läuft gerade. (%s) - http://www.wdr.de/wdrlive/media/einslive.m3u' % nextshow.description
            else:
                starts_in = formatTimespan(int(mktime(nextshow['showstart'].timetuple()) - time()))
                reply = u'Nächste Sendung am %s (%s) - in %s' % (nextshow['showstart'].strftime('%d.%m.%Y um %H:%M'), nextshow.description, starts_in)
        except:
            reply = u'Noch keine Daten vorhanden!'
            
        irc.reply(reply.encode('utf-8'))
        
    domian = wrap(domian)


Class = Domian


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


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

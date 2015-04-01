###
# Copyright (c) 2010-2015, buckket
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
import supybot.ircmsgs as ircmsgs
import supybot.ircdb as ircdb

from random import choice

import json
import requests


class KC(callbacks.Plugin):
    """Misc functionality, related to KC or even other Imageboards."""

    def jn(self, irc, msg, args):
        """

        Randomly choose 'Ja' or 'Nein'
        """

        irc.reply(choice(('Ja', 'Nein')))

    def yn(self, irc, msg, args):
        """

        Randomly choose 'Yes' or 'No'
        """

        irc.reply(choice(('Yes', 'No')))

    def choose(self, irc, msg, args, options):
        """<options>

        Randomly chooses one element of <options>
        """

        try:
            reply = choice(options)
        except:
            reply = u'Depp.'
        finally:
            irc.reply(reply)

    choose = wrap(choose, [many('anything')])

    def _channel_info(self,  channel):
        r = requests.get('https://gdata.youtube.com/feeds/api/users/{}/uploads?v=2&alt=json&max-results=1'.format(channel))
        data = json.loads(r.content)
        url = 'https://www.youtube.com/watch?v=%s' % data['feed']['entry'][0]['media$group']['yt$videoid']['$t']
        title = data['feed']['entry'][0]['title']['$t']
        views = data['feed']['entry'][0]['yt$statistics']['viewCount'] if 'yt$statistics' in data['feed']['entry'][0] else 0
        likes = float(data['feed']['entry'][0]["yt$rating"]['numLikes']) if "yt$rating" in data['feed']['entry'][0] else 0
        dislikes = float(data['feed']['entry'][0]["yt$rating"]['numDislikes']) if "yt$rating" in data['feed']['entry'][0] else 0
        if (likes + dislikes) > 0:
            rating = '%s%%' % round((likes/(likes+dislikes))*100)
        else:
            rating = 'NaN'
        message = 'Title: %s, Views: %s, Rating: %s -- %s' % (ircutils.bold(title), ircutils.bold(views), ircutils.bold(rating), url)
        message = message.encode("utf-8", "replace")
        return message

    def drache(self, irc, msg, args):
        """

        Neustes Video von Drachenlord1510
        """

        message = self._channel_info('drachenlord1510')
        irc.reply(message)

    def drachenvlog(self, irc, msg, args):
        """

        Neustes Video von Drachenvlog1510
        """

        message = self._channel_info('drachenvlog1510')
        irc.reply(message)

    def ludger(self, irc, msg, args):
        """

        Neustes Video von Ludger Winter
        """

        message = self._channel_info('UCNqljVvVXoMv9T7dPTvg0JA')
        irc.reply(message)

    def schmacko(self, irc, msg, args):
        """

        Neustes Video von ProfSchmackofatz
        """

        message = self._channel_info('ProfSchmackofatz')
        irc.reply(message)
    

Class = KC

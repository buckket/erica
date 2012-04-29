###
# Copyright (c) 2007, Benjamin Rubin
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

import supybot.conf as conf
import supybot.log as log
from urlparse import urlparse
from datetime import timedelta
import re
import json
import requests

class Supytube(callbacks.Plugin):
    """Add the help for "@plugin help Supytube" here
    This should describe *how* to use this plugin."""
    threaded = True

    def doPrivmsg(self, irc, msg):
        if(self.registryValue('enable', msg.args[0])):
            # If this is a youtube link, commence lookup
            if(msg.args[1].find("youtube") != -1 or msg.args[1].find("youtu.be") != -1):
                youtube_pattern = re.compile('(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\?=\-]*)(&(amp;)?[\w\?=]*)?')
                
                m = youtube_pattern.search(msg.args[1]);
                if(m):
                    r = requests.get('http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json' % m.group(1))
                    data = json.loads(r.content)
                    likes = float(data['entry']["yt$rating"]['numLikes'])
                    dislikes = float(data['entry']["yt$rating"]['numDislikes'])
                    rating = (likes/(likes+dislikes))*100
                    message = 'Title: %s, Views: %s, Rating: %s%%' % (ircutils.bold(data['entry']['title']['$t']), ircutils.bold(data['entry']['yt$statistics']['viewCount']), ircutils.bold(round(float(rating))))
                    message = message.encode("utf-8", "replace")
                    irc.queueMsg(ircmsgs.privmsg(msg.args[0], message))
                
            if(msg.args[1].find("vimeo") != -1):
                vimeo_pattern = re.compile('vimeo.com/(\\d+)')
                m = vimeo_pattern.search(msg.args[1]);
                if(m):
                    r = requests.get("http://vimeo.com/api/v2/video/%s.json" % m.group(1))
                    data = json.loads(r.content)
                    message = 'Title: %s, Views: %s, Likes: %s' % (ircutils.bold(data[0]['title']), ircutils.bold(data[0]['stats_number_of_plays']), ircutils.bold(data[0]['stats_number_of_likes']))
                    message = message.encode("utf-8", "replace")
                    irc.queueMsg(ircmsgs.privmsg(msg.args[0], message))

Class = Supytube

###
# Copyright (c) 2007, Benjamin Rubin
# Copyright (c) 2015, buckket
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

from apiclient.discovery import build
from oauth2client.file import Storage

from urlparse import urlparse
from datetime import timedelta

import re
import json
import httplib2
import requests


class Supytube(callbacks.Plugin):
    """This plugin announces the title and other relevant information
    about any Youtube or Vimeo link that is said in a channel."""
    threaded = True

    def doPrivmsg(self, irc, msg):
        if(self.registryValue('enable', msg.args[0])):
            # If this is a youtube link, commence lookup
            if(msg.args[1].find("youtube") != -1 or msg.args[1].find("youtu.be") != -1):
                youtube_pattern = re.compile('(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\?=\-]*)(&(amp;)?[\w\?=]*)?')

                m = youtube_pattern.search(msg.args[1]);
                if(m):
                    storage = Storage(self.registryValue("oauth2CredentialFile")
                    creds = storage.get()
                    if creds is None or creds.invalid:
                        #failed to get credentials...
                        raise RuntimeError("failed to get google api credentials")
                    youtube = build('youtube', 'v3', http=creds.authorize(httplib2.Http()))
                    stats = youtube.videos().list(part="statistics", id=m).execute()
                    views = stats['items']['viewCount']
                    likes = float(stats['items']['likeCount'])
                    dislikes = float(stats['items']['dislikeCount'])
                    titleobj = youtube.videos().list(part="snippet", id=m).execute()
                    creds.store()
                    title = titleobj['items'][0]['snippet']['title']
                    if (likes + dislikes) > 0:
                        rating = '%s%%' % round((likes/(likes+dislikes))*100)
                    else:
                        rating = 'NaN'
                    message = 'Title: %s, Views: %s, Rating: %s' % (ircutils.bold(title), ircutils.bold(views), ircutils.bold(rating))
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

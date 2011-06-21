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
import urllib

import xml.sax

class YoutubeHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.inTitle = 0
        self.inAuthor = 0
        self.inName = 0
        self.title = ''
        self.author = ''
        self.rating = ''
        self.rating_count = ''
        self.views = ''
        self.duration = ''
       
        
    def startElement(self, name, attributes):
        if(name == 'title'):
            self.title = ''
            self.inTitle = 1
        if(name == 'author'):
            self.author = ''
            self.inAuthor = 1
        if(name == 'name'):
            self.inName = 1
        if(name == 'gd:rating'):
            self.rating_count = attributes.getValue('numRaters')
          
            # Compute percentage rating based on the average rating and the maximum rating 
            self.rating = ( float(attributes.getValue('average')) / float(attributes.getValue('max')) ) * 100
            self.inRatingCount = 1
        if(name == 'yt:statistics'):
            self.views = attributes.getValue('viewCount')
            self.inViews = 1
        if(name == 'yt:duration'):
            self.duration = timedelta(seconds = float(attributes.getValue('seconds')))
            
    def characters(self,data):
        if(self.inTitle):
            self.title += data
        if(self.inAuthor and self.inName):
            self.author += data

    def endElement(self,name):
        if(name == 'title'):
            self.inTitle=0
        if(name == 'author'):
            self.inAuthor = 0
        if(name == 'name'):
            self.inName = 0       

class Supytube(callbacks.Plugin):
    """Add the help for "@plugin help Supytube" here
    This should describe *how* to use this plugin."""
    threaded = True

    def doPrivmsg(self, irc, msg):
	    if(self.registryValue('enable',msg.args[0])):
		# If this is a youtube link, commence lookup
		if(msg.args[1].find("youtube") != -1):
		    for word in msg.args[1].split(' '):
			if(word.find("youtube") != -1):
			    videoid = urlparse(word)[4].split('=')[1].split('&')[0]

			    f = urllib.urlopen('http://gdata.youtube.com/feeds/videos/%s' % (videoid))
			    parser = xml.sax.make_parser()
			    handler = YoutubeHandler()
			    parser.setContentHandler(handler)
			    parser.parse(f)
			    
			    #log.critical('Title: %s' % handler.title)
			    #log.critical('Author: %s' % handler.author)
			    #log.critical('Rating: %s' % handler.rating)
			    #log.critical('Views: %s' % handler.views)
			    #log.critical('Rating Count: %s' % handler.rating_count)
			    #log.critical('Duration: %s' % handler.duration)
			    
			    # check for empty rating and views
			    handler.rating = handler.rating if handler.rating else 0
			    handler.views = handler.views if handler.views else 0
			    
			    message = 'Title: %s, Views: %s, Rating: %s%%' % (ircutils.bold(handler.title), ircutils.bold(handler.views),ircutils.bold(round(float(handler.rating))))
			    #message = unicode( message, "utf-8")
			    message = message.encode("utf-8", "replace")
			    irc.queueMsg(ircmsgs.privmsg(msg.args[0],message))
                
            
            

Class = Supytube

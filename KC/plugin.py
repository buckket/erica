# -*- coding: utf-8 -*-
###
# Copyright (c) 2010, MrLoom
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

from urlparse import urlparse
from urlparse import urlunparse

import os
import re

class KC(callbacks.Plugin):
	"""Add the help for "@plugin help KC" here
	This should describe *how* to use this plugin."""
	threaded = True
	
	def doPrivmsg(self, irc, msg):
		if(self.registryValue('urlmodify',msg.args[0])):
			
			toModify = {
			'what.cd' : { 'http' : 'what.cd', 'https' : 'ssl.what.cd'},
			'awesome-hd.net' : { 'http' : 'awesome-hd.net', 'https' : 'ssl.awesome-hd.net'}
			}
			
			tmp = []
			
			for name in toModify:
				if(msg.args[1].find(name) != -1):
					for word in msg.args[1].split(' '):
						if(word.find(name) != -1):
							url = urlparse(word)
							if (url[0] == 'http'):
								url = urlunparse(('https', toModify[name]['https'], url[2], url[3], url[4], url[5]))
								tmp.append(url)
							if (url[0] == 'https'):
								url = urlunparse(('http', toModify[name]['http'], url[2], url[3], url[4], url[5]))
								tmp.append(url)
			if len(tmp) > 0:
				tmp.reverse()
				reply = ' '.join(tmp)
				irc.queueMsg(ircmsgs.privmsg(msg.args[0], reply))

	def dump(self, irc, msg, args, text):
		"""<kcurl>
		
		Speichert einen Faden von KC
		"""
		match = re.match(r"http:\/\/krautchan\.net\/(.*)\/thread-(.*)\.html", text)
		irc.reply("Versuche Faden " + match.group(2) + " von /" + match.group(1) + "/ zu speichern.")
		os.system("/var/www/krautdmp/krautdmpSingle.pl " + text)
		if(os.path.isfile("/var/www/krautdmp/" + match.group(1) + "-" + match.group(2) + "/" + match.group(1) + "-" + match.group(2) + ".zip")):
			irc.reply("Fertig: http://94.23.239.51/krautdmp/" + match.group(1) + "-" + match.group(2) + "/" + match.group(1) + "-" + match.group(2) + ".zip")
		else:
			irc.reply("Fehler!")
		
	dump = wrap(dump, ['text'])


Class = KC


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

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
import supybot.schedule as schedule
import supybot.ircmsgs as ircmsgs

import twitter


class Twitter(callbacks.Plugin):
	"""Get teh shit on TwittAAA"""

	def __init__(self, irc):
		self.__parent = super(Twitter, self)
		self.__parent.__init__(irc)
		self.lastid = 0
		
		
	def twitter(self, irc, msg, args):
		"""takes no arguments

		Return the TwitterAccount of the Bot
		"""
		irc.reply("http://twitter.com/EricaHartmann_")
	twitter = wrap(twitter)

	
	def post(self, irc, msg, args, text):
		"""<text>

		Text to post on Twitter.
		"""
		
		nick = msg.nick
		len_message = 140 - len(" (" + nick + ")")
		message = utils.str.ellipsisify(text, len_message)
		message = "%s (%s)" % (message, nick)
		message = unicode( message, "utf-8" )
		
		api = self._get_twitter_api()

		status = api.PostUpdate(message.encode('utf8'))
		irc.replySuccess()
			
	post = wrap(post, ['text'])

	
	def event(self, irc, msg, args, switch):
		"""<on/off>
		
		Turn events on or off.
		"""
		
		def getAt():
			if self.lastid == 0:
				silence = True
			else:
				silence = False
			
			api = self._get_twitter_api()
			msgs = api.GetMentions(since_id=self.lastid)

			for messageInst  in msgs:
				message = "[Twitter] %s (%s) zwitscherte mir: %s" % (messageInst.user.name, messageInst.user.screen_name, messageInst.text.lstrip("@EricaHartmann_"))
				message = message.encode("utf-8", "replace")

				if not silence:
					for channel in irc.state.channels:
						if (self.registryValue('announce', channel)):
							irc.queueMsg(ircmsgs.privmsg(channel, message))
						
				if messageInst.id > self.lastid:
					self.lastid = messageInst.id

		if switch == True:
			try:
				schedule.addPeriodicEvent(getAt, 60, name="getAt")
				irc.replySuccess()
			except AssertionError:
				irc.reply("Failed. Maybe it is already on.")		
		elif switch == False:
			try:
				schedule.removePeriodicEvent("getAt")
				irc.replySuccess()
			except KeyError:
				irc.reply("Failed. Maybe it is already off.")
			
	event = wrap(event, ['boolean', 'admin'])


	def _get_twitter_api(self):
		return twitter.Api(consumer_key=self.registryValue('consumerKey'), consumer_secret=self.registryValue('consumerSecret'), access_token_key=self.registryValue('accessKey'),access_token_secret=self.registryValue('accessSecret'))


Class = Twitter


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

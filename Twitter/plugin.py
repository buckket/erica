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

import re
import tweepy
import HTMLParser


class Twitter(callbacks.Plugin):
    """Hello. This is Twitter."""

    def __init__(self, irc):
        self.__parent = super(Twitter, self)
        self.__parent.__init__(irc)


    def twitter(self, irc, msg, args):
        """

        Returns the Twitter profile
        """

        irc.reply(u"http://twitter.com/{}".format(self.registryValue('botNick')))

    twitter = wrap(twitter)


    def _tweet(self, irc, text, tweet=None):
        try:
            api = self._get_twitter_api()
            if tweet:
                status_id = self._get_status_id(tweet)
                if status_id:
                    if not text.startswith('@'):
                        username = api.get_status(status_id).user.screen_name
                        text = u"@{} {}".format(username, text)
                    message = utils.str.ellipsisify(text, 140)
                    status = api.update_status(status=message,  in_reply_to_status_id=status_id)
                else:
                    irc.reply(u"Du musst mir schon einen Tweet geben, auf den sich der Unsinn beziehen soll.")
                    return
            else:
                message = utils.str.ellipsisify(text, 140)
                status = api.update_status(status=message)
            irc.reply(u"https://twitter.com/{bot}/status/{status_id}".format(bot=self.registryValue('botNick'),
                                                                             status_id=status.id))
        except tweepy.TweepError as e:
            irc.reply(u"Das hat nicht geklappt.")


    def tweet(self, irc, msg, args, text):
        """<text>

        Tweets <text>
        """

        self._tweet(irc, text)

    tweet = wrap(tweet, ["text"])


    def reply(self, irc, msg, args, tweet, text):
        """<tweet url or id> <text>

        Tweets <text> as reply
        """

        self._tweet(irc, text, tweet)

    reply = wrap(reply, ["somethingWithoutSpaces", "text"])


    def fav(self, irc, msg, args, tweet):
        """<tweet url or id>

        Favs tweet
        """

        status_id = self._get_status_id(tweet)
        if status_id:
            try:
                api = self._get_twitter_api()
                api.create_favorite(status_id)
                irc.reply(u"Alles klar.")
            except tweepy.TweepError as e:
                irc.reply(u"Das hat nicht geklappt.")
    fav = wrap(fav, ["somethingWithoutSpaces"])


    def rt(self, irc, msg, args, tweet):
        """<tweet url or id>

        RTs tweet
        """
        status_id = self._get_status_id(tweet)
        if status_id:
            try:
                api = self._get_twitter_api()
                api.retweet(status_id)
                irc.reply(u"Alles klar.")
            except tweepy.TweepError as e:
                irc.reply("Das hat nicht geklappt.")
    rt = wrap(rt, ['somethingWithoutSpaces'])


    def doPrivmsg(self, irc, msg):
        if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
            return
        if ircutils.isChannel(msg.args[0]):
            if msg.args[1].find("twitter") != -1:
                status_id = self._get_status_id(msg.args[1], search=True)
                if status_id:
                    try:
                        api = self._get_twitter_api()
                        tweet = api.get_status(status_id)
                        text = tweet.text.replace("\n", " ")
                        text = HTMLParser.HTMLParser().unescape(text)
                        message = u"Tweet von @{}: {}".format(tweet.user.screen_name, text)
                        message = ircutils.safeArgument(message)
                        irc.queueMsg(ircmsgs.privmsg(msg.args[0], message))
                    except tweepy.TweepError as e:
                        return


    def _get_twitter_api(self):
        auth = tweepy.OAuthHandler(self.registryValue("consumerKey"),
                                   self.registryValue("consumerSecret"))
        auth.set_access_token(self.registryValue("accessKey"),
                              self.registryValue("accessSecret"))
        return tweepy.API(auth)


    def _get_status_id(self, tweet, search=False):
        regexp = re.compile(r"(?:https?://(?:[^.]+.)?twitter.com/(?P<username>[^/]*)/status(?:es)?/)?(?P<status_id>\d+)")
        if search:
            m = re.search(regexp, tweet)
        else:
            m = re.match(regexp, tweet)
        if m and m.group("status_id"):
            return m.group("status_id")
        else:
            return False


Class = Twitter

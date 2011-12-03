###
# Copyright (c) 2011, MrLoom
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

import supybot.log as log

import urllib
import urllib2
import json
import re


class Translate(callbacks.Plugin):
    """Bing Translate"""
    
    def __init__(self, irc):
        self.__parent = super(Translate, self)
        self.__parent.__init__(irc)

        self.allowedLanguages = self._updateLanguages()


    def trans(self, irc, msg, args, text):
        parse, transFrom, transTo, transText = self._parseInput(text)
        
        if (parse):
            if(self._validateInput([transFrom, transTo])):
                
                if(transFrom):
                    result = self._translateQuery('Translate',
                        { 'text' : transText, 'from' : transFrom, 'to' : transTo })
                else:
                    result = self._translateQuery('Translate',
                        { 'text' : transText, 'to' : transTo })
                    transFrom = self._translateQuery('Detect', {'text' : transText })       
                
                reply = u"<%s-%s> %s" % (transFrom, transTo, result)
            else:
                reply = u"Die Sprache kann ich leider nicht!"
        else:
            reply = u"Eingabefehler!"
        
        irc.reply(reply.encode('utf-8'))
    trans = wrap(trans, ['text'])


    def languages(self, irc, msg, args):
        languages = []
        for language in self.allowedLanguages:
            languages.append("%s" % language)
        irc.reply(', '.join(languages).encode('utf-8'))
    languages = wrap(languages)


    def _parseInput(self, text):
        m = re.match(r"(([a-z]{2})-([a-z]{2}))?\s?(.*)", text)
        if (m):
            transFrom, transTo, transText = m.groups()[1:]
        else:
            return [False, None, None, None]
            
        if transTo == None:
            transTo = self.registryValue('defaultLang')
            
        return [True, transFrom, transTo, transText]


    def _validateInput(self, languages):
        for language in languages:
            if language is not None:
                if language not in self.allowedLanguages:
                    return False
        return True


    def _translateQuery(self, function, parameters={}):
        
        if (self.registryValue('appId') == ''):
              log.error('Translate: Set your appId and restart the plugin')
              return
        log.debug('Translate.query: %s' % (repr(parameters)))

        if (self.registryValue('httpProxy') != ''):
            opener = urllib2.build_opener(
                urllib2.ProxyHandler({'http': self.registryValue('httpProxy')}))
        else:
            opener = urllib2.build_opener()

        response = opener.open(self.registryValue('queryURL') + function + '?'+
            'appId=' + self.registryValue('appId') + '&' +
            urllib.urlencode(parameters))
            
        try:
            data = json.loads(json.dumps(response.read()))
            data = json.loads(data[1:])
            log.debug('Translate.reply: %s' % repr(data))
            return(data)
        except:
            log.error('Translate.query error')
            return(None)


    def _updateLanguages(self):
        result = self._translateQuery('GetLanguagesForTranslate', {})
        return result


Class = Translate


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

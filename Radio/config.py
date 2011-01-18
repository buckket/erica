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

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Radio', True)

Radio = conf.registerPlugin('Radio')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Radio, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))
conf.registerGlobalValue(Radio, 'queryURL',
    registry.String('', """Radio server query URL"""))
conf.registerGlobalValue(Radio, 'queryPass',
    registry.String('', """Radio server query pass""", private=True))
conf.registerGlobalValue(Radio, 'httpProxy',
    registry.String('', """HTTP proxy to use for radio queries""", private=True))
conf.registerGlobalValue(Radio, 'enablePolling',
    registry.Boolean(False, """Enable polling of radio server"""))
conf.registerGlobalValue(Radio, 'pollingInterval',
    registry.PositiveInteger(15, """Interval at which to poll the radio server"""))
conf.registerChannelValue(Radio, 'announce',
    registry.Boolean(False, """Announce radio status on this channel"""))
conf.registerGlobalValue(Radio, 'monitor',
    registry.Boolean(False, """Monitor joins and parts"""))
conf.registerGlobalValue(Radio, 'monitorChannel',
    registry.String('', """Select channel to monitor"""))
conf.registerGlobalValue(Radio, 'autovoice',
    registry.Boolean(False, """Voice streamer"""))
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

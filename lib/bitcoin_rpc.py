'''
    Implements simple interface to bitcoind's RPC.
'''

import simplejson as json
import base64
from twisted.internet import defer
from twisted.web import client

import stratum.logger
log = stratum.logger.get_logger('bitcoin_rpc')

gbt_known_rules = ["segwit"]

class BitcoinRPC(object):

    def __init__(self, host, port, username, password):
        self.bitcoin_url = 'http://%s:%d' % (host, port)
        self.credentials = base64.b64encode(f"{username}:{password}")
        self.headers = {
            'Content-Type': 'text/json',
            'Authorization': f'Basic {self.credentials}',
        }

    def _call_raw(self, data):
        return client.getPage(
            url=self.bitcoin_url,
            method='POST',
            headers=self.headers,
            postdata=data,
        )

    def _call(self, method, params):
        return self._call_raw(json.dumps({
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
                'id': '1',
            }))

    @defer.inlineCallbacks
    def submitblock(self, block_hex):
        resp = (yield self._call('submitblock', [block_hex,]))
        if json.loads(resp)['result'] is None:
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    @defer.inlineCallbacks
    def getinfo(self):
         resp = (yield self._call('getinfo', []))
         defer.returnValue(json.loads(resp)['result'])

    @defer.inlineCallbacks
    def getblocktemplate(self):
        resp = (yield self._call('getblocktemplate', [{"rules": gbt_known_rules}]))
        defer.returnValue(json.loads(resp)['result'])

    @defer.inlineCallbacks
    def prevhash(self):
        resp = (yield self._call('getbestblockhash', []))
        try:
            defer.returnValue(json.loads(resp)['result'])
        except Exception as e:
            log.exception(f"Cannot decode prevhash {str(e)}")
            raise

    @defer.inlineCallbacks
    def validateaddress(self, address):
        resp = (yield self._call('validateaddress', [address,]))
        defer.returnValue(json.loads(resp)['result'])

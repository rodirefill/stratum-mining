from twisted.internet import reactor, defer
from stratum import settings

import util
from mining.interfaces import Interfaces

import stratum.logger
log = stratum.logger.get_logger('block_updater')

class BlockUpdater(object):
    '''
        Polls upstream's getinfo() and detecting new block on the network.
        This will call registry.update_block when new prevhash appear.

        This is just failback alternative when something
        with ./bitcoind -blocknotify will go wrong.
    '''

    def __init__(self, registry, bitcoin_rpc):
        self.bitcoin_rpc = bitcoin_rpc
        self.registry = registry
        self.clock = None
        self.schedule()

    def schedule(self):
        when = self._get_next_time()
        #log.debug("Next prevhash update in %.03f sec" % when)
        #log.debug("Merkle update in next %.03f sec" % \
        #          ((self.registry.last_update + settings.MERKLE_REFRESH_INTERVAL)-Interfaces.timestamper.time()))
        self.clock = reactor.callLater(when, self.run)

    def _get_next_time(self):
        return (
            settings.PREVHASH_REFRESH_INTERVAL
            - (Interfaces.timestamper.time() - self.registry.last_update)
            % settings.PREVHASH_REFRESH_INTERVAL
        )

    @defer.inlineCallbacks
    def run(self):
        update = False

        try:
            if self.registry.last_block:
                current_prevhash = "%064x" % self.registry.last_block.hashPrevBlock
            else:
                current_prevhash = None

            prevhash = yield self.bitcoin_rpc.prevhash()
            if prevhash and prevhash != current_prevhash:
                log.info(f"New block! Prevhash: {prevhash}")
                update = True

            elif Interfaces.timestamper.time() - self.registry.last_update >= settings.MERKLE_REFRESH_INTERVAL:
                log.info(f"Merkle update! Prevhash: {prevhash}")
                update = True

            if update:
                self.registry.update_block()

        except Exception:
            log.exception("UpdateWatchdog.run failed")
        finally:
            self.schedule()



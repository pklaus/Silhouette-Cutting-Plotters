#!/usr/bin/env python

import os, select, time, logging

import IPython

logger = logging.getLogger(name=__name__)

f = os.open('/dev/usb/lp0', os.O_RDWR)

def w(cmd):
    """ write to device """
    logger.debug('sending -> ' + repr(cmd))
    os.write(f, cmd)

def r(num=120, timeout=0.2):
    """ read from device """
    start = time.time()
    ret = None
    while True:
        if time.time() - start > timeout: break
        r, _, _ = select.select([f], [], [], 0)
        if f in r:
            ret = os.read(f, num)
            break
        time.sleep(0.01)
    logger.debug('received -> ' + repr(ret))
    return ret

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    IPython.embed()

#!/usr/bin/env python

from __future__ import print_function

import argparse, struct, os, logging
from datetime import datetime as dt

import dpkt

logger = logging.getLogger(name=__name__)

VERBOSE = False

URB_BULK_OUT = '\x01\x03'
URB_BULK_IN  = '\x82\x03'

STATUS_RQ = '\x1b\x05'
STATUS_OK = '0\x03'
STATUS_WORKING = '1\x03'

def mac_addr(mac_string):
    return ':'.join('%02x' % ord(b) for b in mac_string)

def ip_to_str(address):
    return socket.inet_ntop(socket.AF_INET, address)

def print_packets(pcap, target_file):
    last_payload, last_payload_in = None, None
    last_ts = dt.now()
    for timestamp, buf in pcap:
        try:
            assert len(buf) >= 27
            assert struct.unpack('<I', buf[23:27])[0] + 27 == len(buf)
        except:
            fmt = "The packet didn't pass the checks. Strange USB URB Packet?   {}"
            logger.warning(fmt.format(repr(buf)))
            continue
        kind = None
        kind = buf[21:23]
        payload = buf[27:]
        msg = ''
        if kind in (URB_BULK_OUT, URB_BULK_IN):
            ts = dt.utcfromtimestamp(timestamp)
            if VERBOSE: msg += 'Timestamp: {}  {:+.3f}\n'.format(ts, (ts - last_ts).total_seconds())
            last_ts = ts
        if kind == URB_BULK_OUT:
            if last_payload == payload and payload == STATUS_RQ:
                continue
            #print(repr(buf))
            #print(' '.join(['{:02X}'.format(ord(byte)) for byte in buf]))
            msg += 'cmd:   ' + repr(payload) + '\n'
            msg += ' (hex:  ' + ' '.join(['{:02X}'.format(ord(byte)) for byte in payload]) + '\n'
            target_file.write(payload)
            last_payload = payload
        if kind == URB_BULK_IN:
            if last_payload_in == payload and payload in (STATUS_OK, STATUS_WORKING):
                continue
            if VERBOSE:
                msg += 'response: ' + repr(payload) + '\n'
                msg += '    (hex:  ' + ' '.join(['{:02X}'.format(ord(byte)) for byte in payload]) + '\n'
            #target_file.write(payload) # We don't write incoming bytes to the binary output file
            last_payload_in = payload
        if msg: print(msg)

def main():
    """Open up a test pcap file and print out the packets"""
    global VERBOSE
    parser = argparse.ArgumentParser(description='Analyze pcap files')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('pcap_file', help='')
    parser.add_argument('target_file', nargs='?', help='')
    args = parser.parse_args()

    if args.verbose:
        VERBOSE = True
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    if not args.target_file: args.target_file = os.path.splitext(args.pcap_file)[0] + '.bin'

    with open(args.pcap_file) as fp:
        pcap = dpkt.pcap.Reader(fp)
        with open(args.target_file, 'wb') as target_file:
            print_packets(pcap, target_file)

if __name__ == '__main__':
    main()

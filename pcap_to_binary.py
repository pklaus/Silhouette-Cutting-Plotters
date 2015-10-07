#!/usr/bin/env python

from __future__ import print_function

import argparse, struct, os, logging
#import datetime, pdb

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
    for timestamp, buf in pcap:
        try:
            assert len(buf) >= 27
            assert struct.unpack('<I', buf[23:27])[0] + 27 == len(buf)
        except:
            fmt = "The packet didn't pass the checks. Strange USB URB Packet?   {}"
            logger.warning(fmt.format(buf))
            continue
        kind = None
        kind = buf[21:23]
        payload = buf[27:]
        if kind == URB_BULK_OUT:
            if last_payload == payload and payload == STATUS_RQ:
                continue
            #print('\nTimestamp: ', str(datetime.datetime.utcfromtimestamp(timestamp)))
            #print(repr(buf))
            #print(' '.join(['{:02X}'.format(ord(byte)) for byte in buf]))
            print('cmd:   ' + repr(payload))
            print(' (hex:  ' + ' '.join(['{:02X}'.format(ord(byte)) for byte in payload]))
            target_file.write(payload)
            last_payload = payload
        if kind == URB_BULK_IN:
            if last_payload_in == payload and payload in (STATUS_OK, STATUS_WORKING):
                continue
            if VERBOSE:
                print('response: ' + repr(payload))
                print('    (hex:  ' + ' '.join(['{:02X}'.format(ord(byte)) for byte in payload]))
            #target_file.write(payload) # We don't write incoming bytes to the binary output file
            last_payload_in = payload

def main():
    """Open up a test pcap file and print out the packets"""
    global VERBOSE
    parser = argparse.ArgumentParser(description='Analyze pcap files')
    parser.add_argument('--verbose', help='')
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

#!/usr/bin/env python

import re

CMD_KINDS = [
  {'code': '1B 04', 'name': 'initialize plotter',    'equals':  b'\x1b\x04' },
  {'code': '1B 05', 'name': 'status request',        'equals':  b'\x1b\x05' },
  {'code': 'TT',    'name': 'home the cutter',       'startswith': b'TT' },
  {'code': 'FG',    'name': 'query model / version', 'startswith': b'FG' },
  {'code': 'FW',    'name': 'media type',            'pattern': b'^FW(\d+)' },
  {'code': 'FC',    'name': 'cutter offset',         'pattern': b'^FC(\d+)' },
  {'code': 'FY',    'name': 'track enhancing',       'pattern': b'^FY(\d)' },
  {'code': 'FN',    'name': 'orientation',           'pattern': b'^FN(\d)' },
  {'code': 'FE0',   'name': '??',                    'equals':  b'FE0\x03' },
  {'code': 'FE0',   'name': '??',                    'equals':  b'FE0,0\x03' },
  {'code': 'FF',    'name': '??',                    'equals':  b'FF0,0,0\x03' },
  {'code': 'TB71',  'name': '??',                    'equals':  b'TB71\x03' },
  {'code': 'FA',    'name': 'begin page definition', 'equals':  b'FA\x03' },
  {'code': 'FU',    'name': 'page dimensions (h,w) w/o margin', 'pattern': b'^FU(\d+),(\d+)' },
  {'code': 'FM1',   'name': '??',                    'equals':  b'FM1\x03' },
  {'code': 'TB50',  'name': '??',                    'pattern': b'TB50,\d\x03' },
  {'code': 'FO0',   'name': 'feed the page out',     'equals':  b'FO0\x03' },
  {'code': 'FO',    'name': 'feed command?',         'pattern': b'^FO(\d+)' },
  {'code': '&start','name': 'data start',            'pattern': b'^&100,100,100,\\\\0,0,Z(\d+),(\d+),L0,FX(\d+),0\x03'},
  {'code': '&end',  'name': 'data end',              'pattern': b'^&1,1,1,TB50,0\x03'},
  {'code': '!',     'name': 'speed',                 'pattern': b'^!(\d+)' },
  {'code': 'L0',    'name': '??',                    'equals':  b'^L0\x03' },
  {'code': 'FX',    'name': 'force',                 'pattern': b'^FX(\d+)' },
  {'code': 'FX',    'name': 'force',                 'pattern': b'^FX(\d+),0' },
  {'code': '\\\\',  'name': 'border?',               'pattern': b'^\\\\(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'Z',     'name': 'dimensions?',           'pattern': b'^Z(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'M',     'name': 'move',                  'pattern': b'^M(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'D',     'name': 'draw',                  'pattern': b'^D(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'BZ',    'name': 'bezier',                'pattern': b'^BZ(\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+)\x03$' },
]

class Cmd(object):
    def __init__(self, cmd):
        self.cmd = cmd

class NotFound(Cmd):
    def __str__(self):
        return "Unknown Cmd: {}".format(self.cmd)

class GraphtecCmd(Cmd):

    def __init__(self, cmd, kind, groups=None):
        self.cmd = cmd
        self.kind = kind
        self.groups = groups

    @property
    def values(self):
        values = []
        if self.groups:
            for group in self.groups:
                float_val, int_val = float('nan'), None

                try: float_val = float(group)
                except: pass
                try: int_val = int(group)
                except: pass

                if type(float_val) == float and float_val == int_val: values.append(int_val)
                elif type(float_val) == float: values.append(float_val)
                elif int_val: values.append(int_val)
                else: values.append(group)
        return tuple(values)

    def __str__(self):
        desc = "Cmd: '{name}'".format(**self.kind)
        values = self.values
        if len(values) == 1:
            desc += " Value: {}".format(values[0])
        elif len(values):
            desc += " Values: {}".format(values)
        return desc

def parse_cmd(cmd):
    for cmd_kind in CMD_KINDS:
        if 'equals' in cmd_kind and cmd == cmd_kind['equals']:
             return GraphtecCmd(cmd, cmd_kind)
        if 'startswith' in cmd_kind and cmd.startswith(cmd_kind['startswith']):
             return GraphtecCmd(cmd, cmd_kind)
        if 'pattern' in cmd_kind:
             m = re.match(cmd_kind['pattern'], cmd)
             if m:
                 return GraphtecCmd(cmd, cmd_kind, groups=m.groups())
    return NotFound(cmd)
    

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('graphtec_input_file', type=argparse.FileType('rb'))
    args = parser.parse_args()
    content = args.graphtec_input_file.read()
    buff = b''
    commands = []
    for char in content:
        buff += bytes([char])
        if char & 0xF8 == 0:
            # Terminator char
            commands.append(buff)
            buff = b''
    for cmd in commands:
        pcmd = parse_cmd(cmd)
        if args.verbose: print(cmd)
        if type(pcmd) == NotFound: pass
        print(pcmd)

if __name__ == "__main__": main()


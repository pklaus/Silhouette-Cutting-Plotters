#!/usr/bin/env python

import re

def coord_pair_filter(groups):
    numbers = groups[0].decode('ascii').split(',')
    assert len(numbers) % 2 == 0
    return [float(num) for num in numbers]

def default_filter(groups):
    values = []
    for val in groups:
        float_val, int_val = float('nan'), None
        try: float_val = float(val)
        except: pass
        try: int_val = int(val)
        except: pass
        if type(float_val) == float and float_val == int_val: values.append(int_val)
        elif type(float_val) == float: values.append(float_val)
        elif int_val: values.append(int_val)
        else: values.append(group)
    return values

CMD_KINDS = [
  {'code': '1B 04', 'name': 'initialize plotter',    'exp_resp': False, 'equals':  b'\x1b\x04' },
  {'code': '1B 05', 'name': 'status request',        'exp_resp': True,  'equals':  b'\x1b\x05' },
  {'code': 'TT',    'name': 'home the cutter',       'exp_resp': False, 'startswith': b'TT' },
  {'code': 'FG',    'name': 'query model / version', 'exp_resp': True,  'startswith': b'FG' },
  {'code': 'FW',    'name': 'media type',            'exp_resp': False, 'pattern': b'^FW(\d+)' },
  {'code': 'FC',    'name': 'cutter offset',         'exp_resp': False, 'pattern': b'^FC(\d+)' },
  # ^ feed offset; 0: pens 18: other tools
  # sets the offset of the tool relative to the feed
  {'code': 'FY',    'name': 'track enhancing',       'exp_resp': False, 'pattern': b'^FY(\d)' },
  {'code': 'FN',    'name': 'alignment',           'exp_resp': False, 'pattern': b'^FN(\d)' },
  # ^ moves the Cameo2 head left (0) or right (1)
  {'code': 'FE0',   'name': '??',                    'exp_resp': False, 'equals':  b'FE0\x03' },
  {'code': 'FE0',   'name': '??',                    'exp_resp': False, 'equals':  b'FE0,0\x03' },
  {'code': 'FF',    'name': '??',                    'exp_resp': False, 'equals':  b'FF0,0,0\x03' },
  {'code': 'TB71',  'name': '??',                    'exp_resp': True,  'equals':  b'TB71\x03' },
  {'code': 'FA',    'name': 'begin page definition', 'exp_resp': True, 'equals':  b'FA\x03' },
  {'code': 'FU',    'name': 'page dimensions (h,w) w/o margin', 'exp_resp': False, 'pattern': b'^FU(\d+),(\d+)' },
  {'code': 'FM1',   'name': '??',                    'exp_resp': False, 'equals':  b'FM1\x03' },
  {'code': 'TB50',  'name': '? / alignment',         'exp_resp': False, 'pattern': b'TB50,(\d)\x03' },
  # ^ argument is page rotation
  {'code': 'FO0',   'name': 'feed the page out',     'exp_resp': False, 'equals':  b'FO0\x03' },
  {'code': 'FO',    'name': 'feed command?',         'exp_resp': False, 'pattern': b'^FO(\d+)' },
  {'code': '&start','name': 'data start',            'exp_resp': False, 'pattern': b'^&100,100,100,\\\\0,0,Z(\d+),(\d+),L0,FX(\d+),0\x03'},
  {'code': '&end',  'name': 'data end',              'exp_resp': False, 'pattern': b'^&1,1,1,TB50,0\x03'},
  {'code': '!',     'name': 'speed',                 'exp_resp': False, 'pattern': b'^!(\d+)' },
  {'code': 'L0',    'name': '??',                    'exp_resp': False, 'equals':  b'L0\x03' },
  {'code': 'U',     'name': 'read upper right',      'exp_resp': True,  'equals':  b'U\x03' },
  {'code': '[',     'name': 'read lower left',       'exp_resp': True,  'equals':  b'[\x03' },
  {'code': 'FQ0',   'name': 'read spead',            'exp_resp': True,  'equals':  b'FQ0\x03' },
  {'code': 'FQ2',   'name': 'read cutter offset',    'exp_resp': True,  'equals':  b'FQ2\x03' },
  {'code': 'FX',    'name': 'force',                 'exp_resp': False, 'pattern': b'^FX(\d+)' },
  {'code': 'FX',    'name': 'force',                 'exp_resp': False, 'pattern': b'^FX(\d+),0' },
  {'code': '\\\\',  'name': 'border?',               'exp_resp': False, 'pattern': b'^\\\\(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'Z',     'name': 'dimensions?',           'exp_resp': False, 'pattern': b'^Z(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'M',     'name': 'move',                  'exp_resp': False, 'pattern': b'^M(\d+|\d+\.\d+),(\d+|\d+\.\d+)\x03$' },
  {'code': 'D',     'name': 'draw',                  'exp_resp': False, 'pattern': b'^D(((\d+|\d+\.\d+),(\d+|\d+\.\d+)(,(\d+|\d+\.\d+),(\d+|\d+\.\d+))*))\x03$', 'filter': coord_pair_filter},
  {'code': 'BZ',    'name': 'bezier',                'exp_resp': False, 'pattern': b'^BZ(\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+|\d+\.\d+),(\d+)\x03$' },
]

class Cmd(object):
    def __init__(self, cmd):
        self.cmd = cmd

class NotFound(Cmd):
    def __str__(self):
        return "Unknown Cmd: {}".format(self.cmd)

class GraphtecCmd(Cmd):

    def __init__(self, cmd, kind, values=None):
        self.cmd = cmd
        self.kind = kind
        self.values = values or []

    def __str__(self):
        desc = "Cmd: {code:5s} - '{name}'".format(**self.kind)
        if '?' in self.kind['name']: desc += " {}".format(self.cmd)
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
                filter_func = cmd_kind.get('filter', default_filter)
                values = m.groups()
                values = filter_func(values)
                return GraphtecCmd(cmd, cmd_kind, values=values)
    return NotFound(cmd)

def divide_commands(bulk):
    buff = b''
    for char in bulk:
        buff += bytes([char])
        if char & 0xF8 == 0:
            # Terminator char
            yield buff
            buff = b''

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('graphtec_input_file', type=argparse.FileType('rb'))
    args = parser.parse_args()
    binary_content = args.graphtec_input_file.read()
    for cmd in divide_commands(binary_content):
        pcmd = parse_cmd(cmd)
        if args.verbose: print(cmd)
        if type(pcmd) == NotFound: pass
        print(pcmd)

if __name__ == "__main__": main()


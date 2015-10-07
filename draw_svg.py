#!/usr/bin/env python

from __future__ import division

import logging, os

import svgwrite # pip install svgwrite

from graphtec import NotFound, GraphtecCmd, parse_cmd

logger = logging.getLogger(name=__name__)

MAX_AREA = (12, 12) # inch
GRAPHTEC_DPI = 508
SVG_DPI = 72

def swap(coordinates):
    """ swap x/y """
    return (coordinates[1], coordinates[0])

def scale(coordinates):
    """ scale from Graphtec DPI to SVG DPI scale """
    if type(coordinates) in (float, int):
        return coordinates * SVG_DPI / GRAPHTEC_DPI
    elif type(coordinates) in (list, tuple):
        return tuple(scale(val) for val in coordinates)
    else:
        raise NotImplementedError()

def main():
    global SVG_DPI
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--svg-dpi', type=float, help='DPI of the SVG to be created')
    parser.add_argument('graphtec_input_file', type=argparse.FileType('rb'))
    args = parser.parse_args()
    if args.svg_dpi: SVG_DPI = args.svg_dpi
    content = args.graphtec_input_file.read()
    buff = b''
    commands = []
    for char in content:
        buff += bytes([char])
        if char & 0xF8 == 0:
            # Terminator char
            commands.append(buff)
            buff = b''
    svg_filename = os.path.splitext(args.graphtec_input_file.name)[0] + '.svg'
    dwg = svgwrite.Drawing(svg_filename, profile='tiny', size = tuple("{}px".format(dim*SVG_DPI) for dim in MAX_AREA))
    start = (0, 0)
    end = (0, 0)
    for cmd in commands:
        pcmd = parse_cmd(cmd)
        #print(pcmd)
        if type(pcmd) == NotFound:
            logger.warning("Cmd not found: {}".format(cmd))
            continue
        elif type(pcmd) == GraphtecCmd and pcmd.kind['name'] == 'move':
            start = scale(swap(pcmd.values))
        elif type(pcmd) == GraphtecCmd and pcmd.kind['name'] == 'draw':
            end = scale(swap(pcmd.values))
            dwg.add(dwg.line(start, end, stroke=svgwrite.rgb(10, 10, 16, '%')))
            start = end
        elif type(pcmd) == GraphtecCmd and pcmd.kind['name'] == 'bezier':
            fmt = "M {},{} C {},{} {},{} {},{}"
            coord_pairs = pcmd.values[1:9]
            coord_pairs = [coord_pairs[0:2], coord_pairs[2:4], coord_pairs[4:6], coord_pairs[6:8]]
            coord_pairs = [swap(coords) for coords in coord_pairs]
            coord_pairs = [scale(coords) for coords in coord_pairs]
            coords_flat = [item for sublist in coord_pairs for item in sublist]
            d = fmt.format(*coords_flat)
            dwg.add(dwg.path(d=d, stroke=svgwrite.rgb(10, 10, 16, '%'), fill='none'))
            start = coord_pairs[3]
    dwg.save()

if __name__ == "__main__": main()


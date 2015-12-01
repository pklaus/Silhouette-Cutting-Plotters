#!/usr/bin/env python

from __future__ import division

import logging, os

import svgwrite # pip install svgwrite

from graphtec import NotFound, GraphtecCmd, parse_cmd

logger = logging.getLogger(name=__name__)

MAX_AREA = (12, 12) # inch
GRAPHTEC_DPI = 508
SVG_DPI = 90
ORIENTATION = 0
BORDER = 30
X_DIM = 6096 # 12 in * 508 dpi

def transform(coordinates):
    """ Get the coordinate system right for SVG """
    #return (coordinates[0], coordinates[1])
    if ORIENTATION == 0:   return         (coordinates[1], coordinates[0]) # swap x/y
    elif ORIENTATION == 1: return (X_DIM - BORDER - coordinates[0], coordinates[1]) # flip horizontally
    else: raise NotImplementedError()

def scale(coordinates):
    """ scale from Graphtec DPI to SVG DPI scale """
    if type(coordinates) in (float, int):
        return coordinates * SVG_DPI / GRAPHTEC_DPI
    elif type(coordinates) in (list, tuple):
        return tuple(scale(val) for val in coordinates)
    else:
        raise NotImplementedError()

def group_pairs(lst, n=2):
    return list(zip(*[lst[i::n] for i in range(n)]))

def main():
    global SVG_DPI, ORIENTATION
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
    dwg.add(dwg.rect(insert=scale((0,0)),size=scale((X_DIM,X_DIM)), stroke=svgwrite.rgb(10, 10, 100, '%'), fill='none'))
    dwg.add(dwg.rect(insert=scale((BORDER,BORDER)),size=scale((X_DIM-2*BORDER,X_DIM-2*BORDER)), stroke=svgwrite.rgb(100, 10, 16, '%'), fill='none'))
    start = (0, 0)
    end = (0, 0)
    for cmd in commands:
        pcmd = parse_cmd(cmd)
        #print(pcmd)
        if type(pcmd) == NotFound:
            logger.warning("Cmd not found: {}".format(cmd))
            continue
        elif pcmd.kind['code'] == 'TB50':
            ORIENTATION = int(pcmd.values[0])
        elif pcmd.kind['name'] == 'move':
            start = scale(transform(pcmd.values))
        elif pcmd.kind['name'] == 'draw':
            coordinates = pcmd.values
            coordinates = group_pairs(coordinates)
            coordinates = [scale(transform(coords)) for coords in coordinates]
            for coordinate in coordinates:
                end = coordinate
                dwg.add(dwg.line(start, end, stroke=svgwrite.rgb(10, 10, 16, '%'), stroke_width='0.4'))
                start = end
        elif pcmd.kind['name'] == 'bezier':
            fmt = "M {},{} C {},{} {},{} {},{}"
            coord_pairs = pcmd.values[1:9]
            coord_pairs = group_pairs(coord_pairs)
            coord_pairs = [transform(coords) for coords in coord_pairs]
            coord_pairs = [scale(coords) for coords in coord_pairs]
            coords_flat = [item for sublist in coord_pairs for item in sublist]
            d = fmt.format(*coords_flat)
            dwg.add(dwg.path(d=d, stroke=svgwrite.rgb(10, 10, 16, '%'), fill='none', stroke_width='0.4'))
            start = coord_pairs[3]
    dwg.save()

if __name__ == "__main__": main()


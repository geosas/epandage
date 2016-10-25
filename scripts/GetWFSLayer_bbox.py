#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 10:00:02 2016

@author: Mounirsky

This driver is used to download vector layer (limited to a specified BoundingBox) from a WFS stream using OWSLib python library.

"""

from os.path import exists
from datetime import datetime
import argparse
from owslib.wfs import WebFeatureService

parser = argparse.ArgumentParser(
    description="GetWFSLayer_bbox +o <Offset(Optionel)> +u <WFS_URL> +n <TypeName> +p <PATH> +b <BBox>",
    prog='./GetGeojsonBbox.py',
    prefix_chars='+')

parser.add_argument(
    '+o',
    action="store_true",
    help='Optionel flag -o: BoundingBox offset by 500m')
parser.add_argument(
    '+u',
    required=True,
    help='WFS URL - Required - (Usage : +u URL)')
parser.add_argument(
    '+n',
    required=True,
    help='layer typename - Required - (Usage : +n typeName)')
parser.add_argument(
    '+p',
    required=True,
    help='Downloading directory/filename - (Usage : +p /tmp/filename)')
parser.add_argument(
    '+b',
    required=False,
    help="BoundingBox (Usage : +b 'xmin,ymin,xmax,ymax' )")
parser.add_argument(
    '+srs',
    required=False,
    default='EPSG:2154',
    help="EPSG code to request the data in - Default: EPSG:2154 (Usage : -srs EPSG:code')")

args = vars(parser.parse_args())

URL = args['u']
name = args['n']
BBox = args['b']
path = args['p']
srs = args['srs']

if args['o']:
    offset = True
else:
    offset = False

# --------------------------------------------------------------
# GetWFSLayer function
# --------------------------------------------------------------


def GetWFSLayerBbox(u, n, p, b, off, s):
    start = datetime.now()

    bb = b.split(",")
    bbox = tuple([float(xy) for xy in bb])

    # add offset of 500m
    if off:
        offset = 500
        box = (bbox[0] - offset, bbox[1] - offset,
               bbox[2] + offset, bbox[3] + offset)
    else:
        box = bbox

    chemin = p

    if not exists(chemin):
        # Get the vector layer using OGC WFS standard vrsion 1.0.0
        wfs = WebFeatureService(u, version='1.0.0', timeout=10)

        # Supported outputFormat : GML2, GML3, shape-zip, application/json
        getFeature = wfs.getfeature(
            typename=(
                n,
            ),
            outputFormat="application/json",
            bbox=box,
            srsname=s)  # maxfeatures=200

        # Download the zipped shapefile
        data = getFeature.read()
        f = open(chemin, 'wb')
        f.write(data)
        f.close()

    # Calculat time
    delta = datetime.now() - start

    print "\n{0} Downloaded on : {1}\n".format(n, delta)

    return

# --------------------------------------------------------------
# II - Execute function
# --------------------------------------------------------------
if __name__ == '__main__':
    GetWFSLayerBbox(URL, name, path, BBox, offset, srs)

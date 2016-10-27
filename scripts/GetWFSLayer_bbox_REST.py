#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 10:00:02 2016

@author: Mounirsky

This driver is used to download vector layer (limited to a specified BoundingBox) from a WFS stream using requests python library.

"""

from os.path import exists
from datetime import datetime
import argparse
import requests

parser = argparse.ArgumentParser(
    description="GetWFSLayerBbox_REST +o <Offset(Optionel)> +u <WFS_URL> +n <TypeName> +p <PATH> +b <BBox>",
    prog='./GetWFSLayerBbox_REST.py',
    prefix_chars='+')

parser.add_argument(
    '+o',
    action="store_true",
    help='Optionel flag -o: BoundingBox offset by 500m')
parser.add_argument(
    '+u',
    type=str,
    required=True,
    help='WFS URL - Required - (Usage : +u URL)')
parser.add_argument(
    '+n',
    type=str,
    required=True,
    help='layer typename - Required - (Usage : +n typeName)')
parser.add_argument(
    '+p',
    type=str,
    required=True,
    help='Downloading directory - (Usage : +p /tmp)')
parser.add_argument(
    '+b',
    type=str,
    required=False,
    help="BoundingBox (Usage : +b 'xmin,ymin,xmax,ymax' )")
parser.add_argument(
    '+srs',
    type=str,
    required=False,
    default='EPSG:2154',
    help="EPSG code to request the data in - Default: EPSG:2154 (Usage : -srs EPSG:code')")

args = vars(parser.parse_args())

URL = args['u']
name = args['n']
BBox = args['b']
path = args['p']
srs = args['srs']

# if +o argument is added
if args['o']:
    offset = True
else:
    offset = False

# --------------------------------------------------------------
# GetWFSLayer function
# --------------------------------------------------------------

#u = 'http://geowww.agrocampus-ouest.fr/geoserver/epandage/wfs'
#n = 'zonage_pente_bretagne'
#b = '251668.437447,6786461.36502,252656.643096,6787198.46528'
#s = 'EPSG:2154'
#off = True

def GetWFSLayerBbox_REST(u, n, p, b, off, s):
    start = datetime.now()
    # string bbox to list of strings bbox
    bb = b.split(",")
    # list of strings bbox to list of float
    bboxx = [float(i) for i in bb]

    # add offset of 500m if +o argument is added
    if off:
        offset = 500
        bbox = ','.join([str(bboxx[0] - offset),
                str(bboxx[1] - offset),
                str(bboxx[2] + offset),
                str(bboxx[3] + offset)
                ])
    else:
        bbox = b

    chemin = p

    if not exists(chemin):
        # configurate the request parameters
        param = {
            'Service':'WFS',
            'Version':'2.0.0',
            'Request':'GetFeature',
            'typeName':n,
            'bbox':bbox,
            'srsName':s,
            'outputFormat':'application/json'
        }

        # Do the GET request
        r = requests.get(url=u, params=param, timeout=10)

        # Download the zipped shapefile
        data = r.content
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
    GetWFSLayerBbox_REST(URL, name, path, BBox, offset, srs)


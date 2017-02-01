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
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(
    description="GetWFSLayerBbox_REST +o +u <WFS_URL> +n <TypeName> +d <Output directory> +b <BBox> +srs <EPSG:code (Default: EPSG:2154)>  +l <login (optionel)> +pwd <password (optionel)>",
    prog='./GetWFSLayerBbox_REST.py',
    prefix_chars='+')

requiredNamed = parser.add_argument_group('required arguments')

parser.add_argument(
    '+o',
    action="store_true",
    help='Optionel flag -o: BoundingBox offset by 500m')
requiredNamed.add_argument(
    '+u',
    metavar='URL',
    type=str,
    required=True,
    help='WFS URL')
requiredNamed.add_argument(
    '+n',
    metavar='typename',
    type=str,
    required=True,
    help='layer typename')
requiredNamed.add_argument(
    '+d',
    metavar='OUTPUT_DIR',
    type=str,
    required=True,
    help='Output directory')
parser.add_argument(
    '+b',
    type=str,
    required=False,
    help="BoundingBox (Usage : +b 'xmin,ymin,xmax,ymax' )")
parser.add_argument(
    '+srs',
    metavar='EPSG:code',
    type=str,
    required=False,
    default='EPSG:2154',
    help="EPSG code of the request layer - Default: EPSG:2154")
requiredNamed.add_argument(
    '+l',
    metavar='LOGIN',
    type=str,
    required=False,
    default=None,
    help='WFS LOGIN')
requiredNamed.add_argument(
    '+pwd',
    metavar='PASSWORD',
    type=str,
    required=False,
    default=None,
    help='WFS PASSWORD')

args = vars(parser.parse_args())

URL = args['u']
name = args['n']
BBox = args['b']
path = args['d']
srs = args['srs']
login = args['l']
password = args['pwd']

# if +o argument is added
if args['o']:
    offset = True
else:
    offset = False

# --------------------------------------------------------------
# GetWFSLayer function
# --------------------------------------------------------------

def GetWFSLayerBbox_REST(u, n, d, b, off, s, l, pwd):
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

    chemin = d

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
            
        # if building layer -> replace bbox filter to cql_filter to make double
        # filter (bbox & feature)
        if n == "CP.CadastralBuilding":
            cql_filter = "(bbox(geometry,%s,'%s')and(type='01'))" % (bbox, s)
            param.pop('bbox')
            param['CQL_FILTER'] = cql_filter
                
        if l and pwd:
            # parametres d'autentification
            auth = HTTPBasicAuth(l, pwd)
            # Do the GET autenfified request
            r = requests.get(url=u, auth=auth, params=param, timeout=10)
        else:
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
    else:
        print "\n{0} exsists\n".format(n)
    return

# --------------------------------------------------------------
# II - Execute function
# --------------------------------------------------------------
if __name__ == '__main__':
    GetWFSLayerBbox_REST(URL, name, path, BBox, offset, srs, login, password)
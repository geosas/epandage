#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 10:00:02 2016

@author: Mounirsky

This driver is used to download the filtred attributes of vector layer from a WFS stream using OWSLib python library.

"""

from os.path import exists
from datetime import datetime
import argparse
from owslib.wfs import WebFeatureService
from owslib import fes

parser = argparse.ArgumentParser(
    description="GetWFSLayer_filter.py -u <WFS_URL> -n <TypeName> -p <PATH (Default:/tmp/)> -a <Attribute name> -f <'String,...'> -srs <EPSG:code (Default: EPSG:2154)>",
    prog='./GetWFSLayer_filter.py')

parser.add_argument(
    '-u',
    required=True,
    help='WFS URL - Required - (Usage : -u URL)')
parser.add_argument(
    '-n',
    required=True,
    help='layer typename - Required - (Usage : -n typeName)')
parser.add_argument(
    '-p',
    required=True,
    help='Downloading directory/filename - (Usage : -p /tmp/filename)')
parser.add_argument(
    '-a',
    required=True,
    help="Attribut name (Usage : -a Num_ilot )")
parser.add_argument(
    '-f',
    required=True,
    help="Filter features by attribute values (Usage : -f 'Literal1, Literal2,...')")
parser.add_argument(
    '-srs',
    required=False,
    default='EPSG:2154',
    help="EPSG code to request the data in - Default: EPSG:2154 (Usage : -srs EPSG code')")

args = vars(parser.parse_args())

URL = args['u']
name = args['n']
path = args['p']
att_name = args['a']
fe = args['f']
srs = args['srs']

# --------------------------------------------------------------
# GetWFSLayer function
# --------------------------------------------------------------


def GetWFSLayerFilter(u, n, p, a, fe, s):
    start = datetime.now()

    idList = fe.split(",")

    chemin = p

    if not exists(chemin):
        filterList = [fes.PropertyIsEqualTo(att_name, i) for i in idList]
        fr = fes.FilterRequest()
        filter_fes = fr.setConstraintList(filterList, tostring=True)

        # Get the vector layer using OGC WFS standard vrsion 1.0.0
        wfs = WebFeatureService(u, version='1.0.0', timeout=10)
        # Supported outputFormat : GML2, GML3, shape-zip, application/json
        getFeature = wfs.getfeature(
            typename=(n,),
            filter=filter_fes,
            outputFormat="application/json",
            srsname=s)  # maxfeatures=200)

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
    GetWFSLayerFilter(URL, name, path, att_name, fe, srs)

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
    description="GetWFSLayer_filter_REST.py -l <login> -pass <password> -u <WFS_URL> -n <TypeName> -p <Output directory> -a <Field name> -f <'value1,value2,...'> -srs <EPSG:code (Default: EPSG:2154)>",
    prog='./GetWFSLayer_filter_REST.py')

requiredNamed = parser.add_argument_group('required arguments')

requiredNamed.add_argument(
    '-u',
    metavar='URL',
    type=str,
    required=True,
    help='WFS URL')
requiredNamed.add_argument(
    '-n',
    metavar='typename',
    type=str,
    required=True,
    help='layer typename')
requiredNamed.add_argument(
    '-d',
    metavar='OUTPUT_DIR',
    type=str,
    required=True,
    help='Output directory')
requiredNamed.add_argument(
    '-a',
    metavar='Field_name attributes',
    type=str,
    required=True,
    help="Field name")
requiredNamed.add_argument(
    '-f',
    metavar="'value1, value2,...'",
    type=str,
    required=True,
    help="Features values to be used for filter")
parser.add_argument(
    '-srs',
    metavar='EPSG:code',
    type=str,
    required=False,
    default='EPSG:2154',
    help="EPSG code of the request layer - Default: EPSG:2154")

args = vars(parser.parse_args())

URL = args['u']
name = args['n']
path = args['d']
att_name = args['a']
fe = args['f']
srs = args['srs']

# --------------------------------------------------------------
# GetWFSLayer function
# --------------------------------------------------------------


def GetWFSLayerFilter(u, n, d, a, fe, s):
    start = datetime.now()

    idList = fe.split(",")

    chemin = d

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
    else:
        print "\n{0} exsists\n".format(n)
    return

# --------------------------------------------------------------
# II - Execute function
# --------------------------------------------------------------
if __name__ == '__main__':
    GetWFSLayerFilter(URL, name, path, att_name, fe, srs)

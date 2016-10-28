#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 10:00:02 2016

@author: Mounirsky

This driver is used to download the filtred attributes of a vector layer from a WFS stream using requests and OWSLib python library.

"""

from os.path import exists
from datetime import datetime
import argparse
from owslib import fes
import requests

parser = argparse.ArgumentParser(
    description="GetWFSLayer_filter_REST.py -l <login> -p <password> -u <WFS_URL> -n <TypeName> -d <Output directory> -a <Field name> -f <'value1,value2,...'> -srs <EPSG:code (Default: EPSG:2154)>",
    prog='./GetWFSLayer_filter_REST.py')

requiredNamed = parser.add_argument_group('required arguments')

parser.add_argument(
   '-l',
    metavar='LOGIN',
    type=str,
    help='WFS stream login')
parser.add_argument(
    '-p',
    metavar='PASSWORD',
    type=str,
    help='WFS stream password')
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

login = args['l']
password = args['p']
URL = args['u']
name = args['n']
path = args['d']
att_name = args['a']
fe = args['f']
srs = args['srs']

# --------------------------------------------------------------
# GetWFSLayer function
# --------------------------------------------------------------

def GetWFSLayer_filter_REST(login, password, u, n, d, a, fe, s):
    start = datetime.now()
    idList = fe.split(",")
    chemin = d

    if not exists(chemin):
        filterList = [fes.PropertyIsEqualTo(att_name, i) for i in idList]
        fr = fes.FilterRequest()
        filter_fes = fr.setConstraintList(filterList, tostring=True)

        if login and password:
            print 'Pass OK'
            # configurate the request authentification
            auth=requests.auth.HTTPBasicAuth(login, password)
        else:
            print 'No pass'
            auth=None
        # configurate the request parameters
        param = {
            'Service':'WFS',
            'Version':'2.0.0',
            'Request':'GetFeature',
            'typeName':n,
            'filter':filter_fes,
            'srsName':s,
            'outputFormat':'application/json'
        }
        # Do the GET request
        r = requests.get(url=u, params=param, auth=auth, timeout=10)
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
    GetWFSLayer_filter_REST(login, password, URL, name, path, att_name, fe, srs)









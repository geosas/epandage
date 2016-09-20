#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu May 19 10:00:02 2016

@author: Mounirsky

This application allows to return the boundingBox of a GeoJSON file

"""
import argparse
import json

parser = argparse.ArgumentParser(
    description="GetGeojsonBbox.py -d <Directory to GeoJSON file>",
    prog='./GetGeojsonBbox.py')

parser.add_argument(
    '-d',
    required=True,
    help="Directory to GeoJSON file (Usage : -d '/tmp/file.geojson' )")

args = vars(parser.parse_args())

geojsonDir = args['d']


def explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield coordinate tuples.
    As long as the input is conforming, the type of the geometry doesn't matter."""
    for e in coords:
        if isinstance(e, (float, int, long)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def getGeojsonBbox(jsonFDir):
    data = open(jsonFDir).read()
    f = json.loads(data)
    list_x, list_y, list_X, list_Y = [], [], [], []

    for i in range(0, len(f['features'])):
        x, y = zip(*list(explode(f['features'][i]['geometry']['coordinates'])))
        list_x.append(x)
        list_y.append(y)
    for itemx in list_x:
        list_X.extend(itemx)
    for itemy in list_y:
        list_Y.extend(itemy)
    X = tuple(list_X)
    Y = tuple(list_Y)

    # tuple to string
    bboxGeoJSON = min(X), min(Y), max(X), max(Y)
    bb_arr_list = list(bboxGeoJSON)
    bb_arr_strList = [str(j) for j in bb_arr_list]
    bb_arr_str = ','.join(tuple(bb_arr_strList))

    return bb_arr_str

# --------------------------------------------------------------
# II - Execute function
# --------------------------------------------------------------
if __name__ == '__main__':
    print getGeojsonBbox(geojsonDir)

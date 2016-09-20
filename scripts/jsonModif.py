#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu May 19 10:00:02 2016

@author: Mounirsky

This application allows to return a well formated GeoJSON file from a json file.

"""
import argparse
import json
from geojson import MultiPolygon

parser = argparse.ArgumentParser(
    description="jsonModif.py -in <Directory to JSON fileIn> -out <GeoJSON fileOut name>",
    prog='./jsonModif.py')

parser.add_argument(
    '-in',
    required=True,
    help="Directory to JSON file in (Usage : -in '/file.json' )")
parser.add_argument(
    '-dir',
    required=True,
    help="Directory to file out (Usage : -in '/dir/' )")
parser.add_argument(
    '-out',
    required=True,
    help="GeoJSON file out name (Usage : -out 'fileOutName.geojson' )")

args = vars(parser.parse_args())

jsonFile = args['in']
dirctory = args['dir']
fOutName = args['out']


def tracerOut(tracerIn, dirctory, filOut):
    coor = []
    layerType = {
        "type": "FeatureCollection",
        "totalFeatures": 0,
        "features": [],
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::4326"}}}
    for k in range(len(tracerIn)):
        coor2 = [[[]]]
        coor = [tracerIn[k]['geometry']['coordinates'][0]]
        # print coor
        for xy in range(len(coor[0])):
            coor_unit = [float(coor[0][xy][i])
                         for i in range(len(coor[0][xy]))]
            coor2[0][0].append(coor_unit)

        layer = MultiPolygon(coordinates=coor2)
        inFeatures = {"type": "Feature", "properties": {}, "geometry": layer}
        layerType['features'].append(inFeatures)

    layerType['totalFeatures'] = k + 1
    dataOut = json.dumps(layerType, sort_keys=True)
    f = open(dirctory + filOut, 'wb')
    f.write(dataOut)
    f.close()
    return


def modifJSON(jsonFile, dirctory, fOutName):
    jsonIN = json.loads(open(jsonFile).read())
    tracersEnPlus = jsonIN['tracersEnPlus']
    tracersEnMoins = jsonIN['tracersEnMoins']

    if tracersEnPlus != []:
        name = 'Moins_' + fOutName
        tracerOut(tracersEnPlus, dirctory, name)

    if tracersEnMoins != []:
        name = 'Plus_' + fOutName
        tracerOut(tracersEnMoins, dirctory, name)
    return

# --------------------------------------------------------------
# II - Execute function
# --------------------------------------------------------------
if __name__ == '__main__':
    modifJSON(jsonFile, dirctory, fOutName)

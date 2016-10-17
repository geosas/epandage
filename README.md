# WPS epandage & zonage
## GIS programs

- GRASS-GIS 7.*
  * [Download & install](https://grass.osgeo.org/grass7/)
  * [Compile and Install](https://grasswiki.osgeo.org/wiki/Compile_and_Install)

- GDAL 
  * [Install](https://gdal.gloobe.org/install.html#linux)

## Install and configure PyWPS-3.2.* Instance

- [Installation of PyWPS](http://pywps.readthedocs.io/en/pywps-3.2/installation/index.html)
- [Configuration](http://pywps.readthedocs.io/en/pywps-3.2/configuration/index.html#configuration)
- [Testing PyWPS](http://pywps.readthedocs.io/en/pywps-3.2/testing/index.html#testing-pywps)

[//]: #[Documentation]()



## PyWPS & GRASS-GIS

### Configure the Grass section in the "wps_config.cfg" file :
```
[grass]
path=/usr/local/grass-version/bin/:/usr/local/grass-version/scripts/:/usr/local/bin/:/usr/bin/
gisbase=/usr/local/grass-version
ldLibraryPath=/usr/local/grass-version/lib/
```
You may refer to the [wps_config.cfg](wps_config.cfg) for further customization

### Configurate /usr/lib/cgi-bin/pywps.cgi as follow :
```shell=
#!/bin/sh

# Author: Jachym Cepicky
# Purpose: CGI script for wrapping PyWPS script
# Licence: GNU/GPL
# Usage: Put this script to your web server cgi-bin directory, e.g.
# /usr/lib/cgi-bin/ and make it executable (chmod 755 pywps.cgi)

# NOTE: tested on linux/apache

export PYWPS_CFG=/usr/local/wps/epandage/wps_config.cfg
export PYWPS_PROCESSES=/usr/local/wps/epandage/wps
export HOME=/usr/local/wps/epandage
# Add the right python path of the used version of grass
export PYTHONPATH=/usr/local/grass-7.*/etc/python/

/usr/local/bin/wps.py
```

## For WPS "epandage"

### [Python 2.7] required modules (2.6 is compatible but deprecated)
```
- grass.script
- time
- datetime
- os
- tempfile
- hashlib
- yaml
- argparse
- owslib
- geojson
- logging
```

### WPS "epandage" usage
Put the __epandage__ folder preferably on the same level of the __processes__  folder (default : __/usr/local/pywps/processes__ ). For exemple in this project is : [/usr/local/wps/epandage/wps](./wps)

Be sure that the __PYWPS_PROCESSES__ variable on __"pywps.cgi"__  contains the the right directory.


Indicate the right path to your configuration file __"epandage_process.conf"__ containing the WFS URLs and layer names to deal with.

Here is an example of the configuration file __"epandage_process.conf"__ :

```json=1
{
   "RPG_layer":{
      "url":"http://geobretagne.fr.../wfs",
      "name":"RPG",
      "att_name":"ilos_id"
   },
   "layerList":{
      "1":[
         "http://geobretagne.fr..../wfs",
         "bdtopo_cours_eau",
         "distanceEau_7"
      ],
      "2":[
         "http://geobretagne.fr..../wfs",
         "Cadastral_Building",
         "distanceBati"
      ],
      "3":[
         "http://geobretagne.fr..../wfs",
         "cadastre_conchylicole",
         "distanceZC"
      ],
      "4":[....],
	  
      "8":[
         "http://geowww.agrocampus-ouest.fr..../wfs",
         "Vector_SLOPE_layer",
         "slope"
      ]
   }
}
```
__NB:__ For the slope layer (number __8__ in __layerList__) to be used in the process, it should containe the value **"slope"** as 3th value.

The file path (string) should be assigned to the variable named __"config_file"__ on [epandage.py](./wps/epandage.py)

## For WPS zonage
This service allows the generation of the slopes zoning vector layer to be used later in the "epandage" WPS service.

Note: The output layer will automatically be exported on the indicated postgis database.

The default database is "epandage" (on geowww server) and the table is named "zonage_pente_bretagne".
This table is published on geoserver with the following referances:
__URL__: http://geowww.agrocampus-ouest.fr/geoserver/epandage/ows
__name__: zonage_pente_bretagne

__NB__ : When the WPS "zoning" is executed, using the default postgis database, it will overwrite the existing table (itself linked to the geoserver layer) and update automatically the native and the declared CRS on geoserver.

### [Python 2.7] required modules (2.6 is compatible but deprecated)
```
- os
- time
- datetime
- shutil
- logging
- requests
```





***
##### Powred by [![AGROCAMPUS-OUEST](http://www.agrocampus-ouest.fr/infoglueDeliverLive/digitalAssets/89735_Logo-AGROCAMPUS-OUEST.png)](http://www.agrocampus-ouest.fr)
***
[![Creative Commons License](https://licensebuttons.net/l/by-sa/3.0/88x31.png)](https://creativecommons.org/licenses/by-sa/4.0/)



[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen.)

	
   [Python 2.7]: <https://www.python.org/downloads/release>
   


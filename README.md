# WPS "epandage"
## GIS programs

- GRASS-GIS 7.*
  * [Download & install](https://grass.osgeo.org/grass7/)
  * [Compile and Install](https://grasswiki.osgeo.org/wiki/Compile_and_Install)

- GDAL 
  * [Install](https://gdal.gloobe.org/install.html#linux)

## Install end configure PyWPS-3.2.* Instance

- [Installation of PyWPS](http://pywps.readthedocs.io/en/pywps-3.2/installation/index.html)
- [Configuration](http://pywps.readthedocs.io/en/pywps-3.2/configuration/index.html#configuration)
- [Testing PyWPS](http://pywps.readthedocs.io/en/pywps-3.2/testing/index.html#testing-pywps)

[//]: #[Documentation]()



## PyWPS & GRASS-GIS

### Configure the Grass section in the [wps_config.cfg](wps_config.cfg):
```
[grass]
path=/usr/local/grass-version/bin/:/usr/local/grass-version/scripts/:/usr/local/bin/:/usr/bin/
gisbase=/usr/local/grass-version
ldLibraryPath=/usr/local/grass-version/lib/
```
You may refer to the [wps_config.cfg](wps_config.cfg) for further customization

### Configurate /usr/lib/cgi-bin/pywps.cgi as follow :
```sh

# Add the right python path of the used version of grass
export PYTHONPATH=/usr/local/grass-7.*/etc/python/

/usr/local/bin/wps.py
```
 
## [Python 2.7] required modules (2.6 is compatible but deprecated)
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
```

### WPS "epandage" usage
Add your process "epandage" to the list of PyWPS processes

```
/usr/local/wps/processes/__init__.py
```
as follow :

```py
__all__ = ['epandage']
```

Indicate the right path to your configuration file "epandage_process.conf" contaning the WFS URL's and layer names to deal with.

##### Powred by 
[![AGROCAMPUS-OUEST](http://www.agrocampus-ouest.fr/infoglueDeliverLive/digitalAssets/89735_Logo-AGROCAMPUS-OUEST.png)](http://www.agrocampus-ouest.fr)

[![Creative Commons License](https://licensebuttons.net/l/by-sa/3.0/88x31.png)](https://creativecommons.org/licenses/by-sa/4.0/)



[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen.)

	
   [Python 2.7]: <https://www.python.org/downloads/release>
   

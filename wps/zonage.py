from pywps.Process import WPSProcess
from datetime import datetime
import os
import shutil
import time
import logging
import requests


class Process(WPSProcess):
    '''
    TODO :
    1- Indicte the output directory and assing it to the variable "tmp_dir"
    2- Indicte the directory where all the layers and the "reclass_file.txt" are,
    and assign it to the variable "layers_path" on the execute methode.

    If you want to change the classification values please edit the "reclass_file.txt"
    as is montioned on the Grass Doc at :
    https://grass.osgeo.org/grass70/manuals/r.reclass.html#Reclass_rules_examples
    '''

    def __init__(self):

        # init process
        WPSProcess.__init__(
            self,
            identifier="zonage",
            title="Service WPS pour la generation des zonages de pentes",
            version="1.0",
            storeSupported=True,
            statusSupported=True,
            grassLocation=True,
            abstract="""Service WPS pour la generation de la couche de zonages
            de pentes, pour en suite l'utiliser dans le service WPS epandage.
            Remarque : La couche en sortie sera exporter automatiquement sur la
            base postgis indique.
            Par defaut sur la base "epandage" sur "geowww" avec le nom de table
            "zonage_pente_bretagne".
            Celle-ci est publiee sur geoserver avec les referance suivantes :
            URL : http://geowww.agrocampus-ouest.fr/geoserver/epandage/wfs,
            name : zonage_pente_bretagne """)

        #######################################################################
        # Inputs
        #######################################################################
        self.dem_layer = self.addLiteralInput(
            identifier="dem_layer",
            title="Model Numerique de Terrain",
            default="BDALTIV2_25M_BZH.tif",
            type="")

        self.RH_layer = self.addLiteralInput(
            identifier="RH_layer",
            title="Vecteur reseau hydrographique",
            default="BDTOPO_TRONCON_COURS_EAU_BZH_2016.shp",
            type="")

        self.SurfaceEau_layer = self.addLiteralInput(
            identifier="SurfaceEau_layer",
            title="Vecteur surfaces en eau",
            default="BDTOPO_SURFACE_EAU_BZH_2016.shp",
            type="")

        self.zone_limit_layer = self.addLiteralInput(
            identifier="zone_limit_layer",
            title="Nom du fichier vecteur zones d'application",
            default="",
            minOccurs=0,
            type="")

        self.distanceEau = self.addLiteralInput(
            identifier="distanceEau",
            title="Distance maximale (m) du cours d'eau",
            default='100',
            type="")

        self.simplifier = self.addLiteralInput(
            identifier="simplifier",
            title="Simplification du vecteur en sortie avec un Trasholde de 6 metres",
            default=True,
            allowedValues=[
                True,
                False],
            type=True)

        self.supprimer = self.addLiteralInput(
            identifier="supprimer",
            title="Supprimer le fichier shapefile en sortie",
            default=True,
            allowedValues=[
                True,
                False],
            type=True)

        self.host = self.addLiteralInput(
            identifier="host",
            title="postgres host",
            default='geowww.agrocampus-ouest.fr',
            type="")

        self.port = self.addLiteralInput(
            identifier="port",
            title="postgres port",
            default='5432',
            type="")

        self.dbname = self.addLiteralInput(
            identifier="dbname",
            title="Nom de la base de donnees",
            default='epandage',
            type="")

        self.user = self.addLiteralInput(
            identifier="user",
            title="Nom d'utilisateur postgres",
            default='vidae',
            type="")

        self.password = self.addLiteralInput(
            identifier="password",
            title="Mot de passe postgres",
            type="")

        self.geoserver_user = self.addLiteralInput(
            identifier="geoserver_user",
            title="Nom d'utilisateur geoserver",
            type="")

        self.geoserver_pass = self.addLiteralInput(
            identifier="geoserver_pass",
            title="Mot de passe geoserver",
            type="")

        self.email = self.addLiteralInput(
            identifier="email",
            title='Adresse(s) e-mail pour etre prevenus a la fin du traitement.\
             (separer par virgule "," si plusieurs)',
            minOccurs=0,
            type="")

        self.outputSrs = self.addLiteralInput(
            identifier="outputSrs",
            title="EPSG de la couche en sortie et publiee",
            allowedValues=[
                'EPSG:2154',
                'EPSG:3857',
                'EPSG:4326'],
            default="EPSG:2154",
            type="")

    def execute(self):

        LOGGER = logging.getLogger(__name__)

        stime = datetime.now()

        LOGGER.info('Start Time : {0} \n'.format(stime))

        # Directory where will be the temporary GRASS location and where will be (or not) the final layer (shapefile)
        tmp_dir = '/home/saadni/tmp/tmp_zonage/'

        # Creat epandage tmp dirrectory if not exists
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        # File indecating the classes and layers directory
        layers_path = '/home/saadni/layers_pentes/'

        # Point to the folder 'scripts' (two folders above 'zonage.py')
        current_path = os.path.realpath(__file__)
        scripts_path = os.path.abspath(
            os.path.join(
                current_path,
                '..',
                '..',
                'scripts')) + '/'

        RH_path = layers_path + self.getInputValue('RH_layer')
        SurfaceEau_path = layers_path + self.getInputValue('SurfaceEau_layer')

        if self.getInputValue('zone_limit_layer') != "":
            zone_limit_path = layers_path + \
                self.getInputValue('zone_limit_layer')
        else:
            zone_limit_path = None

        #######################################################################
        # Vector processing
        #######################################################################
        stime_process = datetime.now()
        # Import data into GRASS using v.in.ogr
        self.cmd("v.in.ogr --quiet -o input=%s output=RH" % (RH_path))
        self.cmd(
            "v.in.ogr --quiet -o input=%s output=surface_eau" %
            (SurfaceEau_path))

        overlay_list = []
        vector_List = ['RH', 'surface_eau']
        if zone_limit_path:
            # Import data into GRASS using v.in.ogr
            self.cmd(
                "v.in.ogr --quiet -o input=%s output=zone_lim" %
                (zone_limit_path))

            #########################################
            # limit zone overlay
            #########################################
            i = 0
            for inputs in vector_List:
                output = 'overlay' + str(i)
                # v.overlay - Overlays two vector maps - and: also known as
                # 'intersection' in GIS
                self.cmd(
                    "v.overlay --quiet ainput=%s binput=zone_limit operator=and output=%s olayer=1,0,0" %
                    (inputs, output))
                overlay_list.append(output)
                i += 1
        delta = datetime.now() - stime_process
        LOGGER.info('Vector import on {0} \n'.format(delta))
        #########################################
        # Buffer
        #########################################
        stime_process = datetime.now()

        bufferList = []
        j = 0
        if len(overlay_list) > 0:
            for inputs in overlay_list:
                out_buffer = 'buffer' + str(j)
                # v.buffer - Creates a buffer around vector features of given
                # type.
                self.cmd(
                    "v.buffer --quiet --overwrite input=%s output=%s distance=%s" %
                    (inputs, out_buffer, self.getInputValue('distanceEau')))

                bufferList.append(out_buffer)
                j += 1
        else:
            for inputs in vector_List:
                out_buffer = 'buffer' + str(j)
                # v.buffer - Creates a buffer around vector features of given
                # type.
                self.cmd(
                    "v.buffer --quiet --overwrite input=%s output=%s distance=%s" %
                    (inputs, out_buffer, self.getInputValue('distanceEau')))

                bufferList.append(out_buffer)
                j += 1
        delta = datetime.now() - stime_process
        LOGGER.info('Buffer on {0} \n'.format(delta))

        stime_process = datetime.now()
        # v.overlay - Overlays two vector maps - or: also known as 'union' in
        # GIS (only for atype=area)
        self.cmd(
            "v.overlay --quiet ainput=%s binput=%s operator=or output=union_buffer olayer=1,0,0" %
            (bufferList[0], bufferList[1]))

        delta = datetime.now() - stime_process
        LOGGER.info('Overlay on {0} \n'.format(delta))

        # v.db.addcolumn - Adds one or more columns to the attribute table
        # connected to a given vector map.
        self.cmd(['v.db.addcolumn', '--quiet',
                  'map=union_buffer', 'columns=disolve'])

        stime_process = datetime.now()
        # v.dissolve - Dissolves boundaries between adjacent areas sharing a
        # common category number or attribute.
        self.cmd(
            "v.dissolve --quiet --overwrite input=union_buffer column=disolve output=disolved_buffer")

        delta = datetime.now() - stime_process
        LOGGER.info('Dissolve on {0} \n'.format(delta))
        #######################################################################
        # Raster processing
        #######################################################################
        stime_process = datetime.now()

        dem_path = layers_path + self.getInputValue('dem_layer')

        # r.external - Links GDAL supported raster data as a pseudo GRASS
        # raster map.
        self.cmd(
            "r.external --overwrite --quiet -o input=%s band=1 output=dem" %
            (dem_path))

        delta = datetime.now() - stime_process
        LOGGER.info('Ratser import on {0} \n'.format(delta))

        # g.region - Manages the boundary definitions for the geographic
        # region. set resolution to 5m
        self.cmd("g.region --quiet raster=dem res=5")

        stime_process = datetime.now()
        # r.in.gdal - Imports raster data into a GRASS raster map using GDAL
        # library.
        self.cmd(
            "r.resamp.interp --quiet --overwrite method=bicubic input=dem output=resampled")

        delta = datetime.now() - stime_process
        LOGGER.info('Resample 5m on {0} \n'.format(delta))

        stime_process = datetime.now()
        # v.to.rast - Converts (rasterize) a vector map into a raster map.
        self.cmd(
            "v.to.rast --quiet input=disolved_buffer output=raster_boundary use=val value=1")

        delta = datetime.now() - stime_process
        LOGGER.info('vect to Raster on {0} \n'.format(delta))

        # r.mask - Creates a MASK for limiting raster operation.
        self.cmd("r.mask --quiet --overwrite raster=raster_boundary")

        stime_process = datetime.now()
        # r.slope.aspect - Generates raster maps of slope, aspect, curvatures
        # and partial derivatives from an elevation raster map.
        self.cmd(
            "r.slope.aspect --quiet --overwrite precision=CELL zscale=1 min_slope=0 elevation=resampled slope=slope")

        delta = datetime.now() - stime_process
        LOGGER.info('Slope on {0} \n'.format(delta))

        stime_process = datetime.now()
        # file indecating the classes to be used on the classification
        # algorithme located in "layers_path"
        reclass_file = layers_path + 'reclass_file.txt'
        # r.reclass - Reclassify raster map based on category values.
        self.cmd(
            "r.reclass --quiet --overwrite input=slope rules=%s output=reclassified" %
            (reclass_file))

        delta = datetime.now() - stime_process
        LOGGER.info('Reclass on {0} \n'.format(delta))

        stime_process = datetime.now()
        # r.to.vect - Converts a raster map into a vector map.
        self.cmd(
            "r.to.vect --quiet --overwrite -s input=reclassified type=area output=zonage_out")

        delta = datetime.now() - stime_process
        LOGGER.info('Raster to vect on {0} \n'.format(delta))

        stime_process = datetime.now()
        # v.clean - Toolset for cleaning topology of vector map.
        self.cmd("v.clean --quiet input=zonage_out tool=rmarea output=clean_zonage_out threshold=1000")

        delta = datetime.now() - stime_process
        LOGGER.info('clean vect on {0} \n'.format(delta))

        final_out = 'clean_zonage_out'

        # g.region -a n=6799625.0 s=6749315.0 e=258895.0 w=212970.0 res=100
        self.cmd("g.region --quiet -a res=100")

        if self.getInputValue('simplifier'):
            stime_process = datetime.now()

            # v.generalize - Performs vector based generalization. using rduction method
            self.cmd("v.generalize --quiet --overwrite input=%s method=reduction threshold=6 slide=0.5 iterations=1 -l output=simplified_zonage_out" %(final_out))

            delta = datetime.now() - stime_process
            LOGGER.info('Generalize on {0} \n'.format(delta))

            final_out = 'simplified_zonage_out'

        #######################################################################
        # Exporting
        #######################################################################
        CurrentDateTime = time.strftime("%Y%m%d-%H%M%S")
        dir_out = tmp_dir + 'ShapeFile_' + CurrentDateTime

        # v.out.ogr - Exports a vector map layer to any of the supported
        # OGR vector formats.
        self.cmd(
            "v.out.ogr --quiet --overwrite -s -e format=ESRI_Shapefile input=%s output=%s" %
            (final_out, dir_out))


        stime_process = datetime.now()

        shape_out = dir_out + '/' + final_out + '.shp'

        # Get values from inputs
        outputSrs = self.getInputValue('outputSrs')
        host = self.getInputValue('host')
        port = self.getInputValue('port')
        dbname = self.getInputValue('dbname')
        user = self.getInputValue('user')
        password = self.getInputValue('password')
        layers_name_out =  'zonage_pente_bretagne'

        geoserver_login = self.getInputValue('geoserver_user')
        geoserver_pass = self.getInputValue('geoserver_pass')
        # Concatinate database server informations
        pgsql = 'PostgreSQL PG:"host={0} port={1} dbname={2}\
        password={3} user={4}"'.format(host, port, dbname, password, user)

        # Concatinate the command ogr2ogr to dump the output shapefile to the database
        command = 'ogr2ogr -overwrite -progress --config PG_USE_COPY YES -f {0} {1} -nlt MULTIPOLYGON -lco SCHEMA=public -lco GEOMETRY_NAME=geom -lco FID=id -nln {2} -s_srs EPSG:2154 -t_srs {3}'.format(pgsql, shape_out, layers_name_out, outputSrs)

        p = os.popen(command,"r").readline()

        LOGGER.info('{0} \n'.format(p))

        delta = datetime.now() - stime_process
        LOGGER.info('Dump shapefile to postgis on : {0} \n'.format(delta))

        # configurate the request header and autentification
        headers = {'Content-type': 'text/xml',}

        auth=requests.auth.HTTPBasicAuth(geoserver_login, geoserver_pass)


        # Update datastore
        url = 'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/epandage/datastores/{0}'.format(layers_name_out)
        datastore = "<dataStore><enabled>true</enabled><update>overwrite</update></dataStore>"

        requests.put(url=url, headers=headers, data=datastore, auth=auth)

        # Change the Native and the Declared SRS of the published layer on geoserver as the outputSrs
        url = 'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/epandage/datastores/{0}/featuretypes/{0}?recalculate=nativebbox,latlonbbox'.format(layers_name_out)

        data_feature = '<featureType><enabled>true</enabled><nativeCRS>{0}</nativeCRS><srs>{0}</srs><projectionPolicy>FORCE_DECLARED</projectionPolicy></featureType>'.format(outputSrs)

        requests.put(url=url, headers=headers, data=data_feature, auth=auth)

        if self.getInputValue('supprimer'):
            if os.path.exists(dir_out):
                    shutil.rmtree(dir_out)

        delta = datetime.now() - stime
        temps_sec = 'Total processing time: {0} \n'.format(delta)
        LOGGER.info(temps_sec)

        # Send mail
        email = self.getInputValue('email')

        if email is not None:
          self.cmd(scripts_path + "mailSender.sh %s %s" % (email, delta))

        return

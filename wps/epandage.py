from pywps.Process import WPSProcess
import time
from datetime import datetime
import json
import os
import tempfile
import hashlib
import yaml
import logging


class Process(WPSProcess):
    '''
    TODO : Indicate, on the execute methode, the right path to your configuration file "epandage_process.conf"
    contaning the WFS URL's and names to deal with.
    '''

    def __init__(self):

        # init process
        WPSProcess.__init__(
            self,
            identifier="epandage",
            title="Service WEB de calcul des SPE",
            version="1.0",
            storeSupported=True,
            statusSupported=True,
            grassLocation=True,
            abstract="Service WPS pour le calcul des superfice des parcelles pottentiellement epandables (SPE)")

        #######################################################################
        # Inputs
        #######################################################################
        self.parcelList = self.addLiteralInput(identifier="parcelList",
                                               title="Identifiant(s) de(s) parcelle(s) - attributs 'ilot_cdn' (separateur: virgule)",
                                               default="361664,361665,361666,361667,361669",
                                               type="",
                                               minOccurs=1)

        self.userData = self.addComplexInput(
            identifier="userData",
            title="Zones rentrees manuellement par l'utilisateur (JSON format)",
            minOccurs=0,
            formats=[
                {
                    "mimeType": "text/plain"}])

        self.distanceEau_7 = self.addLiteralInput(
            identifier="distanceEau_7",
            title="Distance minimale (m) du cours d'eau",
            default="35",
            allowedValues=['35'],
            type="")

        self.distanceEau_10 = self.addLiteralInput(
            identifier="distanceEau_10",
            title="Distance minimale (m) du cours d'eau",
            default="35",
            allowedValues=[
                '35',
                '100'],
            type="")

        self.distanceEau_15 = self.addLiteralInput(
            identifier="distanceEau_15",
            title="Distance minimale (m) du cours d'eau",
            default="100",
            allowedValues=['100'],
            type="")

        self.distancePisci = self.addLiteralInput(
            identifier="distanceEauPisciculture",
            title="Distance minimale (m) du cours d'eau si pisciculture en amont",
            default="50",
            type="")

        self.distanceBati = self.addLiteralInput(
            identifier="distanceBati",
            title="Distance minimale (m) du batis dur",
            default="10",
            type="")

        self.distanceCamping = self.addLiteralInput(
            identifier="distanceCamping",
            title="Distance minimale (m) des aires de camping",
            default="10",
            type="")

        self.distanceStade = self.addLiteralInput(
            identifier="distanceStade",
            title="Distance minimale (m) des stades",
            default="10",
            type="")

        self.distanceForage = self.addLiteralInput(
            identifier="distanceForage",
            title="Distance minimale (m) des forages, puits, sources non destinees a la consomation humaine",
            default="35",
            type="")

        self.distanceCaptage = self.addLiteralInput(
            identifier="distanceCaptageEau",
            title="Distance minimale (m) des captages d'eau a distination humaine",
            default="50",
            type="")

        self.distancePlage = self.addLiteralInput(
            identifier="distancePlage",
            title="Distance minimale (m) des baignades declarees et plages",
            default="50",
            type="")

        self.distanceZC = self.addLiteralInput(
            identifier="distanceZC",
            title="Distance minimale (m) des zones conchylicoles",
            default="500",
            type="")

        self.distanceZH = self.addLiteralInput(
            identifier="distanceZH",
            title="Distance minimale (m) des zones humides",
            default="0",
            type="")

        self.toleranceBuffer = self.addLiteralInput(
            identifier="toleranceBuffer",
            title="Distance maximale entre l'arc theoriques et les segements du polygon",
            default="0.01",
            type="")

        self.outputFormat = self.addLiteralInput(
            identifier="outputFormat",
            title="Format de sortie",
            default="CSV",
            allowedValues=[
                'GeoJSON',
                'GML',
                'CSV'],
            type="")

        self.outputSrs = self.addLiteralInput(
            identifier="outputSrs",
            title="EPSG de la couche en sortie",
            allowedValues=[
                'EPSG:4326',
                'EPSG:3857',
                'EPSG:2154'],
            default="EPSG:4326",
            type="")

        #######################################################################
        # Outputs
        #######################################################################
        self.outputData = self.addComplexOutput(
            identifier="outputData",
            title="Tableau (CSV) ou couche vecteur (GML/Geojson) en sortie des superficies potentiellement epandables",
            formats=[
                {
                    "mimeType": "text/xml"}])

        self.processTime = self.addLiteralOutput(identifier="processTime",
                                                 title="Temps de traitement",
                                                 type="")

    def execute(self):
        from grass.script import core as grass

        LOGGER = logging.getLogger(__name__)

        stime = datetime.now()

        CurrentDateTime = time.strftime("%Y%m%d-%H%M%S")
        stime = datetime.now()

        tmp = tempfile.gettempdir()
        tmp_dir = tmp + '/tmp_epandage/'

        # Creat epandage tmp dirrectory if not exist
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        # Delete all file in /tmp/epandage directory older than n_days
        now = time.time()
        n_days = 0
        cutoff = now - (n_days * 86400)
        files = os.listdir(tmp_dir)
        for xfile in files:
            if os.path.isfile(tmp_dir + xfile):
                t = os.stat(tmp_dir + xfile)
                c = t.st_ctime
                # delete file if older than 3 days
                if c < cutoff:
                    os.remove(tmp_dir + xfile)

        # Point to the folder 'scripts' (two folders above 'epandage.py')
        current_path = os.path.realpath(__file__)
        scripts_path = os.path.abspath(
            os.path.join(
                current_path,
                '..',
                '..',
                'scripts')) + '/'

        # Load config file
        config_file = '/home/saadni/private_conf/epandage_process.conf'
        read_file = open(config_file).read()
        config_in = json.dumps(json.loads(read_file))  # return a string

        # convert str to dict
        config_in = yaml.load(config_in)

        # Get layers list {number : [URL, NameSpace, Distance]}
        layerList = config_in['layerList']

        # Change layerList distance identifier to input value :
        # getInputValue(distance)
        for key, val in layerList.iteritems():
            distance = val[2]
            if distance[:8] == 'distance':
                layerList[key][2] = self.getInputValue(distance)

        layerList['1'][2]
        # RPG Nominatif layer WFS URL
        RPG_layer = config_in['RPG_layer']
        url_par = RPG_layer['url']
        name_par = RPG_layer['name']
        att_name = RPG_layer['att_name']

        parcellesId = self.getInputValue('parcelList')

        idList = parcellesId.split(",")
        ids = ''.join(map(str, idList))
        idList_hash = str(int(hashlib.md5(ids).hexdigest(), 16))
        path_to_file = tmp_dir + name_par + '_' + idList_hash + '.geojson'

        # try the WFS filtered request 3 times
        for t in range(3):
            try:
                # Get WFS parcelles layer by attributes (default srs =
                # EPSG:2154)
                self.cmd(
                    scripts_path + "GetWFSLayer_filter.py -u %s -n %s -p %s -a %s -f %s" %
                    (url_par, name_par, path_to_file, att_name, parcellesId))
                break
            except:
                print 'Timeout !'

        # Import data into GRASS using v.in.ogr
        self.cmd(
            "v.in.ogr --quiet -o input=%s output=parcelle" %
            (path_to_file))

        grass.run_command(
            'v.db.addcolumn',
            quiet=True,
            map='parcelle',
            columns='Parcelle_ha double precision')
        self.cmd(
            "v.to.db --quiet map=parcelle columns=Parcelle_ha option=area unit=hectares")

        area_ha = self.cmd(
            scripts_path +
            "GetGeojsonBboxArea.py -d %s" %
            (path_to_file))

        # area max hectars
        max_area = 20000

        if int(area_ha) < max_area:
            # Get geojson file extent
            bbox = self.cmd(
                scripts_path +
                "GetGeojsonBbox.py -d %s" %
                (path_to_file))

            # add offset of 500m
            off = 500
            bb = bbox.split(",")
            bb = tuple([float(xy) for xy in bb])
            # add offset of 500m
            box = (str(bb[0] - off), str(bb[1] - off),
                   str(bb[2] + off), str(bb[3] + off))
            box_str = ''.join(box)

            k = 0
            ogrInList = []
            dist_list = []
            for key, val in sorted(layerList.iteritems()):
                url = val[0]
                name = val[1]
                dist = val[2]

                # generate a unique name using the layernName & the bbox
                bb_arr_id = str(int(hashlib.md5(box_str).hexdigest(), 16))
                pathName = tmp_dir + name + '_' + bb_arr_id + ".geojson"
                data = 'data' + str(k)

                # try the WFS request 3 times
                for s in range(3):
                    try:
                        # Download layer using WFS Bonding box filter and add
                        # offset of 500m (flag '+o')
                        self.cmd(
                            scripts_path + "GetWFSLayer_bbox_REST.py +u %s +n %s +p %s +b %s +o" %
                            (url, name, pathName, bbox))
                        break
                    except:
                        LOGGER.info('GetWFSLayer_bbox {0} Request Error !'.format(name))

                # Test si le ficher vecteur n'est pas vide
                with open(pathName) as data_file:
                    in_data = json.load(data_file)
                    nfeatures = in_data['totalFeatures']
                    if not nfeatures == 0:
                        # Import data into GRASS using v.in.ogr (-t : don't
                        # import table)
                        self.cmd(
                            "v.in.ogr --quiet -o input=%s output=%s" %
                            (pathName, data))
                        ogrInList.append(data)
                        dist_list.append(dist)
                        k += 1

            #########################################
            # Buffer
            #########################################
            bufferList = []
            j = 0
            slope_input = None
            for inputs in ogrInList:
                out_buffer = inputs + str(j)
                distance = dist_list[j]
                if distance == 'slope':
                    slope_input = inputs
                else:
                    # v.buffer - Creates a buffer around vector features of given type.
                    grass.run_command(
                        'v.buffer',
                        quiet=True,
                        input=inputs,
                        output=out_buffer,
                        distance=distance,
                        tolerance=self.getInputValue('toleranceBuffer'))

                    bufferList.append(out_buffer)
                    j += 1

            #########################################
            # Difference
            #########################################
            overlayList = []
            i = 0
            try:
                for inputs in bufferList:
                    outDiff = inputs + 'Diff' + str(i)
                    # make the first overlay for the first buffer 'data00'
                    if inputs == 'data00':
                        overlayList.append(outDiff)
                        # v.overlay - Overlays two vector maps - not: features
                        # from ainput not overlayed by features from binput
                        self.cmd(
                            "v.overlay --quiet ainput=parcelle binput=%s operator=not output=%s olayer=0,1,0" %
                            (inputs, overlayList[i]))
                    # make the other overlay for the result of the first buffer
                    else:
                        i += 1
                        outDiff = inputs + 'Diff' + str(i)
                        overlayList.append(outDiff)
                        # v.overlay - Overlays two vector maps - not: features
                        # from ainput not overlayed by features from binput
                        self.cmd(
                            "v.overlay --quiet ainput=%s binput=%s operator=not output=%s olayer=0,1,0" %
                            (overlayList[i - 1], inputs, overlayList[i]))
                # Put the right value on final_out
                if len(bufferList) == 0:
                    final_out = 'parcelle'
                elif len(bufferList) == 1:
                    final_out = overlayList[0]
                else:
                    final_out = overlayList[i]
            except:
                final_out = None

            # if buffer do not overlay completely the parcelles layer (layerOut
            # exist)
            if final_out is not None:

                if slope_input is not None:
                    # v.extract - Selects vector objects from an existing
                    # vector map and creates a new map containing only the
                    # selected objects.
                    grass.run_command(
                        'v.extract',
                        quiet=True,
                        input=slope_input,
                        output='extracted_3',
                        where='value = "3"')

                    # v.overlay - Overlays two vector maps - not: features from
                    # ainput not overlayed by features from binput
                    self.cmd(
                        "v.overlay --quiet ainput=%s binput=extracted_3 operator=not output=out_overlay_3 olayer=0,1,0" %
                        (final_out))

                    final_out = 'out_overlay_3'

                    if self.getInputValue('distanceEau_10') == '100':

                        # v.extract - Selects vector objects from an existing
                        # vector map and creates a new map containing only the
                        # selected objects.
                        grass.run_command(
                            'v.extract',
                            quiet=True,
                            input=slope_input,
                            output='extracted_2',
                            where='value = "2"')

                        # v.overlay - Overlays two vector maps - not: features
                        # from ainput not overlayed by features from binput
                        self.cmd(
                            "v.overlay --quiet ainput=%s binput=extracted_2 operator=not output=out_overlay_3_2 olayer=0,1,0" %
                            (final_out))

                        final_out = 'out_overlay_3_2'

                # Overlay with usertacerData
                userData = self.getInputValue('userData')
                # Modifay the JSON input to a GeoJSON file (default srs =
                # EPSG:3857)
                if userData is not None:
                    self.cmd(scripts_path +
                             "jsonModif.py -in %s -dir %s -out %s" %
                             (userData, tmp_dir, CurrentDateTime))

                    outMoins = tmp_dir + 'Moins_' + CurrentDateTime
                    outPlus = tmp_dir + 'Plus_' + CurrentDateTime

                    outMoins_2154 = outMoins + '.geojson'
                    outPlus_2154 = outPlus + '.geojson'

                    if os.path.exists(outMoins):
                        # Reproject userData from EPSG:4326 to EPSG:2154
                        self.cmd(
                            "ogr2ogr -f GeoJSON -s_srs EPSG:4326 -t_srs EPSG:2154 %s %s" %
                            (outMoins_2154, outMoins))
                        # Remove tmp files
                        os.remove(outMoins)
                        # Import data into GRASS using v.in.ogr
                        self.cmd(
                            "v.in.ogr --quiet -o input=%s output=userLayerMoins" %
                            (outMoins_2154))
                        # v.overlay - Overlays two vector maps - not: features
                        # from ainput not overlayed by features from binput
                        self.cmd(
                            "v.overlay --quiet ainput=%s binput=userLayerMoins operator=not output=OutFinale olayer=0,1,0" %
                            (final_out))
                        # Remove tmp file
                        os.remove(outMoins_2154)
                        final_out = 'OutFinale'

                        if os.path.exists(outPlus):
                            # Reproject userData from EPSG:4326 to EPSG:2154
                            self.cmd(
                                "ogr2ogr -f GeoJSON -s_srs EPSG:4326 -t_srs EPSG:2154 %s %s" %
                                (outPlus_2154, outPlus))
                            # Remove tmp files
                            os.remove(outPlus)
                            # Import data into GRASS using v.in.ogr
                            self.cmd(
                                "v.in.ogr --quiet -o input=%s output=userLayerPlus" %
                                (outPlus_2154))

                            # v.overlay - Overlays two vector maps - not:
                            # features from ainput not overlayed by features
                            # from binput
                            self.cmd(
                                "v.overlay --quiet ainput=OutFinale binput=userLayerPlus operator=or output=OutFinale2 olayer=1,1,0")
                            # v.db.dropcolumn - Drops a column from the
                            # attribute table connected to a given vector map.
                            grass.run_command(
                                'v.db.dropcolumn',
                                quiet=True,
                                map='OutFinale2',
                                columns='a_cat,b_cat')

                            # Remove tmp file
                            os.remove(outPlus_2154)
                            final_out = 'OutFinale2'

                    elif os.path.exists(outPlus):
                        # Reproject userData from EPSG:4326 to EPSG:2154
                        self.cmd(
                            "ogr2ogr -f GeoJSON -s_srs EPSG:4326 -t_srs EPSG:2154 %s %s" %
                            (outPlus_2154, outPlus))
                        # Remove tmp files
                        os.remove(outPlus)
                        # Import data into GRASS using v.in.ogr
                        self.cmd(
                            "v.in.ogr --quiet -o input=%s output=userLayerPlus" %
                            (outPlus_2154))
                        # v.overlay - Overlays two vector maps - not: features
                        # from ainput not overlayed by features from binput
                        self.cmd(
                            "v.overlay --quiet ainput=%s binput=userLayerPlus operator=or output=OutFinale3 olayer=1,1,0" %
                            (final_out))
                        # v.db.dropcolumn - Drops a column from the attribute
                        # table connected to a given vector map.
                        grass.run_command(
                            'v.db.dropcolumn',
                            quiet=True,
                            map='OutFinale3',
                            columns='a_cat,b_cat')

                        # Remove tmp file
                        os.remove(outPlus_2154)
                        final_out = 'OutFinale3'

                # v.db.addcolumn - Adds one or more columns to the attribute
                # table connected to a given vector map.
                grass.run_command(
                    'v.db.addcolumn',
                    quiet=True,
                    map=final_out,
                    columns='SPE_ha double precision')

                # v.to.db - Populates attribute values from vector features.
                self.cmd(
                    "v.to.db --quiet map=%s columns=SPE_ha option=area unit=hectares" %
                    (final_out))

                #########################################
                # Exporting
                #########################################
                if self.getInputValue('outputFormat') == "GeoJSON":
                    # v.out.ogr - Exports a vector map layer to any of the
                    # supported OGR vector formats.
                    self.cmd(
                        "v.out.ogr --quiet --overwrite -s format=GeoJSON input=%s output=out.geojson" %
                        (final_out))
                    # Reproject userData from EPSG:2154 to outputSrs
                    self.cmd(["ogr2ogr",
                              "-f",
                              "GeoJSON",
                              "-s_srs",
                              "EPSG:2154",
                              "-t_srs",
                              self.getInputValue('outputSrs'),
                              "ZPE.geojson",
                              "out.geojson"])
                    fileOut = "ZPE.geojson"
                elif self.getInputValue('outputFormat') == "GML":
                    # v.out.ogr - Exports a vector map layer to any of the
                    # supported OGR vector formats.
                    self.cmd(
                        "v.out.ogr --quiet --overwrite -s format=GML input=%s output=out.gml" %
                        (final_out))
                    # Reproject userData from EPSG:2154 to outputSrs
                    self.cmd(["ogr2ogr",
                              "-f",
                              "GML",
                              "-s_srs",
                              "EPSG:2154",
                              "-t_srs",
                              self.getInputValue('outputSrs'),
                              "ZPE.gml",
                              "out.gml"])
                    fileOut = "ZPE.gml"
                else:
                    # db.out.ogr - Exports attribute tables into various
                    # formats.
                    self.cmd(
                        "db.out.ogr --quiet --overwrite input=%s format=CSV output=ZPE.csv" %
                        (final_out))
                    fileOut = "ZPE.csv"

                # affecting output data
                self.outputData.setValue(fileOut)

                # affecting output time
                delta = datetime.now() - stime
                temps_sec = 'Temps de traitement: {0} \n'.format(delta)
                LOGGER.info(temps_sec)

                self.processTime.setValue(temps_sec)



            # if buffer overlay completely the parcelles layer (if final_out is None)
            else:
                # Change the variable "outputData" from ComplexOutput to
                # LiteralOutput
                self.outputData = self.addLiteralOutput(
                    identifier="outputData", title="Message d'erreur", type='')

                # affecting output time
                delta = datetime.now() - stime
                temps_sec = 'Temps de traitement: {0} \n'.format(delta)
                LOGGER.info(temps_sec)

                self.processTime.setValue(temps_sec)

                self.outputData.setValue(
                    "Il n'y a pas de zone potentiellement epandable pour vos parcelles")
        # if the area to process is bigger to max_area (ha)
        else:

            # Change the variable "outputData" from ComplexOutput to
            # LiteralOutput
            self.outputData = self.addLiteralOutput(identifier="outputData",
                                                    title="Message d'erreur",
                                                    type='')
            self.outputData.setValue(
                "Le perimetre de calcule est superieur a " +
                str(max_area) +
                " ha, veillez choisir des parcelles plus proches les unes des autres")

        return

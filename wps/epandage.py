from pywps.Process import WPSProcess
import time
from datetime import datetime
import json
import os
import hashlib
import yaml
import logging

import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex


class Process(WPSProcess):
    """
    TODO: In the condition, if userData send a "zone epandable plus" (line 642 and 650)
    The overlay process (line 658 and 685) should dissolve the added polygones with the
    original polygone (parcelle) to creat one feature instead of two.
    """

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
            abstract='''Service WPS pour le calcul des superfice des parcelles
            pottentiellement epandables (SPE)''')

        #######################################################################
        # Inputs
        #######################################################################
        self.parcelList = self.addLiteralInput(
            identifier="parcelList",
            title="Identifiant(s) de(s) parcelle(s) - attributs 'ilot_cdn' (separateur: virgule)",
            default="361667",
            type="",
            minOccurs=1)

        self.userData = self.addComplexInput(
            identifier="userData",
            title="Zones rentrees manuellement par l'utilisateur (JSON format)",
            minOccurs=0,
            formats=[
                {
                    "mimeType": "text/plain"}])

        self.distanceEau_0 = self.addLiteralInput(
            identifier="distanceEau_0",
            title="Distance minimale (m) du cours d'eau lorsque la valeur de pente moins de 7% a un max de 100m du cours d'eau",
            default="35",
            type="")

        self.distanceEau_7 = self.addLiteralInput(
            identifier="distanceEau_7",
            title="Distance minimale (m) du cours d'eau lorsque la valeur de pente >= 7% a un max de 100m du cours d'eau",
            default="35",
            type="")

        self.distanceEau_10 = self.addLiteralInput(
            identifier="distanceEau_10",
            title="Distance minimale (m) du cours d'eau lorsque la valeur de pente >= 10% a un max de 100m du cours d'eau",
            default="35",
            type="")

        self.distanceEau_15 = self.addLiteralInput(
            identifier="distanceEau_15",
            title="Distance minimale (m) du cours d'eau lorsque la valeur de pente >= 15% a un max de 100m du cours d'eau",
            default="100",
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

        Process_start_time = time.strftime("%Y-%m-%d_%H:%M:%S")
        LOGGER.info("\nStart a new Execute at : {0}\n".format(Process_start_time))
#        LOGGER.info('\n%s\n' % (cmd))

        stime = datetime.now()

        # Creat a date suffix
        CurrentDateTime = time.strftime("%Y%m%d-%H%M%S")
        stime = datetime.now()

        # Point to the folder where manifest.json is
        current_path = os.path.realpath(__file__)
        config_path = os.path.abspath(
            os.path.join(
                current_path,
                '..',
                '..'))

        manifest_path = '%s/manifest.json' % (config_path)

        # Load manifest file
        read_manifest = open(manifest_path).read()
        manifest_conf = json.dumps(json.loads(read_manifest))
        manifest_conf = yaml.load(manifest_conf)

        # Get cumputer's tmp directory and creat "tmp_epandage" folder in
        directories = manifest_conf['directories']
        tmp_dir = directories['epandage_tmp_dir']

        # Creat epandage tmp dirrectory if not exist
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        # Delete all file in /tmp/epandage directory older than n_days
        now = time.time()

        # Get from manifest.json the number of days to keep layers on cash
        n_days = manifest_conf['epandage_n_dayes_cash']

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
        scripts_path = "%s/" % (os.path.abspath(
            os.path.join(
                current_path,
                '..',
                '..',
                'scripts')))

        # Get epandage_config_file from manifest.json
        epandage_config_file = directories['epandage_config_layers']

        # Load config file
        read_file = open(epandage_config_file).read()
        config_in = json.dumps(json.loads(read_file))
        # convert str to dict
        config_in = yaml.load(config_in)

        # Get layers list {number : [URL, NameSpace, Distance]}
        layerDict = config_in['layerDict']

        # Change layerDict distance identifier to input value :
        # getInputValue(distance)
        for key, val in layerDict.iteritems():
            distance = val['distance_att']
            if distance[:8] == 'distance':
                layerDict[key]['distance_att'] = self.getInputValue(distance)

        #LOGGER.info('\n%s\n' % (layerDict))
        #########################################
        # Get Parcelles layer
        #########################################

        # RPG Nominatif layer WFS URL
        RPG_layer = config_in['RPG_layer']
        url_par = RPG_layer['url']
        name_par = RPG_layer['name']
        att_name = RPG_layer['att_name']
        login = RPG_layer['login']
        password =  RPG_layer['password']

        parcellesId = self.getInputValue('parcelList')

        idList = parcellesId.split(",")
        ids = ''.join(map(str, idList))
        idList_hash = hashlib.md5(ids).hexdigest()
        path_to_file = tmp_dir + name_par + '_' + idList_hash

        results = []
        # try the WFS filtered request 3 times
        for t in range(3):
            try:
                # Get WFS parcelles layer by attributes (default srs =
                # EPSG:2154)
                commande = "%sGetWFSLayer_filter.py -u %s -l %s -pwd %s -n %s -d %s -a %s -f %s" % (
                    scripts_path, url_par, login, password, name_par, path_to_file, att_name, parcellesId)
                p = subprocess.Popen(
                    shlex.split(commande),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                out = p.communicate()
                break
            except:
                LOGGER.info(
                    'GetWFSLayer_filter request Error: {0} \n'.format(out))

        # Import data into GRASS using v.in.ogr
        self.cmd(
            "v.in.ogr --quiet -o input=%s output=parcelle" %
            (path_to_file))

        grass.run_command(
            'v.db.addcolumn',
            quiet=True,
            map='parcelle',
            columns='surf_ilot_ha double precision')
        self.cmd(
            "v.to.db --quiet map=parcelle columns=surf_ilot_ha option=area unit=hectares")

        #########################################
        # Check the bbox size of Parcelle layer
        #########################################

        # Get the bbox of parcelle layer
        area_ha = self.cmd(
            scripts_path +
            "GetGeojsonBboxArea.py -d %s" %
            (path_to_file))

        # area max hectars
        max_area = 20000
        if int(area_ha) <= max_area:
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

            ###################################################################
            # Get the other layers depending to the bbox size of Parcelle layer
            ###################################################################
            def call_async_process_grass(cmd):
                """ This methode allows to run a separate thread. """
                # subprocess.call(shlex.split(cmd))  # This will block until
                # cmd finishes
                p = grass.Popen(
                    shlex.split(cmd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                out, err = p.communicate()
                return (out, err)

            def delete_feilds_suffix(geojson_in, prefix):
                '''
                This methode rename all fields with deleting the input prefix.
                Inputs:
                    geojson_in : path to the geojson file (String)
                    prefix : prefix to be delated (String)
                '''
                read_file = open(geojson_in).read()
                vect_dict = json.loads(read_file)
                n = 0
                # Iterate all the features
                for fe in  vect_dict['features']:
                    properties = fe['properties']
                    # Delate the prefix on all the feilds names
                    corrected_dict = {}
                    for x in properties.keys():
                        corrected_dict[x.replace(prefix, '')] = properties[x]

                    # Or do it in one line : corrected_dict = {x.replace(prefix, '') : \
                    #properties[x] for x in properties.keys()}
                    vect_dict['features'][n]['properties'] = corrected_dict
                    n += 1
                with open(geojson_in, 'w') as f:
                    json.dump(vect_dict, f)
                return

            # Count computer's CPU
            n_cpu = multiprocessing.cpu_count()
            pool = ThreadPool(n_cpu)

            for key, val in sorted(layerDict.iteritems()):
                url = val['url']
                name = val['name']
                login = val['login']
                password = val['password']
                results = []
                # generate a unique name using the layernName & the bbox
                bb_arr_id = hashlib.md5(box_str).hexdigest()
                pathName = tmp_dir + name + '_' + bb_arr_id

                # try the WFS request 3 times
                for s in range(3):
                    try:
                        # Download layer using WFS Bonding box filter and add
                        # offset of 500m (flag '+o')
                        if login and password:
                            cmd = scripts_path + \
                                "GetWFSLayer_bbox_REST.py +u %s +n %s +d %s +b %s +o +l %s +pwd %s" % (url,
                                                                                                       name,
                                                                                                       pathName,
                                                                                                       bbox,
                                                                                                       login,
                                                                                                       password)
                        else:
                            cmd = scripts_path + \
                                "GetWFSLayer_bbox_REST.py +u %s +n %s +d %s +b %s +o" % (url,
                                                                                         name,
                                                                                         pathName,
                                                                                         bbox)

                        # Run the command asynchronously on full CPU capacity
                        results.append(
                            pool.apply_async(
                                call_async_process_grass, (cmd,)))
                        break
                    except:
                        # Display the command stdout error
                        for result in results:
                            out, err = result.get()
                            LOGGER.info(
                                'GetWFSLayer_bbox request Error:  {0}\n'.format(err))

                # Add the downloaded files paths to the layerDict dict
                layerDict[key]['pathname'] = pathName

            # Close the pool and wait for each running task to complete
            pool.close()
            pool.join()

            #########################################
            # OGR Inputs
            #########################################
            # init vars
            pool = ThreadPool(n_cpu)
            results = []
            ogrInList = []
            dist_list = []
            pathName_list = []
            d = 0
            # Test if the vector downloaded is not empty, add it to the process
            # list
            for key, val in sorted(layerDict.iteritems()):
                dist = val['distance_att']
                pathName = val['pathname']
                with open(pathName) as data_file:
                    in_data = json.load(data_file)
                    nfeatures = in_data['totalFeatures']
                    if not nfeatures == 0:
                        data = 'data' + str(d)

                        # Import data into GRASS using v.in.ogr (-t : don't
                        # import table)
                        cmd_in_ogr = "v.in.ogr --quiet -o input=%s output=%s" % (
                            pathName, data)

                        # Run the command asynchronously on full CPU capacity
                        results.append(
                            pool.apply_async(
                                call_async_process_grass, (cmd_in_ogr,)))

                        # Populate inputs and distances lists
                        ogrInList.append(data)
                        dist_list.append(dist)
                        pathName_list.append(pathName)
                        d += 1

            # Close the pool and wait for each running task to complete
            pool.close()
            pool.join()

            #########################################
            # Buffer
            #########################################
            pool = ThreadPool(n_cpu)
            results = []
            bufferList = []
            j = 0
            slope_input = None
            for inputs in ogrInList:
                out_buffer = inputs + str(j)
                distance = dist_list[j]
                if distance == 'slope':
                    slope_input = inputs
                else:
                    # v.buffer - Creates a buffer around vector features of
                    # given type.
                    cmd_buffer = "v.buffer --quiet input=%s output=%s distance=%s tolerance=%s" % (
                        inputs, out_buffer, distance, self.getInputValue('toleranceBuffer'))

                    # Run the command asynchronously on full CPU capacity
                    results.append(
                        pool.apply_async(
                            call_async_process_grass, (cmd_buffer,)))

                    # Add buffer outputs to the list
                    bufferList.append(out_buffer)
                    j += 1

            # Close the pool and wait for each running task to complete
            pool.close()
            pool.join()

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
                    try:
                        self.cmd(
                            "v.overlay --quiet ainput=%s binput=extracted_3 operator=not output=out_overlay_3 olayer=0,1,0" %
                            (final_out))

                        final_out = 'out_overlay_3'
                    except:
                        pass

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
                        try:
                            self.cmd(
                                "v.overlay --quiet ainput=%s binput=extracted_2 operator=not output=out_overlay_3_2 olayer=0,1,0" %
                                (final_out))

                            final_out = 'out_overlay_3_2'
                        except:
                            pass

                    if self.getInputValue('distanceEau_7') == '100':

                        # v.extract - Selects vector objects from an existing
                        # vector map and creates a new map containing only the
                        # selected objects.
                        grass.run_command(
                            'v.extract',
                            quiet=True,
                            input=slope_input,
                            output='extracted_1',
                            where='value = "1"')

                        # v.overlay - Overlays two vector maps - not: features
                        # from ainput not overlayed by features from binput
                        try:
                            self.cmd(
                                "v.overlay --quiet ainput=%s binput=extracted_1 operator=not output=out_overlay_3_1 olayer=0,1,0" %
                                (final_out))

                            final_out = 'out_overlay_3_1'
                        except:
                            pass

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
                                "v.overlay --quiet ainput=OutFinale binput=userLayerPlus operator=or output=OutFinale2 olayer=1,0,0")
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
                            "v.overlay --quiet ainput=%s binput=userLayerPlus operator=or output=OutFinale3 olayer=1,0,0" %
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

                # v.clean - Toolset for cleaning topology of vector map - remove small area (< 200 m2)
                self.cmd("v.clean --quiet input=%s output=cleanmap tool=rmarea threshold=200" % (final_out))
                final_out = "cleanmap"

                # v.db.addcolumn - Adds one or more columns to the attribute
                # table connected to a given vector map.
                grass.run_command(
                    'v.db.addcolumn',
                    quiet=True,
                    map=final_out,
                    columns='surf_SPE_ha double precision')

                # v.to.db - Populates attribute values from vector features.
                self.cmd(
                    "v.to.db --quiet map=%s columns=surf_SPE_ha option=area unit=hectares" %
                    (final_out))

                # v.out.ogr - Exports a vector map layer to any of the
                # supported OGR vector formats.
                self.cmd(
                    "v.out.ogr --quiet --overwrite -s format=GeoJSON input=%s output=out.geojson" %
                    (final_out))

                # Rename all fields with removing the prefix ('a_')
                delete_feilds_suffix('out.geojson', 'a_')

                #########################################
                # Exporting
                #########################################
                if self.getInputValue('outputFormat') == "GeoJSON":
                    # Reproject userData from EPSG:2154 to outputSrs and export to GeoJSON format
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
                    # Reproject userData from EPSG:2154 to outputSrs and export to GML format
                    self.cmd(["ogr2ogr",
                              "-f",
                              "GML",
                              "-s_srs",
                              "EPSG:2154",
                              "-t_srs",
                              self.getInputValue('outputSrs'),
                              "ZPE.gml",
                              "out.geojson"])
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

                self.processTime.setValue(temps_sec)

            # if buffer overlay completely the parcelles layer (if final_out is
            # None)
            else:
                # Change the variable "outputData" from ComplexOutput to
                # LiteralOutput
                self.outputData = self.addLiteralOutput(
                    identifier="outputData", title="Message d'erreur", type='')

                # affecting output time
                delta = datetime.now() - stime
                temps_sec = 'Temps de traitement: {0} \n'.format(delta)

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

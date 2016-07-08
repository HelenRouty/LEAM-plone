"""Definition of the simmap content type
"""

from zope.interface import implements, directlyProvides
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

from AccessControl import ClassSecurityInfo

from Products.Archetypes import atapi
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata

from iw.fss.FileSystemStorage import FileSystemStorage

from leam.simmap import simmapMessageFactory as _
from leam.simmap.interfaces import ISimMap
from leam.simmap.interfaces import ISimMapSettings
from leam.simmap.config import PROJECTNAME

import os
import zipfile
import json

__widget__ = """
<div id="map" class="olMap" style="width:{width};height:{height};">
            <!-- openlayers map -->
</div>

<div id="map_parameters" style="display:none;">
  <div id="map_url">{url}</div>
  <div id="map_mapserver">{mapserver}</div>
  <div id="map_mappath">{mappath}</div>
  <div id="map_title">{title}</div>
  <div id="map_transparency">{transparency}</div>
  <div id="map_latlong">{latlong}</div>
  <div id="map_zoom">{zoom}</div>
</div>
"""

WMS_ENABLE = """
    WEB
        METADATA
            wms_enable_request "*"
        END
    END

"""

simmapSchema = schemata.ATContentTypeSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-
    atapi.FileField( 'simImage',
        storage=FileSystemStorage(),
        widget=atapi.FileWidget(
            label=_(u"GIS Layer"),
            description=_(u""),
        ),
        required=True,
        validators=('isNonEmptyFile'),
    ),


    atapi.FileField( 'mapFile',
        storage=FileSystemStorage(),
        widget=atapi.FileWidget(
            label=_(u"Mapserver Map File"),
            description=_(u""),
        ),
        #validators=('isNonEmptyFile'),
    ),


    atapi.TextField('details',
        storage=atapi.AnnotationStorage(),
        default_content_type='text/html',
        allowable_content_type='(text/html, text/plain)',
        default_output_type='text/x-html-safe',
        widget=atapi.RichWidget(
            label=_(u"Details"),
            description=_(u"Description of GIS Layer"),
        ),
    ),


    atapi.FloatField( 'transparency',
        storage=atapi.AnnotationStorage(),
        widget=atapi.DecimalWidget(
            label=_(u"Transparency"),
            description=_(u"0.0 = transparent, 1.0 = opaque"),
        ),
        default = 0.7,
        validators = ('isDecimal'),
    ),


    atapi.StringField('latlong',
        storage=atapi.AnnotationStorage(),
        widget=atapi.StringWidget(
            label=_(u"Latitude Longitude"),
            description=_(u'formatted as "lat long"'),
        ),
        required=False,
    ),

    atapi.IntegerField('zoom',
        storage=atapi.AnnotationStorage(),
        widget=atapi.IntegerWidget(
            label=_(u"Zoom Level"),
            description=_(u"0 = No Zoom, 19 = Full Zoom"),
        ),
        default = 10,
        validators = ('isInt'),
    ),

))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

simmapSchema['title'].storage = atapi.AnnotationStorage()
simmapSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(simmapSchema, moveDiscussion=False)


def removeLEAM(simmap, event):
    """Remove the LEAM specific version of the simmap files from the FSS
    managed directory. This is generally called after simmap edits to 
    rebuild the mapfile and leam.files directory.
    """
    p = os.path.split(simmap.getSimImage().path)[0]
    os.system('rm -rf %s/leam.*' % p)
    

class SimMap(base.ATCTContent):
    """SimMap version 2"""
    implements(ISimMap)

    meta_type = "SimMap"
    schema = simmapSchema
    security = ClassSecurityInfo()

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')
    
    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    simImage = atapi.ATFieldProperty('simImage')
    mapFile = atapi.ATFieldProperty('mapFile')
    details = atapi.ATFieldProperty('details')
    transparency = atapi.ATFieldProperty('transparency')
    latlong = atapi.ATFieldProperty('latlong')
    zoom = atapi.ATFieldProperty('zoom')


    def extract_layer(self, src):
        """Attmpts to unzip the <src> file and save files to disk.  If <src>
           is not a zip file no changes are made on the file system.
           extract_layer returns the name of the layer (filename only)
           appropriate for modifying the mapfile DATA parameter.
        """

        path, layer = os.path.split(src)
        myfiles = os.path.join(path, 'leam.files')

        try:
            if os.path.exists(myfiles):
                os.system('rm -rf %s' % myfiles)
            os.mkdir(myfiles)

            zip = zipfile.ZipFile(open(src, 'r'))
            for fname in zip.namelist():

                # skip any directories within the zipfile
                if fname.endswith('/'):
                    continue

                # save all normal files in lower case!
                ofile = os.path.join(myfiles, os.path.basename(fname).lower())
                f = open(ofile, 'wb')
                f.write(zip.read(fname))
                f.close()

                # save the outfile name if it's the primary file
                n, ext = os.path.splitext(ofile)
                if ext in ['.shp', '.tif', '.img']:
                    layer = os.path.join('leam.files', os.path.basename(ofile))

        # if it's not a zip file, we assume it's a valid GIS layer
        except zipfile.BadZipfile:
            pass

        return layer


    def create_files(self, layer, mapfile):
        """create_files is responsible for unpacking any compressed
           layer files (using extract_layer) and creating a custom mapfile
           that has the DATA field modified to point to the local files
           and enables WMS capabilities if necessary.  Modified mapfile
           will be named with 'leam.' filename prefix.

           @layer -- absolute path to the GIS layer being imported.
           @mapfile -- absoluate path to the mapfile.
        """
        layer = self.extract_layer(layer)

        path, mapname = os.path.split(mapfile)
        mymap = os.path.join(path, 'leam.'+mapname)

        mapout = open(mymap, 'w')
        s = open(mapfile, 'r').read()
        wms = s.find('wms_enable_request')
        for l in s.splitlines():

            # replace the DATA field
            indent = l.find('DATA')
            if indent > -1 and l.find('METADATA') == -1:
                mapout.write('%sDATA "%s"\n' % (' '*indent, layer))
                continue

            # enable WMS just before the LAYER field if necessary
            indent = l.find('LAYER')
            if indent > -1 and wms == -1:
                mapout.write(WMS_ENABLE)
                mapout.write(l+'\n')
                continue

            # write the original line in all other cases
            mapout.write(l+'\n')

        mapout.close()


    def calc_latlong(self, mapPath):
        # Seeks through a map file and finds the EXTENT field
        # Once found, it calculates a center lat and long and returns it
        # Relevant line is in form: lat long
        mapfile = open(mapPath, 'r')
        for l in mapfile:
            if l.find('EXTENT') != -1:
                 coordArray = l.split('EXTENT ')
                 coordArray = coordArray[1].split(' ')
                 long = (float(coordArray[0]) + float(coordArray[2]))/2
                 lat = (float(coordArray[1]) + float(coordArray[3]))/2
                 break
            else:
                continue
        return '%s %s'%(lat,long)


    def get_mappath(self):
        """return the full path of the map file"""

        path, mapfile = os.path.split(self.getMapFile().path)
        mappath = os.path.join(path, 'leam.'+mapfile)

        # If this is the first run, create the needed files
        if not os.path.exists(mappath):
            self.create_files(self.getSimImage().path, self.getMapFile().path)
        if not self.getLatlong():
            self.setLatlong(self.calc_latlong(mappath))

        return mappath


    def getWidget(self, width, height):
        """return simmap as widget for use in other pages"""
        #import pdb; pdb.set_trace()

        settings = getUtility(IRegistry).forInterface(ISimMapSettings)

        return __widget__.format(width=width, height=height,
                             url=self.absolute_url(),
                             mapserver=settings.mapserver,
                             mappath=self.get_mappath(),
                             title=self.title_or_id(),
                             transparency=self.transparency,
                             latlong=self.latlong,
                             zoom=self.zoom)


    security.declarePublic("getMapMeta")
    def getMapMeta(self):
        """returns the SimMap meta data"""
        #import pdb; pdb.set_trace()

        settings = getUtility(IRegistry).forInterface(ISimMapSettings)

        meta = dict(
                    title = self.Title(),
                    mappath = self.get_mappath(),
                    mapserve = settings.mapserver,
                    transparency = self.transparency,
                    latlong = self.latlong,
                    zoom = self.zoom
                    )
                  
        self.REQUEST.RESPONSE.setHeader("content-type", "application/json")
        return json.dumps(meta)


    # Dynamically finds mapfile
    # Makes calculations and allocations if it is the first time viewing
    #security.declareProtected(permissions.View, "getMapPath")
    security.declarePublic("getMapPath")
    def getMapPath(self):
        """returns the file system path to the Simmap mapFile"""
        return self.get_mappath()

    # changed from get_mapserve to get_mapserver with an R for consistency
    security.declarePublic("get_mapserver")
    def get_mapserver(self, REQUEST, RESPONSE):
        """redirects to the mapserver to aid in debugging"""
        settings = getUtility(IRegistry).forInterface(ISimMapSettings)
        mymap = self.getMapPath()

        RESPONSE.redirect("%s?mode=map&map=%s" % (settings.mapserver, mymap))
        

    #security.declareProtected(permissions.View, "get_layer")
    security.declarePublic("get_layer")
    def get_layer(self, REQUEST, RESPONSE):
        """Download the GIS Layer"""
        RESPONSE.redirect(self.absolute_url()+'/at_download/simImage')
        return

    #security.declareProtected(permissions.View, "get_mapfile")
    security.declarePublic("get_mapfile")
    def get_mapfile(self, REQUEST, RESPONSE):
        """Download the mapfile """
        RESPONSE.redirect(self.absolute_url()+'/at_download/mapFile')
        return

atapi.registerType(SimMap, PROJECTNAME)

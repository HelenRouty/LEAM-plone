"""Definition of the Probmap content type
"""
from xml.etree.ElementTree import Element, SubElement
from xml.etree.ElementTree import tostring, fromstring

from zope.interface import implements

from AccessControl import ClassSecurityInfo

from Products.Archetypes import atapi
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata

from plone.app.blob.field import FileField
from archetypes.referencebrowserwidget import ReferenceBrowserWidget

# -*- Message Factory Imported Here -*-
from leam.luc import lucMessageFactory as _

from leam.luc.interfaces import IProbmap
from leam.luc.config import PROJECTNAME

ProbmapSchema = schemata.ATContentTypeSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-

    atapi.IntegerField(
        'year',
        storage=atapi.AnnotationStorage(),
        widget=atapi.IntegerWidget(
            label=_(u"Effective Year"),
            description=_(u"Each driver given below should correspond to this year."),
        ),
        required=True,
        default=_(u"2010"),
        validators=('isInt'),
    ),


    atapi.ReferenceField(
        'tdm',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            allow_browse=1,
            allow_search=1,
            startup_directory='/luc/drivers/transportation',
            label=_(u"TDM Transportation Network"),
            #description=_(u""),
        ),
        required=True,
        relationship='probmap_tdm',
        allowed_types=('SimMap'),
        multiValued=False,
    ),


    atapi.ReferenceField(
        'roads',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            visible={'view': 'hidden', 'edit': 'hidden'},
            allow_browse=1,
            allow_search=1,
            startup_directory='/luc/drivers/transportation',
            label=_(u"Additional Roads"),
            #description=_(u"Select a single GIS layer."),
        ),
        required=False,
        relationship='probmap_roads',
        allowed_types=('SimMap'),
        multiValued=False,
    ),


#    atapi.ReferenceField(
#        'transit',
#        storage=atapi.AnnotationStorage(),
#        widget=ReferenceBrowserWidget(
#            visible={'view': 'hidden', 'edit': 'hidden'},
#            allow_browse=1,
#            allow_search=1,
#            startup_directory='/luc/drivers/transportation',
#            label=_(u"Transit Networks"),
#            #description=_(u"Select one or more GIS layers"),
#        ),
#        required=False,
#        relationship='probmap_transit',
#        allowed_types=('SimMap'),
#        multiValued=True,
#    ),
#

    atapi.ReferenceField(
        'drivers',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            allow_browse=1,
            allow_search=1,
            startup_directory='/luc/drivers/specials',
            label=_(u"Special Drivers"),
            #description=_(u"Select one or more GIS layers."),
        ),
        required=False,
        relationship='probmap_driver',
        allowed_types=('SimMap'),
        multiValued=True,
    ),


    atapi.ReferenceField(
        'nogrowth',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            allow_browse=1,
            allow_search=1,
            startup_directory='/luc/drivers/nogrowth',
            label=_(u"No Growth Maps"),
            #description=_(u"Select one or more GIS layers."),
        ),
        required=False,
        relationship='probmap_nogrowth',
        allowed_types=('SimMap'),
        multiValued=True,
    ),


    atapi.ReferenceField(
        'popcenters',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            label=_(u"City and Population Centers"),
            #description=_(u"Select one or more GIS layer."),
            startup_directory='/luc/drivers/attractors',
        ),
        required=True,
        relationship='probmap_popcenters',
        allowed_types=('SimMap'),
        multiValued=True,
    ),


    atapi.ReferenceField(
        'empcenters',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            label=_(u"Employment Centers"),
            #description=_(u"Select one or more GIS layer."),
            startup_directory='/luc/drivers/attractors',
        ),
        required=True,
        relationship='probmap_empcenters',
        allowed_types=('SimMap'),
        multiValued=True,
    ),


    atapi.ReferenceField(
        'landuse',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            label=_(u"Initial Land Use Map"),
            #description=_(u"Select a single GIS layer."),
            startup_directory='/luc/drivers/grids',
        ),
        required=True,
        relationship='probmap_landuse',
        allowed_types=('SimMap'),
        multiValued=False,
    ),


    atapi.ReferenceField(
        'dem',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            visible={'view': 'hidden', 'edit': 'hidden'},
            label=_(u"Digital Elevation Map"),
            #description=_(u"Select a sigle GIS layer."),
            startup_directory='/luc/drivers/grids',
        ),
        required=False,
        relationship='probmap_dem',
        allowed_types=('SimMap'),
        multiValued=False,
    ),


    atapi.ReferenceField(
        'probview',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            visible={'view': 'hidden', 'edit': 'hidden'},
            label=_(u"Probmap View"),
            #description=_(u"A SimMap view visualzing the Probmap."),
            startup_directory='/luc/drivers',
        ),
        required=False,
        relationship='probmap_probview',
        allowed_types=('SimMap'),
        multiValued=False,
    ),


    FileField(
        'probfile',
        storage=atapi.AnnotationStorage(),
        widget=atapi.FileWidget(
            visible={'view': 'hidden', 'edit': 'visible'},
            label=_(u"Probmap File"),
            #description=_(u"Precomputed version of the probability map."),
        ),
        required=False,
    ),

))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

ProbmapSchema['title'].storage = atapi.AnnotationStorage()
ProbmapSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(ProbmapSchema, moveDiscussion=False)


class Probmap(base.ATCTContent):
    """a Land Use Change probability map"""
    implements(IProbmap)

    meta_type = "Probmap"
    schema = ProbmapSchema
    security = ClassSecurityInfo()

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    year = atapi.ATFieldProperty('year')

    roads = atapi.ATReferenceFieldProperty('roads')

    #transit = atapi.ATReferenceFieldProperty('transit')

    tdm = atapi.ATReferenceFieldProperty('tdm')

    drivers = atapi.ATReferenceFieldProperty('drivers')

    nogrowth = atapi.ATReferenceFieldProperty('nogrowth')

    empcenters = atapi.ATReferenceFieldProperty('empcenters')

    popcenters = atapi.ATReferenceFieldProperty('popcenters')

    dem = atapi.ATReferenceFieldProperty('dem')

    landuse = atapi.ATReferenceFieldProperty('landuse')

    probview = atapi.ATReferenceFieldProperty('probview')

    probfile = atapi.ATFieldProperty('probfile')

    def _simmap(self, obj):
        """returns URL of the simImage download"""
        return obj.absolute_url() + '/at_download/simImage'

    security.declarePublic('getConfig')
    def getConfig(self):
        """Generate a configuration file for the Probmap"""
        #import pdb; pdb.set_trace()

        tree = Element('probmap')

        SubElement(tree, 'id').text = self.id
        SubElement(tree, 'title').text = self.title
        SubElement(tree, 'year').text = str(self.year)
        SubElement(tree, 'url').text = self.absolute_url()
        SubElement(tree, 'download').text = self.absolute_url() + \
            '/at_download/probfile'

        e = SubElement(tree, 'tdm')
        if self.tdm:
            e.text = self._simmap(self.tdm)

        e = SubElement(tree, 'roads')
        if self.roads:
            e.text = self._simmap(self.roads)

        e = SubElement(tree, 'drivers')
        for s in self.drivers:
            SubElement(e, 'driver').text = self._simmap(s)
        
        e = SubElement(tree, 'nogrowth_maps')
        for s in self.nogrowth:
            SubElement(e, 'nogrowth').text = self._simmap(s)
        
        e = SubElement(tree, 'empcenters')
        for s in self.empcenters:
            SubElement(e, 'empcenter').text = self._simmap(s)
        
        e = SubElement(tree, 'popcenters')
        for s in self.popcenters:
            SubElement(e, 'popcenter').text = self._simmap(s)

        e = SubElement(tree, 'landuse')
        if self.landuse:
            e.text = self._simmap(self.landuse)

        e = SubElement(tree, 'dem')
        if self.dem:
            e.text = self._simmap(self.dem)

        self.REQUEST.RESPONSE.setHeader('Content-Type',
            'application/xml;;charset=UTF-8')
        self.REQUEST.RESPONSE.setHeader('Content-Disposition',
            'attachment; filename="%s_probmap.xml"' % self.title)

        return tostring(tree, encoding='UTF-8')


atapi.registerType(Probmap, PROJECTNAME)

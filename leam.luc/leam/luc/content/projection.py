"""Definition of the Projection content type
"""
import json
from StringIO import StringIO

from xml.etree.ElementTree import Element, SubElement
from xml.etree.ElementTree import fromstring, tostring

from zope.interface import implements

from AccessControl import ClassSecurityInfo

from Products.Archetypes import atapi
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata

from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from Products.DataGridField import DataGridField
from Products.DataGridField import DataGridWidget
from Products.DataGridField.Column import Column

# -*- Message Factory Imported Here -*-
from leam.luc import lucMessageFactory as _

from leam.luc.interfaces import IProjection
from leam.luc.config import PROJECTNAME

ProjectionSchema = schemata.ATContentTypeSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-

    DataGridField( 'projection',
        searchable = False,
        storage=atapi.AnnotationStorage(),
        columns = ('year', 'pop', 'emp'),
        allow_reorder = False,
        default = [ { 'year': '2010', 'pop': '0', 'emp': '0'},
                    { 'year': '2040', 'pop': '0', 'emp': '0'},
                  ],
        widget=DataGridWidget(
            label=_(u"Projection"),
            description=_(u"Enter as many population and employment values as needed.  Intermediate values will be calculated automatically."),
            columns = {
                'year': Column(_(u"Year"), default='2010'),
                'pop': Column(_(u"Population"), default='0'),
                'emp': Column(_(u"Employment"), default='0'),
                }
        ),
        required=True,
    ),

    atapi.ReferenceField( 'zone',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            label=_(u"Effective Zone"),
            description=_(u"Select a subregional map defining the effective modeling zone."),
            startup_directory='/luc/projections/subregional'
        ),
        relationship='projection_zone',
        allowed_types = ('SimMap',),
        multiValued=False,
        required=True,
    ),

    atapi.ReferenceField( 'pop_density',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            label=_(u"Population Density"),
            description=_(u"A GIS layer defining the new population density."),
            startup_directory='/luc/projections/density',
        ),
        relationship='projection_pop_density',
        allowed_types = ('SimMap',),
        multiValued=False,
        required=False,
    ),

    atapi.ReferenceField( 'emp_density',
        storage=atapi.AnnotationStorage(),
        widget=ReferenceBrowserWidget(
            label=_(u"Employment Density"),
            description=_(u"A GIS layer defining the new employment density."),
            startup_directory='/luc/projections/density',
        ),
        relationship='projection_emp_density',
        allowed_types = ('SimMap',),
        multiValued=False,
        required=False,
    ),

    atapi.BooleanField( 'redevelopment',
        storage=atapi.AnnotationStorage(),
        widget=atapi.BooleanWidget(
            label=_(u"Redevelopment"),
            description=_(u"Check box to allow redevelopment."),
        ),
        default=False,
    ),
))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

ProjectionSchema['title'].storage = atapi.AnnotationStorage()
ProjectionSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(ProjectionSchema, moveDiscussion=False)


class Projection(base.ATCTContent):
    """A population and employment projection used within the LEAM model"""
    implements(IProjection)

    meta_type = "Projection"
    schema = ProjectionSchema
    security = ClassSecurityInfo()

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    projection = atapi.ATFieldProperty('projection')

    zone = atapi.ATReferenceFieldProperty('zone')

    pop_density = atapi.ATReferenceFieldProperty('pop_density')

    emp_density = atapi.ATReferenceFieldProperty('emp_density')

    redevelopment = atapi.ATFieldProperty('redevelopment')


    security.declarePublic('config')
    def config(self):
        """return projection configuration"""

        url = self.absolute_url()
        p = self.getProjection()

        year = [rec['year'] for rec in p]
        pop = [rec['pop'] for rec in p]
        emp = [rec['emp'] for rec in p]

        r = {
            '@context': 'http://leamgroup.com/contexts/projections.jsonld',
            '@id': url,
            'title': self.title,
            'shortname': self.id,
            'startyear': p[0]['year'],
            'endyear': p[-1]['year'],
            'value': {
                'years': year,
                'population': pop,
                'employment': emp,
                },
            'zone': {
                '@id': self.zone.absolute_url(),
                '@type': 'simmap',
                'layer': self.zone.absolute_url() + '/at_download/simImage',
                'mapfile': self.zone.absolute_url() + '/at_download/mapFile',
                },

            # deprecated
            'graph': url + '/getGraph',
            }

        if self.pop_density:
            url = self.pop_density.absolute_url()
            r['pop_density'] = {
                '@id': url,
                '@type': 'simmap',
                'layer': url + '/at_download/simImage',
                'mapfile': url + '/at_download/mapFile',
                }
    
        if self.emp_density:
            url = self.emp_density.absolute_url()
            r['pop_density'] = {
                '@id': url,
                '@type': 'simmap',
                'layer': url + '/at_download/simImage',
                'mapfile': url + '/at_download/mapFile',
                }

        self.REQUEST.RESPONSE.setHeader('Content-type','application/json')
        return json.dumps(r)


    security.declarePublic('getConfig')
    def getConfig(self):
        """Generates a configuration file for this projection"""

        tree = Element('projection')

        SubElement(tree, 'id').text = self.id
        SubElement(tree, 'title').text = self.title
        SubElement(tree, 'startyear').text = self.getProjection()[0]['year']
        SubElement(tree, 'endyear').text = self.getProjection()[-1]['year']
        SubElement(tree, 'graph').text = self.absolute_url() + '/getGraph'
        SubElement(tree, 'layer').text = self.zone.absolute_url() + \
            '/at_download/simImage'
        SubElement(tree, 'redevelopment').text = str(self.redevelopment)

        e = SubElement(tree, 'pop_density')
        if self.pop_density:
            e.text = self.pop_density.absolute_url() + '/at_download/simImage'

        e = SubElement(tree, 'emp_density')
        if self.emp_density:
            e.text = self.emp_density.absolute_url() + '/at_download/simImage'

        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        self.REQUEST.RESPONSE.setHeader('Content-Disposition',
            'attachment; filename="%s_demand.xml"' % self.title)
        return tostring(tree, encoding='UTF-8')


    security.declarePublic('getGraph')
    def getGraph(self):
        """Generates a the projection in the LEAM land use models
        required format.
        """
        proj = StringIO()
        proj.write('# population and employment graph\n')
        proj.write('# title: %s\n' % self.title)
        proj.write('# url: %s\n' % self.absolute_url())
        proj.write('# spatial area: %s\n' % self.getZone().absolute_url())
        if self.pop_density:
            proj.write('# population density: %s\n' % \
                self.pop_density.absolute_url())
        if self.emp_density:
            proj.write('# employment density: %s\n\n' % \
                self.emp_density.absolute_url())

        proj.write('Population\n')
        for p in self.getProjection():
            proj.write('%s, %s\n' % (p['year'], p['pop'].replace(',','')))

        proj.write('\nEmployment\n')
        for p in self.getProjection():
            proj.write('%s, %s\n' % (p['year'], p['emp'].replace(',','')))

        # need to specify the encoding
        #self.REQUEST.RESPONSE.setHeader('Content-Type', 
        #    'text/plain;;charset=UTF-8')
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        self.REQUEST.RESPONSE.setHeader('Content-Disposition',
            'attachment; filename="%s_demand.txt"' % self.title)
        #return unicode(proj.getvalue())
        return proj.getvalue()


    security.declarePublic('getDecline')
    def getDecline(self):
        """Generates a the projection in the LEAM land use models
        required format normalized for decline.
        """
        proj = StringIO()
        proj.write('# population and employment graph\n')
        proj.write('# title: %s\n' % self.title)
        proj.write('# url: %s\n' % self.absolute_url())
        proj.write('# spatial area: %s\n' % self.getZone().absolute_url())
        if self.pop_density:
            proj.write('# population density: %s\n' % \
                self.pop_density.absolute_url())
        if self.emp_density:
            proj.write('# employment density: %s\n\n' % \
                self.emp_density.absolute_url())

        p = self.getProjection()[0]
        startpop=int(p['pop'].replace(',',''))
        startemp=int(p['emp'].replace(',',''))

        proj.write('Population\n')
        for p in self.getProjection():
            pop = int(p['pop'].replace(',','')) - startpop
            if pop < 0:
                pop = -1 * pop
            else:
                pop = 0
            proj.write('%s, %d\n' % (p['year'], pop))

        proj.write('\nEmployment\n')
        for p in self.getProjection():
            emp = int(p['emp'].replace(',','')) - startemp
            if emp < 0:
                emp = -1 * emp
            else:
                emp = 0
            proj.write('%s, %s\n' % (p['year'], emp))

        # need to specify the encoding
        #self.REQUEST.RESPONSE.setHeader('Content-Type', 
        #    'text/plain;;charset=UTF-8')
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        self.REQUEST.RESPONSE.setHeader('Content-Disposition',
            'attachment; filename="%s_demand.txt"' % self.title)
        #return unicode(proj.getvalue())
        return proj.getvalue()

    security.declarePublic('csv')
    def csv(self):
        """return the projection in 3-column CSV format"""
        proj = StringIO()
        proj.write('# population and employment projection\n')
        proj.write('# title: %s\n' % self.title)
        proj.write('# url: %s/csv\n' % self.absolute_url())

        for p in self.getProjection():
            proj.write(', '.join((p['year'], p['pop'].replace(',',''), 
                                  p['emp'].replace(',',''))))

        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/csv')
        self.REQUEST.RESPONSE.setHeader('Content-Disposition',
            'attachment; filename="%s.csv"' % self.title)
        return proj.getvalue()


atapi.registerType(Projection, PROJECTNAME)

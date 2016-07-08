import json
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring
from logging import getLogger

try:
    from five.grok import CodeView as View
except ImportError:
    from five.grok import View

from five import grok
from z3c.form import group, field
from zope import schema
from zope.interface import Interface, invariant, Invalid
from zope.component import getUtility
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.schema.interfaces import IContextSourceBinder

from Acquisition import aq_inner, aq_parent

from plone.dexterity.content import Item
from plone.directives.dexterity import DisplayForm
from plone.registry.interfaces import IRegistry
from plone.namedfile.interfaces import IImageScaleTraversable
from plone.supermodel import model
from plone.autoform import directives as form

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder


from leam.taz import MessageFactory as _

from leam.taz.settings import ISettings
from leam.simmap.interfaces import ISimMap
from leam.luc.interfaces import ILUCScenario, IModel


# Interface class; used to define content-type schema.

class ITAZAnalysis(model.Schema, IImageScaleTraversable):
    """
    TAZ Analysis of a LEAM Scenario
    """

    layer = RelationChoice(
        title = _(u"GIS layer"),
        source = ObjPathSourceBinder(object_provides=ISimMap.__identifier__),
        )

    baseyear = schema.TextLine(
        title = _(u"Year"),
        default = u"2010",
        )

    years = schema.TextLine(
        title = _(u"Target Years"),
        description = _(u"comma seperated list of target years"),
        default = _(u"2020,2025,2030,2035,2040"),
        )

    scenario = RelationChoice(
        title = _(u"LEAM Scenario"),
        description = _(u"Select specific scenarios for a onetime run"),
        source = ObjPathSourceBinder(object_provides= \
                                     ILUCScenario.__identifier__),
        required = False,
        )

    #form.omitted('runstatus')
    runstatus = schema.TextLine(
        title = _(u"Job Status"),
        default = u"pending",
        )

# Set the default value based on registry 
# take from the following: http://stackoverflow.com/questions/6662467/how-do-you-override-the-default-value-of-a-field-in-a-dexterity-behavior-in-plon
#
#@default_value(field=ITAZAnalysis['years'])
#def yearsDefaultValue(data):
#    data.context._years


# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.

class TAZAnalysis(Item):
    grok.implements(ITAZAnalysis, IModel)

    def __init__(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISettings)
        self._cmdline = settings.cmdline
        self._years = settings.years

    def getCmdline(self, context):
        return self._cmdline.format(
            config = context.absolute_url() + '/getConfig'
            )


@grok.subscribe(ITAZAnalysis, IObjectAddedEvent)
def scenarioSpecified(obj, event):
    #import pdb; pdb.set_trace()

    if obj.scenario:
        obj.runstatus = "queued"


class DefaultView(DisplayForm):
    """ default view class """

    grok.context(ITAZAnalysis)
    grok.require('zope2.View')

    grok.name('view')

    # Add view methods here


class ModelConfig(View):
    """ configuration information as JSON """

    grok.context(ITAZAnalysis)
    grok.name('getConfig')

    def render(self):
        #import pdb; pdb.set_trace()
 
        context = aq_inner(self.context)
 
        r = context.luc.resources.items()
        d = dict(
            id = context.id,
            title = context.title,
            layer_url = context.layer.to_object.absolute_url() + \
                    '/at_download/simImage',
            base_year = context.baseyear,
            luc_url = context.scenario.to_object.absolute_url(),
            grass = context.luc.resources.grass.absolute_url() + \
                    '/at_download/file',
            years = context.years,
            cmdline = context.getCmdline(context),
            )

        self.response.setHeader('Content-Type', 'application/json')
        return json.dumps(d)

class requeue(View):
    """ requeue job if necessary """

    grok.context(ITAZAnalysis)
    grok.name('requeue')

    def render(self):
        context = aq_inner(self.context)
        context.runstatus = 'queued'
        context.reindexObject(['runstatus',])

        self.response.setHeader("Content-Type", "text/plain")
        return "requeued."


from zope.interface import implements, Interface
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from leam.simmap import simmapMessageFactory as _
from leam.simmap.interfaces import ISimMap, ISimMapSettings


class ISimMapView(Interface):
    """SimMap view interace"""


class SimMapView(BrowserView):
    """SimMap browser view"""
    implements(ISimMapView)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(ISimMapSettings)

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def maps(self):
        """ returns a list of simmaps from the container """
        #import pdb; pdb.set_trace()

        # get all SimMaps in the current folder and create a list
        # of URLs NOT INCLUDING the current SimMap
        # Note: determine if simmap is default view of folder?
        # Note: switch to inferface search rather than portal_type?
        # Note: include references?
        fpath = '/'.join(self.context.getParentNode().getPhysicalPath())
        sibs = self.portal_catalog(path={'query':fpath,'depth':1}, 
                portal_type='SimMap', sort_on='getObjPositionInParent')
        urls = [b.getURL() for b in sibs \
                if b.getURL() != self.context.absolute_url()]

        # add references to map list if they are not already in URL list
        refs = self.context.getRefs()
        urls.extend([o.absolute_url() for o in refs \
                if o.Type() == 'SimMap' and o.absolute_url() not in urls])

        # add references to map list if they are not already in URL list
        refs = self.context.getBRefs()
        urls.extend([o.absolute_url() for o in refs \
                if o.Type() == 'SimMap' and o.absolute_url() not in urls])

        # start with the current SimMap URL
        urls.insert(0, self.context.absolute_url())

        return urls


    def mapserver(self):
        return self.settings.mapserver


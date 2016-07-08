from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from leam.luc import lucMessageFactory as _
from leam.luc.interfaces import IModel

import json


class IPopQueue(Interface):
    """
    project view interface
    """
    pass


class PopQueue(BrowserView):
    """
    project browser view
    """
    implements(IPopQueue)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def __call__(self):
        
        #import pdb; pdb.set_trace()

        filter = { 'object_provides' : IModel.__identifier__,
                   'runstatus' : 'queued'
                 }
        results = self.portal_catalog(filter, sort_on='modified')
        if results:
            obj = results[0].getObject()
            url = obj.absolute_url()
            rsp = dict(
                status = 'OK',
                id = obj.id,
                title = obj.title,
                url = url,
                repository = obj.repository(),
                cmdline = obj.cmdline(),
                on_success = url + '/success',
                on_error = url + '/error',
                )
                #cmdline = getattr(obj, 'cmdline', ''),


            # mark the object as running
            obj.runstatus = 'running'
            obj.reindexObject(['runstatus',])

        # nothing to do
        else:
            rsp = dict( status = 'EMPTY' )

        self.request.RESPONSE.setHeader('Content-Type', 'application/json')
        return json.dumps(rsp)


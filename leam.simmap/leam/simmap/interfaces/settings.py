from zope import schema
from zope.interface import Interface

from leam.simmap import simmapMessageFactory as _


class ISimMapSettings(Interface):
    """Global SimMap settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    mapserver = schema.TextLine(
        title=_(u"Mapserver"),
        description=_(u"The URL of the mapserver"),
        required=True,
        default=u'http://localhost.leamgroup.com/cgi-bin/mapserv',
        )

    baselayer = schema.TextLine(
        title=_(u"OpenLayers Baselayer"),
        description=_(u"A javascript string defining blayer."),
        required=False,
        default=u'',
        )


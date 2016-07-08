from zope import schema
from zope.interface import Interface

from leam.simmap import simmapMessageFactory as _

class ISimMap(Interface):
    """SimMap version 2"""
    
    # -*- schema definition goes here -*-
    simImage = schema.Bytes(
        title=_(u"GIS Layer"), 
        required=True,
        description=_(u"GIS layer or zipfile containing GIS layer"),
    )

    mapFile = schema.Bytes(
        title=_(u"Map File"), 
        required=False,
        description=_(u"Mapserver Map File"),
    )

    details = schema.Text(
        title=_(u"Details"), 
        required=False,
        description=_(u"A detailed description of the SimMap"),
    )


    transparency = schema.Float(
        title=_(u"Transparency"), 
        required=False,
        description=_(u"Transparency of the overlay (1.0 = opaque)"),
    )

    latlong = schema.TextLine(
        title=_(u"Latitude Longitude"), 
        required=False,
        description=_(u"lat/long in decimal degrees"),
    )

    zoom = schema.Int(
        title=_(u"Zoom level"), 
        required=False,
        description=_(u"Zoom level (1-20)"),
    )


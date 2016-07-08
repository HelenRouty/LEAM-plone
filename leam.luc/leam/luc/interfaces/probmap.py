from zope.interface import Interface
# -*- Additional Imports Here -*-
from zope import schema

from leam.luc import lucMessageFactory as _



class IProbmap(Interface):
    """a Land Use Change probability map"""

    # -*- schema definition goes here -*-
    probview = schema.Object(
        title=_(u"Simmap view of the probmap."),
        required=False,
        description=_(u"A SimMap view visualzing the Probmap."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    probfile = schema.Bytes(
        title=_(u"Probmap File"),
        required=False,
        description=_(u"Precomputed version of the probability map."),
    )
#
    year = schema.Int(
        title=_(u"Effective Year"),
        required=True,
        description=_(u"First year the probmap will be used."),
    )
#
    roads = schema.Object(
        title=_(u"Additional Roads"),
        required=False,
        description=_(u"Select a GIS layer that contains any roads not included in the TDM network."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
#    transit = schema.Object(
#        title=_(u"Transit Networks"),
#        required=False,
#        description=_(u"Select one or more GIS layers containing regional or local transit networks."),
#        schema=Interface, # specify the interface(s) of the addable types here
#    )
#
    tdm = schema.Object(
        title=_(u"Travel Demand Model Transportation Network"),
        required=True,
        description=_(u"Select a transportation network that has been generated from a travel demand model."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    nogrowth = schema.Object(
        title=_(u"No Growth Maps"),
        required=False,
        description=_(u"Select one or more GIS layers.  These areas will be protected from model development."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    empcenters = schema.Object(
        title=_(u"Employment Centers"),
        required=True,
        description=_(u"Select a GIS layer containing employeers and employmment centers."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    popcenters = schema.Object(
        title=_(u"City and Population Centers"),
        required=True,
        description=_(u"Select the GIS layer with city centers."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    dem = schema.Object(
        title=_(u"Digital Elevation Map"),
        required=True,
        description=_(u"Select a GIS layer that provides regional elevation."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    landuse = schema.Object(
        title=_(u"Initial Land Use Map"),
        required=True,
        description=_(u"Provide an initial land use map for the scenario.  Unused if a Starting Scenario is provided."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#

from zope.interface import Interface
# -*- Additional Imports Here -*-
from zope import schema

from leam.luc import lucMessageFactory as _


class IProjection(Interface):
    """A population and employment projection used within the LEAM model"""

    # -*- schema definition goes here -*-
    projection = schema.Float(
        title=_(u"Projection"),
        required=True,
        description=_(u"Enter as many population and employment as necssary.  Intermediate values will be calculated automatically."),
    )

    zone = schema.Object(
        title=_(u"Effected Zone"),
        required=True,
        description=_(u"A GIS layer defining the region of the projection."),
        schema=Interface, # specify the interface(s) of the addable types here
    )

    pop_density = schema.Object(
        title=_(u"Population Density"),
        required=False,
        description=_(u"A GIS layer defining the new population density."),
        schema=Interface, # specify the interface(s) of the addable types here
    )

    emp_density = schema.Object(
        title=_(u"Employment Density"),
        required=False,
        description=_(u"A GIS layer defining the new employment density."),
        schema=Interface, # specify the interface(s) of the addable types here
    )

    redevelopment = schema.Bool(
        title=_(u"Redevelopment"),
        description=_(u"Select to allow redevelopment."),
    )


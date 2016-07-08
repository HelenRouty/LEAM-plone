from zope.interface import Interface
# -*- Additional Imports Here -*-
from zope import schema

from leam.luc import lucMessageFactory as _


class ILUCScenario(Interface):
    """LEAM Land Use Change (LUC) Scenario"""
#
    end_time = schema.Date(
        title=_(u"End Time"),
        required=False,
        description=_(u"When the model completed."),
    )
#
    start_time = schema.Date(
        title=_(u"Start Time"),
        required=False,
        description=_(u"When the model began execution."),
    )
#
    runstatus = schema.TextLine(
        title=_(u"Run Status"),
        required=True,
        description=_(u"Provide the current run state of the scenario."),
    )
#
    growth = schema.Object(
        title=_(u"Growth Projections"),
        required=False,
        description=_(u"Add one or more growth Projections for this scenario."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    growthmap = schema.Object(
        title=_(u"Growth Drivers"),
        required=False,
        description=_(u"Add one or more driver sets."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    decline = schema.Object(
        title=_(u"Decline Projections"),
        required=False,
        description=_(u"Identify the study area and population and employment projections."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#
    declinemap = schema.Object(
        title=_(u"Decline Drivers"),
        required=False,
        description=_(u"Add one or more driver sets."),
        schema=Interface, # specify the interface(s) of the addable types here
    )
#

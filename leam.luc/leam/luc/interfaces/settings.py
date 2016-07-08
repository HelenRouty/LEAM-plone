from zope import schema
from zope.interface import Interface

from leam.luc import lucMessageFactory as _


class ILUCSettings(Interface):
    """Setup site configuration for the LUC model"""

    # -*- schema definition goes here -*-
    scenario_repo = schema.TextLine(
        title=_(u"Scenario Repository"),
        required=False,
        description=_(u"Enter the subversion repository for the LUC model"),
    )

    scenario_cmd = schema.TextLine(
        title=_(u"Scenario Startup Command"),
        required=False,
        description=_(u"Enter starting command line string"),
        default=u"python startup.py -c config.xml",
    )

    probmap_repo = schema.TextLine(
        title=_(u"Driver Set Repository"),
        required=False,
        description=_(u"Enter the subversion repository for the drivers"),
    )

    probmap_cmd = schema.TextLine(
        title=_(u"Probmap Startup Command"),
        required=False,
        description=_(u"Enter starting command line string"),
        default=u"python startup.py -c config.xml",
    )


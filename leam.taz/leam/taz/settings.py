from zope.interface import Interface
from zope import schema
from five import grok
from Products.CMFCore.interfaces import ISiteRoot

from plone.z3cform import layout
from plone.directives import form
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

class ISettings(form.Schema):
    """ Define settings data structure """

    years = schema.TextLine(
        title=u"Target Years",
        description=u"Command line for project specific TAZ analysis",
        default = u"2015,2020,2025,2030,2035,2040",
        )
    cmdline = schema.TextLine(
        title=u"Command Line",
        description=u"Command line for project specific TAZ analysis",
        default = u"/usr/local/ewg/taz.py {config}",
        )

class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    schema = ISettings
    label = u"LEAM TAZ Settings"

class SettingsView(grok.View):
    """
    View which wrap the settings form using ControlPanelFormWrapper to a HTML boilerplate frame.
    """
    grok.name("leam-taz-settings")
    grok.context(ISiteRoot)

    def render(self):
        view_factor = layout.wrap_form(SettingsEditForm,
                ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()

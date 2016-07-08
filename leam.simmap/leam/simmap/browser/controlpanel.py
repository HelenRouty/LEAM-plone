from plone.app.registry.browser import controlpanel

from leam.simmap import simmapMessageFactory as _
from leam.simmap.interfaces import ISimMapSettings


class SimMapSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ISimMapSettings
    label = _(u"SimMap settings")
    description = _(u"""Configure the SimMap""")

    def updateFields(self):
        super(SimMapSettingsEditForm, self).updateFields()


    def updateWidgets(self):
        super(SimMapSettingsEditForm, self).updateWidgets()

class SimMapSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SimMapSettingsEditForm

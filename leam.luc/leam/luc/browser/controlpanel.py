from plone.app.registry.browser import controlpanel

from leam.luc import lucMessageFactory as _
from leam.luc.interfaces import ILUCSettings


class LUCSettingsEditForm(controlpanel.RegistryEditForm):

    schema = ILUCSettings
    label = _(u"LUC Settings")
    description = _(u"""Configure the LEAM LUC scenario""")

    def updateFields(self):
        super(LUCSettingsEditForm, self).updateFields()


    def updateWidgets(self):
        super(LUCSettingsEditForm, self).updateWidgets()


class LUCSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = LUCSettingsEditForm

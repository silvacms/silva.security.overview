# package

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller
from zope.interface import Interface


silvaconf.extensionName("SilvaSecurityOverview")
silvaconf.extensionTitle("Silva Security Overview")


class SecurityOverviewInstaller(DefaultInstaller):
    """Installer for the Security overview extension. 
    Override install, uninstall to add more actions.
    """

    service_id = 'service_securityoverview'

    def install(self, root):
        factory = root.manage_addProduct['silva.security.overview']

        if self.service_id not in root.objectIds():
            factory.manage_addSecurityOverviewService(
                self.service_id, 'Silva Security Overview')

    def uninstall(self, root):
        if self.service_id in root.objectIds():
            root.manage_delObjects([self.service_id])

    def is_installed(self, root):
        return self.service_id in root.objectIds()


class ISecurityOverviewExtension(Interface):
    """Marker interface for our extension.
    """


install = SecurityOverviewInstaller("SilvaSecurityOverview",
    ISecurityOverviewExtension)



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


class ISecurityOverviewExtension(Interface):
    """Marker interface for our extension.
    """


install = SecurityOverviewInstaller("SilvaSecurityOverview",
    ISecurityOverviewExtension)



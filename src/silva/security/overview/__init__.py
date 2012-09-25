# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt
# package

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller
from zope.interface import Interface


silvaconf.extension_name("SilvaSecurityOverview")
silvaconf.extension_title("Silva Security Overview")


class Installer(DefaultInstaller):
    """Installer for the Security overview extension.
    Override install, uninstall to add more actions.
    """

    service_id = 'service_securityoverview'

    def install_custom(self, root):
        if self.service_id not in root.objectIds():
            factory = root.manage_addProduct['silva.security.overview']
            factory.manage_addSecurityOverviewService(self.service_id)

    def uninstall_custom(self, root):
        if self.service_id in root.objectIds():
            root.manage_delObjects([self.service_id])


class IExtension(Interface):
    """Marker interface for our extension.
    """


install = Installer("SilvaSecurityOverview", IExtension)



# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest
import transaction
import silva.security.overview
from Products.Silva.testing import SilvaLayer
from silva.core.interfaces import IAuthorizationManager


class SilvaSecurityOverviewLayer(SilvaLayer):

    def _install_application(self, app):
        super(SilvaSecurityOverviewLayer, self)._install_application(app)
        app.root.service_extensions.install('SilvaSecurityOverview')
        transaction.commit()


FunctionalLayer = SilvaSecurityOverviewLayer(silva.security.overview)


class TestBase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        self.service = self.root.service_securityoverview


def add_roles(content, user, *roles):
    access =  IAuthorizationManager(content)
    authorization = access.get_authorization(user, dont_acquire=True)
    for role in roles:
        authorization.grant(role)


def remove_roles(content, user):
    access =  IAuthorizationManager(content)
    authorization = access.get_authorization(user, dont_acquire=True)
    authorization.revoke()




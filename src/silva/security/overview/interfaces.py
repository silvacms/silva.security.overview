# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.interface import Interface, Attribute
from silva.core.services.interfaces import ISilvaService


class ISecurityOverviewConfiguration(Interface):
    pass


class ISecurityOverviewService(ISilvaService,
                               ISecurityOverviewConfiguration):
    """ Interface for security overview service
    """

    catalog = Attribute('zope.catalog object for indexing the objects')

    def build(root):
        """ clear all and walk down the root to index every permission
        """

    def index_object(ob):
        """ index one object
        """


class IUserRoleList(Interface):

    users = Attribute(u"Return a list of users that have permissions defined")
    roles = Attribute(u"Return list of roles")
    users_roles = Attribute(u"Return (user,role) tuple list")
    path = Attribute(u"Return path to the object")


# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

from StringIO import StringIO
import unittest

from zope.component import getUtility
from zope.interface.verify import verifyObject
from zope.intid.interfaces import IIntIds
import transaction

from Products.Silva.testing import SilvaLayer, http
from silva.security.overview import interfaces
from silva.core.interfaces import IUserAccessSecurity
import silva.security.overview


class SilvaSecurityOverviewLayer(SilvaLayer):

    def _install_application(self, app):
        super(SilvaSecurityOverviewLayer, self)._install_application(app)
        app.root.service_extensions.install('SilvaSecurityOverview')
        transaction.commit()


class TestBase(unittest.TestCase):

    layer = SilvaSecurityOverviewLayer(
                silva.security.overview,
                zcml_file='configure.zcml')

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        self.service = self.root.service_securityoverview

    def add_roles(self, content, user, *roles):
        access =  IUserAccessSecurity(content)
        authorization = access.get_user_authorization(
            user, dont_acquire=True)
        for role in roles:
            authorization.grant(role)

    def remove_roles(self, content, user):
        access =  IUserAccessSecurity(content)
        authorization = access.get_user_authorization(
            user, dont_acquire=True)
        authorization.revoke()


class TestSecurityOverviewService(TestBase):

    def test_utility_registration(self):
        self.assertTrue(hasattr(self.root, 'service_securityoverview'))
        utility = getUtility(interfaces.ISecurityOverviewService)
        self.assertEquals(utility, self.root.service_securityoverview)
        self.assertTrue(verifyObject(interfaces.ISecurityOverviewService,
            utility))


class TestIndexing(TestBase):

    def setUp(self):
        super(TestIndexing, self).setUp()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addPublication('publication', 'Publication')
        self.publication = self.root.publication

    def test_user_is_indexed(self):
        self.add_roles(self.publication, 'dummy', 'Reader')
        results = self.service.catalog.searchResults(users='dummy')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user')

    def test_roles_are_indexed(self):
        self.add_roles(self.publication, 'dummy', 'Editor')
        self.add_roles(self.publication, 'viewer', 'Reader')

        results = self.service.catalog.searchResults(roles=['Editor'])
        self.assertTrue(
            self.publication in results,
            'publication should show up when querying for user')

        results = self.service.catalog.searchResults(roles=['Reader'])
        self.assertTrue(
            self.publication in results,
            'publication should show up when querying for one of the roles')

        results = self.service.catalog.searchResults(
            roles=['Reader', 'Editor'])
        self.assertTrue(
            self.publication in results,
            'publication should show up when querying for both roles')

        results = self.service.catalog.searchResults(
            roles={'query': ['Editor', 'ChiefEditor'], 'operator': 'or'})
        self.assertTrue(
            self.publication in results,
            'publication should show up when querying for one matching role')


    def test_multiple_users_add_remove_role(self):
        self.add_roles(self.publication, 'dummy', 'Reader')
        self.add_roles(self.publication, 'editor', 'Editor')

        results = self.service.catalog.searchResults(users='dummy')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user dummy')

        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        self.add_roles(self.publication, 'editor', 'ChiefEditor')
        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        self.remove_roles(self.publication, 'editor')
        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication not in results, 'publication should'
            ' not be in the results anymore because all roles where removed'
            ' for user editor')

    def test_remove_user(self):
        self.add_roles(self.publication, 'editor', 'Editor', 'ChiefEditor')

        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        self.remove_roles(self.publication, 'editor')
        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication not in results,
            'publication should not show up in the results anymore')

    def test_content_removal(self):
        self.add_roles(self.publication, 'editor', 'Editor')
        pubid = getUtility(IIntIds).getId(self.publication)

        results = self.service.catalog.apply({"users":'editor'})
        self.assertTrue(pubid in results, 'publication should be indexed')

        self.root.manage_delObjects(['publication',])

        results = self.service.catalog.apply({'users': 'editor'})
        self.assertTrue(
            pubid not in results,
            'publication should not appear anymore in the results')


class TestCSVExport(TestBase):

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        factory = self.root.manage_addProduct["Silva"]
        factory.manage_addPublication('publication', 'Publication')
        factory.manage_addFile('file', 'File', StringIO())
        factory = self.root.publication.manage_addProduct["Silva"]
        factory.manage_addFile('file', 'File', StringIO())

        self.add_roles(self.root.file, 'editor', 'Viewer ++')
        self.add_roles(self.root.publication, 'dummy', 'Reader', 'Editor')
        self.add_roles(self.root.publication.file, 'dummy', 'Reader')
        self.add_roles(self.root.publication.file, 'editor', 'Viewer')

    def test_csv_unauthorized_export(self):
        response = http(
            'GET /root/service_securityoverview/manage_export HTTP/1.1',
            parsed=True)
        self.assertEquals(401, response.getStatus())

    def test_csv_export(self):
        response = http(
            "GET /root/service_securityoverview/manage_export HTTP/1.1\n" \
            "Authorization: Basic manager:manager",
            parsed=True)
        self.assertEquals(200, response.getStatus())
        self.assertEquals(
"""path,user,role
/root/file,editor,Viewer ++
/root/publication,dummy,Editor
/root/publication/file,dummy,Reader
/root/publication/file,editor,Viewer
""".replace("\n", "\r\n"), response.getBody())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSecurityOverviewService))
    suite.addTest(unittest.makeSuite(TestIndexing))
    suite.addTest(unittest.makeSuite(TestCSVExport))
    return suite

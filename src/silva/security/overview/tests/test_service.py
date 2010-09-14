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
from silva.core.interfaces import IAuthorizationManager
import silva.security.overview


class SilvaSecurityOverviewLayer(SilvaLayer):

    def _install_application(self, app):
        super(SilvaSecurityOverviewLayer, self)._install_application(app)
        app.root.service_extensions.install('SilvaSecurityOverview')
        transaction.commit()



def add_roles(content, user, *roles):
    access =  IAuthorizationManager(content)
    authorization = access.get_authorization(user, dont_acquire=True)
    for role in roles:
        authorization.grant(role)


def remove_roles(content, user):
    access =  IAuthorizationManager(content)
    authorization = access.get_authorization(user, dont_acquire=True)
    authorization.revoke()


class TestBase(unittest.TestCase):

    layer = SilvaSecurityOverviewLayer(
                silva.security.overview,
                zcml_file='configure.zcml')

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        self.service = self.root.service_securityoverview


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
        factory = self.publication.manage_addProduct['Silva']
        factory.manage_addLink('test_link', 'Test')
        self.link = self.publication.test_link

    def test_user_is_indexed(self):
        add_roles(self.publication, 'dummy', 'Reader')
        results = self.service.catalog.searchResults(users='dummy')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user')

    def test_roles_are_indexed(self):
        add_roles(self.publication, 'dummy', 'Editor')
        add_roles(self.publication, 'viewer', 'Reader')

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
        add_roles(self.publication, 'dummy', 'Reader')
        add_roles(self.publication, 'editor', 'Editor')

        results = self.service.catalog.searchResults(users='dummy')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user dummy')

        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        add_roles(self.publication, 'editor', 'ChiefEditor')
        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        remove_roles(self.publication, 'editor')
        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication not in results, 'publication should'
            ' not be in the results anymore because all roles where removed'
            ' for user editor')

    def test_remove_user(self):
        add_roles(self.publication, 'editor', 'Editor', 'ChiefEditor')

        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        remove_roles(self.publication, 'editor')
        results = self.service.catalog.searchResults(users='editor')
        self.assertTrue(self.publication not in results,
            'publication should not show up in the results anymore')

    def test_content_removal(self):
        add_roles(self.publication, 'editor', 'Editor')
        pubid = getUtility(IIntIds).getId(self.publication)

        results = self.service.catalog.apply({"users":'editor'})
        self.assertTrue(pubid in results, 'publication should be indexed')

        self.root.manage_delObjects(['publication',])

        results = self.service.catalog.apply({'users': 'editor'})
        self.assertTrue(
            pubid not in results,
            'publication should not appear anymore in the results')

    def test_object_renamed(self):
        add_roles(self.link, 'editor', 'Editor')
        lid = getUtility(IIntIds).getId(self.link)
        results = self.service.catalog.apply({"users":'editor'})
        self.assertTrue(lid in results, 'link should be indexed')
        self.publication.manage_renameObject('test_link', 'test_renamed')
        results = self.service.catalog.apply({"users":'editor',
            "path": "/root/publication/test_renamed"})
        self.assertEquals([lid], list(results))
        results = self.service.catalog.apply({"users":'editor',
            "path": "/root/publication/test_link"})
        self.assertEquals([], list(results))

    def test_cut_paste_object(self):
        add_roles(self.root.publication, 'editor', 'Editor')
        add_roles(self.root.publication.test_link, 'editor', 'Editor')

        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('destination', 'Destination')
        token = self.root.manage_cutObjects(['publication'])
        self.root.destination.manage_pasteObjects(token)

        service = getUtility(IIntIds)
        publication_id = service.getId(self.root.destination.publication)
        link_id = service.getId(self.root.destination.publication.test_link)

        results = self.service.catalog.apply(
            {"users":'editor',
             "path": "/root/destination"})
        self.assertEquals(set([link_id, publication_id]), set(results))


class TestCSVExport(TestBase):

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        factory = self.root.manage_addProduct["Silva"]
        factory.manage_addPublication('publication', 'Publication')
        factory.manage_addFile('file', 'File', StringIO())
        factory = self.root.publication.manage_addProduct["Silva"]
        factory.manage_addFile('file', 'File', StringIO())

        add_roles(self.root.file, 'editor', 'Viewer ++')
        add_roles(self.root.publication, 'dummy', 'Reader', 'Editor')
        add_roles(self.root.publication.file, 'dummy', 'Reader')
        add_roles(self.root.publication.file, 'editor', 'Viewer')

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

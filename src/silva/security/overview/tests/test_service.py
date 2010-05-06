import unittest

from zope.interface.verify import verifyObject
from silva.security.overview import interfaces

from zope.component import getUtility
from zope.intid.interfaces import IIntIds

from Products.Silva.tests.SilvaTestCase import user_dummy
from Products.Silva.tests.SilvaTestCase import user_editor

from Products.Silva.testing import SilvaLayer
import silva.security.overview
import transaction

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
        self.service = self.root.service_securityoverview
        self.service.ignored_roles = set(['Owner'])


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
        factory.manage_addPublication('pub', 'Publication')
        self.publication = self.root.pub

    def test_user_is_indexed(self):
        self.publication.sec_assign(user_dummy, 'Reader')
        results = self.service.catalog.searchResults(users=user_dummy)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user')

    def test_ignored_roles(self):
        self.service.ignored_roles.add('Reader')
        self.service.cleanup()
        self.publication.sec_assign(user_dummy, 'Viewer')
        self.publication.sec_assign(user_dummy, 'Reader')
        results = self.service.catalog.searchResults(roles='Reader')
        self.assertTrue(self.publication not in results, 'publication should'
            ' not show up in results since role is ignored')
        results = self.service.catalog.searchResults(roles='Viewer')
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in results since role is NOT ignored')

    def test_roles_are_indexed(self):
        self.publication.sec_assign(user_dummy, 'Reader')
        self.publication.sec_assign(user_dummy, 'Editor')

        results = self.service.catalog.searchResults(roles=['Reader'])
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user')

        results = self.service.catalog.searchResults(roles=['Reader'])
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for one of the roles')

        results = self.service.catalog.searchResults(
            roles=['Reader', 'Editor'])
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for both roles')

        results = self.service.catalog.searchResults(
            roles={'query': ['Reader', 'ChiefEditor'], 'operator': 'or'})
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for one matching role')


    def test_multiple_users_add_remove_role(self):
        self.publication.sec_assign(user_dummy, 'Reader')
        self.publication.sec_assign(user_editor, 'Editor')

        results = self.service.catalog.searchResults(users=user_dummy)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user dummy')

        results = self.service.catalog.searchResults(users=user_editor)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        self.publication.sec_assign(user_editor, 'ChiefEditor')
        results = self.service.catalog.searchResults(users=user_editor)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        self.publication.sec_revoke(user_editor, ['ChiefEditor'])
        results = self.service.catalog.searchResults(users=user_editor)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results because editor user still has Editor'
            ' role')

        self.publication.sec_revoke(user_editor, ['Editor'])
        results = self.service.catalog.searchResults(users=user_editor)
        self.assertTrue(self.publication not in results, 'publication should'
            ' not be in the results anymore because all roles where removed'
            ' for user editor')

    def test_remove_user(self):
        self.publication.sec_assign(user_editor, 'Editor')
        self.publication.sec_assign(user_editor, 'ChiefEditor')

        results = self.service.catalog.searchResults(users=user_editor)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user editor')

        self.publication.sec_remove(user_editor)
        self.assertTrue(self.publication not in results,
            'publication should not show up in the results anymore')

    def test_object_removal(self):
        self.publication.sec_assign(user_editor, 'Editor')
        intids = getUtility(IIntIds)
        pubid = intids.getId(self.publication)
        results = self.service.catalog.apply({"users":user_editor})
        self.assertTrue(pubid in results,
            'publication should be indexed')

        del self.publication
        del self.root['pub']
        results = self.service.catalog.apply({'users': user_editor})
        self.assertTrue(pubid not in results, 'publication should'
            ' not appear anymore in the results')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSecurityOverviewService))
    suite.addTest(unittest.makeSuite(TestIndexing))
    return suite



import unittest
from zope.component import queryUtility
from Testing.ZopeTestCase.layer import onsetup as ZopeLiteLayerSetup
from Products.Five import zcml

from Products.Silva.tests import SilvaTestCase
from Products.Silva.tests.layer import installPackage, SilvaLayer


from zope.interface.verify import verifyClass
from silva.security.overview.service import UserList, SecurityOverviewService
from silva.security.overview import interfaces

from zope.component import getUtility
from zope.intid.interfaces import IIntIds

from Products.Silva.tests.SilvaTestCase import user_dummy
from Products.Silva.tests.SilvaTestCase import user_editor


class SecurityOverviewLayer(SilvaLayer):

    @classmethod
    def setUp(cls):
        import silva.security.overview
        installPackage('silva.security.overview')
        zcml.load_config('configure.zcml', silva.security.overview)

    @classmethod
    def tearDown(cls):
        pass


class TestBase(SilvaTestCase.SilvaTestCase):

    layer = SecurityOverviewLayer

    def afterSetUp(self):
        super(TestBase, self).afterSetUp()
        self.installExtension('SilvaSecurityOverview')
        self.service = self.root.service_securityoverview

    def beforeTeadown(self):
        super(TestBase, self).beforeTeadown()
        self.uninstallExtension('SilvaSecurityOverview')


class TestSecurityOverviewService(TestBase):

    def test_interfaces_compliance(self):
        self.assertTrue(verifyClass(interfaces.IUserRoleList, UserList))
        self.assertTrue(verifyClass(interfaces.ISecurityOverviewService,
            SecurityOverviewService))

    def test_utility_registration(self):
        self.assertTrue(hasattr(self.root, 'service_securityoverview'))
        self.assertTrue(getUtility(interfaces.ISecurityOverviewService))


class TestIndexing(TestBase):

    def afterSetUp(self):
        super(TestIndexing, self).afterSetUp()
        self.add_publication(self.root, 'pub', 'Publication')
        self.publication = self.root.pub

    def test_user_is_indexed(self):
        self.publication.sec_assign(user_dummy, 'Reader')
        results = self.service.catalog.searchResults(users=user_dummy)
        self.assertTrue(self.publication in results, 'publication should'
            ' show up in the results when querying for user')

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
        self.assertTrue(self.publication not in results)

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



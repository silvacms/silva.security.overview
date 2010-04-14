import unittest
from Products.Silva.tests import SilvaTestCase
from zope.interface.verify import verifyObject


class TestSecurityOverviewService(SilvaTestCase.SilvaTestCase):

    def afterSetUp(self):
        pass

    def test_test(self):
        self.assertTrue(true)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSecurityOverviewService))
    return suite



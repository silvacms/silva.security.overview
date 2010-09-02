from infrae.testbrowser.browser import Browser
from silva.security.overview.tests.test_service import (add_roles,
    TestBase)
import transaction


class TestFuncService(TestBase):

    def setUp(self):
        super(TestFuncService, self).setUp()
        self.browser = Browser(self.layer._create_wsgi_application())

        factory = self.root.manage_addProduct['Silva']
        factory.manage_addPublication('publication', 'Publication')
        self.publication = self.root.publication
        factory = self.publication.manage_addProduct['Silva']
        factory.manage_addLink('test_link', 'Test')
        self.link = self.publication.test_link

        add_roles(self.publication, 'dummy', 'Reader')
        add_roles(self.link, 'viewer', 'Viewer +')
        self.service.build()
        transaction.commit()

    def test_simple_path_query_results(self):
        status = self.browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': '/root'})
        self.assertEquals(200, status)
        paths = self.browser.html.xpath('//td[@class="path"]/a/text()')
        self.assertEquals(['/root/publication', '/root/publication/test_link'],
                          paths)

    def test_simple_path_and_role(self):
        status = self.browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': '/root/publication',
                   'form.field.role': 'Viewer +'})
        self.assertEquals(200, status)
        paths = self.browser.html.xpath('//td[@class="path"]/a/text()')
        self.assertEquals(['/root/publication/test_link'],
                          paths)

    def test_simple_path_and_user(self):
        status = self.browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': '/root/publication',
                   'form.field.user': 'viewer'})
        self.assertEquals(200, status)
        paths = self.browser.html.xpath('//td[@class="path"]/a/text()')
        self.assertEquals(['/root/publication/test_link'],
                          paths)

    def test_path_replace_relative_path_in_query(self):
        status = self.browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': 'publication'})
        self.assertEquals(200, status)
        field = self.browser.html.xpath('//input[@name="form.field.path"]')[0]
        self.assertEquals('/root/publication', field.get('value'))

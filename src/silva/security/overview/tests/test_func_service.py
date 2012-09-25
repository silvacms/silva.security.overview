# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

from silva.security.overview.testing import (
    add_roles, TestBase)
import transaction


def overview_settings(browser):
    browser.inspect.add('results', '//span[@class="path"]/a')


class ServiceFunctionalTestCase(TestBase):

    def setUp(self):
        super(ServiceFunctionalTestCase, self).setUp()

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

    def test_authentication_required(self):
        browser = self.layer.get_browser(overview_settings)
        self.assertEqual(
            browser.open('/root/service_securityoverview/manage_main'),
            401)

    def test_simple_path_query_results(self):
        browser = self.layer.get_browser(overview_settings)
        browser.options.handle_errors = False
        browser.login('manager', 'manager')

        status = browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': '/root'})
        self.assertEquals(200, status)
        self.assertEquals(
            ['/root/publication', '/root/publication/test_link'],
            browser.inspect.results)

    def test_simple_path_and_role(self):
        browser = self.layer.get_browser(overview_settings)
        browser.login('manager', 'manager')

        status = browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': '/root/publication',
                   'form.field.role': 'Viewer +'})
        self.assertEquals(200, status)
        self.assertEquals(
            ['/root/publication/test_link'],
            browser.inspect.results)

    def test_simple_path_and_user(self):
        browser = self.layer.get_browser(overview_settings)
        browser.login('manager', 'manager')

        status = browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': '/root/publication',
                   'form.field.user': 'viewer'})
        self.assertEquals(200, status)
        self.assertEquals(
            ['/root/publication/test_link'],
            browser.inspect.results)

    def test_path_replace_relative_path_in_query(self):
        browser = self.layer.get_browser(overview_settings)
        browser.login('manager', 'manager')

        status = browser.open(
            '/root/service_securityoverview/manage_main',
            query={'form.action.search': 'Search',
                   'form.field.path': 'publication'})
        self.assertEquals(200, status)
        field = browser.html.xpath('//input[@name="form.field.path"]')[0]
        self.assertEquals('/root/publication', field.get('value'))

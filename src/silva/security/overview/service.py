# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

import csv
from logging import getLogger

from five import grok
from zope import interface, schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.cachedescriptors.property import CachedProperty
from zope.catalog.keyword import KeywordIndex
from zope.component import getUtility, queryMultiAdapter
from zope.intid.interfaces import IIntIds


from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject
from silva.core.interfaces import IUserAccessSecurity
from silva.core.services.base import SilvaService
from silva.core.services.utils import walk_silva_tree
from silva.core.views.views import ZMIView
from silva.security.overview.catalog import Catalog
from silva.security.overview.index import PathIndex
from silva.security.overview.interfaces import ISecurityOverviewConfiguration
from silva.security.overview.interfaces import ISecurityOverviewService
from silva.security.overview.interfaces import IUserRoleList

from zeam.form import silva as silvaforms
from zeam.utils.batch.interfaces import IBatching


from Products.Silva import roleinfo

logger = getLogger('silva.security.overview.service')


class UserList(grok.Adapter):
    grok.context(ISilvaObject)
    grok.implements(IUserRoleList)
    grok.provides(IUserRoleList)

    def __init__(self, context):
        super(UserList, self).__init__(context)
        access = IUserAccessSecurity(context)

        self.roles = set()
        self.users = []
        self.users_roles = []

        accesses = access.get_defined_authorizations(dont_acquire=True)
        for user_id, authorization in accesses.iteritems():
            role = authorization.local_role
            self.users.append(user_id)
            self.users_roles.append((user_id, role,))
            self.roles.add(role)

    @CachedProperty
    def path(self):
        return "/".join(self.context.getPhysicalPath())


class SecurityOverviewService(SilvaService):
    """ This service is responsible for managing the security events
    """
    meta_type = 'Silva Security Overview Service'
    grok.implements(ISecurityOverviewService)
    default_service_identifier = 'service_securityoverview'
    silvaconf.icon('service.png')

    manage_options = (
        {'label':'Security overview', 'action':'manage_main'},
        {'label':'Configuration', 'action': 'manage_config'},
        ) + SilvaService.manage_options

    def __init__(self, id):
        super(SecurityOverviewService, self).__init__(id)
        self.cleanup()

    def cleanup(self):
        """ Remove the entire catalog and recreates it
        """
        if hasattr(self, 'catalog'): del self.catalog
        self.catalog = self._build_catalog()
        self.catalog.__parent__ = self

    def build(self, root=None):
        self.cleanup()
        root = root or self.get_root()
        intids = getUtility(IIntIds)
        count = 0
        for (index, ob,) in enumerate(walk_silva_tree(root)):
            if self.index_object(ob, intids): count += 1
        return count

    def index_object(self, ob, intutil=None):
        intids = intutil or getUtility(IIntIds)
        try:
            intid = intids.getId(ob)
            role_list = IUserRoleList(ob)
            if role_list.roles:
                self.catalog.index_doc(intid, ob)
                return ob
            else:
                self.catalog.unindex_doc(intid)
            return None
        except KeyError:
            return None

    def build_query(self, user, role, path):
        query = {}
        if user and role:
            query['users_roles'] = {'query': [(user, role)],
                'operator': 'or'}
        if user:
            query['users'] = user
        if role:
            query['roles'] = role
        if path:
            query['path'] = {'query': path, 'include_path': True}
        return query

    def _build_catalog(self):
        catalog = Catalog()
        catalog['users'] = KeywordIndex('users', IUserRoleList, False)
        catalog['roles'] = KeywordIndex('roles', IUserRoleList, False)
        catalog['users_roles'] = KeywordIndex(
            'users_roles', IUserRoleList, False)
        catalog['path'] = PathIndex('path', IUserRoleList, False)
        return catalog


class Cycle(object):

    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.index = 0

    def cycle(self):
        try:
            return self.values[self.index]
        finally:
            self.inc()

    def inc(self):
        self.index += 1
        if self.index > (len(self) - 1):
            self.index = 0

    def __len__(self):
        return len(self.values)


def _validate_search(form):
    data, errors = form.extractData()
    if data['user'] is silvaforms.NO_VALUE and not data['role']:
        raise silvaforms.ActionError(
            'Please provide at least a user or a role')
    if data['path'] is not silvaforms.NO_VALUE:
        root_path = "/".join(form.context.get_root().getPhysicalPath())
        if not (data['path'].startswith(root_path)):
            raise silvaforms.ActionError(
                'Path is invalid. It should start with %s' % root_path)
    return True


@apply
def silva_role_source():
    roles = [SimpleTerm(value='', token='none', title='Select a role')]
    for role in roleinfo.ALL_ROLES:
        roles.append(SimpleTerm(value=role, token=role, title=role))
    return SimpleVocabulary(roles)


class ISearchSchema(interface.Interface):
    user = schema.TextLine(
        title=u"user",
        description=u"The username you are looking for (case sensitive).",
        required=False)
    role = schema.Choice(
        title=u"role",
        description=u"Silva role you are looking for.",
        source=silva_role_source,
        default='',
        required=False)
    path = schema.TextLine(
        title=u"path",
        description=u"Container path from where the search will start.",
        required=False)


class SecurityOverView(silvaforms.ZMIForm):
    name = 'manage_main'
    grok.name(name)
    grok.context(ISecurityOverviewService)

    label = u"Search for role assignement"
    description = u"This service lets you search "\
        u"for roles assigned inside Silva containers."
    fields = silvaforms.Fields(ISearchSchema)

    def update(self):
        self.entries = None

    @silvaforms.action('Search', validator=_validate_search)
    def search(self):
        catalog = self.context.catalog
        data, errors = self.extractData()
        self.data = data
        if errors:
            return silvaforms.FAILURE

        def extract(val):
            return val is not silvaforms.NO_VALUE and val or ''

        self.query = self.context.build_query(
            extract(data['user']),
            extract(data['role']),
            extract(data['path']))

        self.query['_limit'] = int(self.request.get('pagelen') or 20)
        self.query['_sort_index'] = 'path'
        logger.info('query user roles catalog: %s' % repr(self.query))
        self.entries = catalog.searchResults(
            request=self.request, **self.query)
        self.batch = queryMultiAdapter(
            (self, self.entries, self.request,), IBatching)

    @property
    def form_path(self):
        return '%s/manage_main' % self.context.absolute_url()

    @property
    def root_path(self):
        return "/".join(self.context.get_root().getPhysicalPath())

    def smi_security_url(self, obj):
        return "%s/edit/tab_access" % obj.absolute_url()

    def cycle(self, name, values):
        if not hasattr(self, '_cycles'):
            self._cycles = {}
        if not self._cycles.has_key(name):
            c = Cycle(name, values)
            self._cycles[name] = c
        else:
            c = self._cycles[name]
        return c.cycle()

    def unpack_entry(self, entry):
        user_list = IUserRoleList(entry)
        for user, role in user_list.users_roles:
            yield {'user': user,
                   'role': role,
                   'path': user_list.path,
                   'hilite': self._hilite(user, role)}

    def _hilite(self, user, role):
        hi = []
        if not hasattr(self, 'data'):
            return hi
        if self.data['user'] == user:
            hi.append('user')
        if self.data['role'] == role:
            hi.append('role')
        return hi


class SecurityConfigForm(silvaforms.ZMIComposedForm):

    grok.name('manage_config')
    grok.context(ISecurityOverviewConfiguration)

    label = u"Configuration"
    description = u"Configure security overview service."


class RebuildCatalog(silvaforms.ZMISubForm):
    silvaforms.view(SecurityConfigForm)

    label = u"Reindex"
    description = u"Go through the whole Silva site to "\
        u"reindex currently set permissions."

    @silvaforms.action('Rebuild')
    def rebuild_index(self):
        count = self.context.build()
        self.status = '%d objects indexed.' % count
        return silvaforms.SUCCESS


class SecurityServiceExporter(silvaforms.ZMISubForm):
    silvaforms.view(SecurityConfigForm)

    label = u'Export'
    description = u'Export all current permissions into a CSV file.'

    @silvaforms.action(u'Export')
    def export(self):
        self.redirect(self.context.absolute_url()  + '/manage_export')


class ExportView(ZMIView):
    grok.context(ISecurityOverviewService)
    grok.name('manage_export')

    field_names = ['path', 'user', 'role']

    def render(self):
        response = self.request.response
        response.setHeader('Content-Type', 'text/csv')
        response.setHeader('Content-Disposition',
                           'attachment; filename=silva_user_role.csv')

        data = self.context.catalog.searchResults(
            _sort_index='path',
            roles={'query': roleinfo.ASSIGNABLE_ROLES,
                   'operator': 'or'})
        writer = csv.DictWriter(response,
                                self.field_names,
                                extrasaction='ignore')
        writer.writerow(dict([(f,f,) for f in self.field_names]))
        for item in data:
            user_list = IUserRoleList(item)
            for user, role in user_list.users_roles:
                writer.writerow({'path':user_list.path,
                                 'user':user,
                                 'role':role})

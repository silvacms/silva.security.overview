from five import grok

from zope.component import getUtility, queryUtility, queryMultiAdapter
from zope.intid.interfaces import IIntIds

from silva.security.overview.catalog import Catalog
from zope.catalog.keyword import KeywordIndex
from zope.catalog.field import FieldIndex
from silva.security.overview.index import PathIndex

from zope.catalog.interfaces import ICatalog, INoAutoIndex
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.intid.interfaces import IIntIdAddedEvent, IIntIdRemovedEvent
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.cachedescriptors.property import CachedProperty

from silva.core.services.base import SilvaService
from silva.core.services.utils import walk_silva_tree
from silva.core import conf as silvaconf

from silva.security.overview.interfaces import (ISecurityOverviewService,
    ISecurityOverviewConfiguration)
from silva.core.interfaces import (ISecurityRoleAddedEvent,
    ISecurityRoleRemovedEvent, ISilvaObject)
from silva.security.overview.interfaces import IUserRoleList
from silva.core.views import views as silvaviews
from zeam.form import silva as silvaforms
from zeam.utils.batch.interfaces import IBatching

from logging import getLogger
logger = getLogger('silva.security.overview.service')


class UserList(grok.Adapter):
    grok.context(ISilvaObject)
    grok.implements(IUserRoleList)
    grok.provides(IUserRoleList)

    def __init__(self, context):
        super(UserList, self).__init__(context)
        self.service = getUtility(ISecurityOverviewService)

    @CachedProperty
    def users(self):
        return self.context.__ac_local_roles__.keys()

    @CachedProperty
    def roles(self):
        role_set = set()
        for roles in self.context.__ac_local_roles__.values():
            for role in roles:
                if role not in self.service.ignored_roles:
                    role_set.add(role)
        return role_set

    @CachedProperty
    def users_roles(self):
        users_roles = []
        for user, roles in self.context.__ac_local_roles__.iteritems():
            for role in roles:
                if role not in self.service.ignored_roles:
                    users_roles.append((user, role,))
        return users_roles

    @CachedProperty
    def path(self):
        return "/".join(self.context.getPhysicalPath())


class SecurityOverviewService(SilvaService):
    """ This service is responsible for managing the security events
    """
    meta_type = 'Silva Security Overview Service'
    grok.implements(ISecurityOverviewService)
    default_service_identifier = 'silva_securityoverview'
    silvaconf.icon('service.png')

    ignored_roles = set(['Owner'])

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
            query['roles'] = {'query': role, 'operator': 'or'}
        if path:
            query['path'] = {'query': path, 'include_path': True}
        return query

    def _build_catalog(self):
        catalog = Catalog()
        catalog['users_roles'] = KeywordIndex('users_roles', IUserRoleList, False)
        catalog['path'] = PathIndex('path', IUserRoleList, False)
        return catalog


@grok.subscribe(ISilvaObject, ISecurityRoleAddedEvent)
def role_added(ob, event):
    logger.info("event role add on %s" % "/".join(ob.getPhysicalPath()))
    if INoAutoIndex.providedBy(ob): return
    service = queryUtility(ISecurityOverviewService)
    if service:
        service.index_object(ob)

@grok.subscribe(ISilvaObject, ISecurityRoleRemovedEvent)
def role_removed(ob, event):
    logger.info("event role remove on %s" % "/".join(ob.getPhysicalPath()))
    if INoAutoIndex.providedBy(ob): return
    service = queryUtility(ISecurityOverviewService)
    if service:
        service.index_object(ob)


@grok.subscribe(ISilvaObject, IIntIdRemovedEvent)
def object_removed(ob, event):
    service = queryUtility(ISecurityOverviewService)
    intids = queryUtility(IIntIds)
    if intids and service:
        service.catalog.unindex_doc(intids.getId(ob))

@grok.subscribe(ISilvaObject, IIntIdAddedEvent)
def object_added(ob, event):
    service = queryUtility(ISecurityOverviewService)
    intids = queryUtility(IIntIds)
    if intids and service:
        service.index_object(intids.getId(ob))


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
    if data['user'] is silvaforms.NO_VALUE \
            and data['role'] is silvaforms.NO_VALUE:
        return False
    return True

class SecurityOverView(silvaforms.ZMIForm):
    name = 'manage_main'
    grok.name(name)
    grok.context(ISecurityOverviewService)

    fields = silvaforms.Fields(
        silvaforms.Field('user'),
        silvaforms.Field('role'),
        silvaforms.Field('path'))

    def update(self):
        self.entries = None

    @silvaforms.action('Search', validator=_validate_search)
    def search(self):
        catalog = self.context.catalog
        data, errors = self.extractData()
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
        results = []
        user_list = IUserRoleList(entry)
        for user, role in user_list.users_roles:
            yield {'user': user,
                   'role': role,
                   'path': user_list.path}


class SecurityConfigForm(silvaforms.ZMIComposedForm):

    grok.name('manage_config')
    grok.context(ISecurityOverviewConfiguration)

    label = u"Configuration"
    description = u"Configure security overview service"


class RebuildCatalog(silvaforms.SubForm):
    silvaforms.view(SecurityConfigForm)

    label = u"Reindex roles information of the whole silva tree"

    @silvaforms.action('Rebuild')
    def rebuild_index(self):
        count = self.context.build()
        self.status = '%d objects indexed.' % count
        return silvaforms.SUCCESS


class SecurityServiceConfiguration(silvaforms.SubForm):
    silvaforms.view(SecurityConfigForm)

    label = u"Configure security overview service options"
    actions = silvaforms.Actions(silvaforms.EditAction(u"Update"))
    fields = silvaforms.Fields(ISecurityOverviewConfiguration)
    ignoreContent = False


from five import grok

from zope.component import getUtility
from zope.intid.interfaces import IIntIds

from zope.catalog.catalog import Catalog
from zope.catalog.keyword import KeywordIndex
from zope.catalog.field import FieldIndex
from silva.security.overview.index import PathIndex

from zope.catalog.interfaces import ICatalog, INoAutoIndex
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.intid.interfaces import IIntIdAddedEvent, IIntIdRemovedEvent

from silva.core.services.base import SilvaService
from silva.core.services.utils import walk_silva_tree
from silva.core import conf as silvaconf

from silva.security.overview.interfaces import ISecurityOverviewService
from silva.core.interfaces import (ISecurityRoleAddedEvent,
    ISecurityRoleRemovedEvent, ISilvaObject)
from silva.security.overview.interfaces import IUserList
from silva.core.views import views as silvaviews


from logging import getLogger
logger = getLogger('silva.security.overview.service')

_role_ignore_set = set(['Owner'])

class UserList(grok.Adapter):
    grok.context(ISilvaObject)
    grok.implements(IUserList)
    grok.provides(IUserList)

    def users(self):
        return self.context.__ac_local_roles__.keys()

    def roles(self):
        role_set = set()
        for roles in self.context.__ac_local_roles__.values():
            for role in roles:
                if role not in _role_ignore_set: 
                    role_set.add(role)
        return role_set

    def users_roles(self):
        users_roles = []
        for user, roles in self.context.__ac_local_roles__.iteritems():
            for role in roles:
                if role not in _role_ignore_set: 
                    users_roles.append((user, role,))
        return users_roles

    def path(self):
        return self.context.getPhysicalPath()


class SecurityOverviewService(SilvaService):
    """ This service is responsible for managing the security events
    """
    meta_type = 'Silva Security Overview Service'
    grok.implements(ISecurityOverviewService)
    silvaconf.icon('service.png')

    manage_options = (
        {'label':'Security overview', 'action':'manage_main'},
        {'label':'Configuration', 'action': 'manage_config'},
        ) + SilvaService.manage_options

    def __init__(self, id, title):
        super(SecurityOverviewService, self).__init__(id, title)
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
        for (index, ob) in enumerate(walk_silva_tree(root)):
            if self.index_object(ob, intids): count += 1
        return count

    def index_object(self, ob, intutil=None):
        intids = intutil or getUtility(IIntIds)
        try:
            intid = intids.getId(ob)
            self.catalog.index_doc(intid, ob)
            return ob
        except KeyError:
            return None

    def build_query(self, user=None, roles=None):
        query = {}
        if roles and user:
            # special case :
            # we want the objects that have user with a specific role
            # not a role on any user
            users_roles = []
            for role in roles:
                users_roles.append((user, role,))
            query['users_roles'] = {'query': users_roles, 'operator': 'or'}
            return query
        if user:
            query['users'] = user
        if roles:
            query['roles'] = {'query': roles, 'operator': 'or'}
        return query

    def _build_catalog(self):
        catalog = Catalog()
        catalog['users'] = KeywordIndex('users', IUserList, True)
        catalog['roles'] = KeywordIndex('roles', IUserList, True)
        # this index aim to store which user has which role
        catalog['users_roles'] = KeywordIndex('users_roles', IUserList, True)
        catalog['path'] = PathIndex('path', IUserList, True)
        return catalog


@grok.subscribe(ISilvaObject, ISecurityRoleAddedEvent)
def role_added(ob, event):
    try:
        logger.debug("event role add on %s" % "/".join(ob.getPhysicalPath()))
        if INoAutoIndex.providedBy(ob): return
        service = getUtility(ISecurityOverviewService)
        service.index_object(ob)
    except (Exception,), e:
        logger.error('error in ISecurityRoleAddedEvent subscriber for'
            ' silva.security.overview : %s' % str(e))
        raise

@grok.subscribe(ISilvaObject, ISecurityRoleRemovedEvent)
def role_removed(ob, event):
    try:
        logger.debug("event role remove on %s" % "/".join(ob.getPhysicalPath()))
        if INoAutoIndex.providedBy(ob): return
        service = getUtility(ISecurityOverviewService)
        service.index_object(ob)
    except (Exception,), e:
        logger.error('error in ISecurityRoleRemovedEvent subscriber for'
            ' silva.security.overview : %s' % str(e))
        raise

@grok.subscribe(ISecurityOverviewService, IObjectCreatedEvent)
def configure_security_overview_service(service, event):
    """Configure the reference after it have been created. Register
    the relation catalog to the root local site.
    """
    root = service.get_root()
    sm = root.getSiteManager()
    sm.registerUtility(service.catalog, ICatalog)

@grok.subscribe(ISilvaObject, IIntIdRemovedEvent)
def object_removed(ob, event):
    root = ob.get_root()
    intids = getUtility(IIntIds)
    root.service_securityoverview.catalog.unindex_doc(intids.getId(ob))

@grok.subscribe(ISilvaObject, IIntIdAddedEvent)
def object_added(ob, event):
    root = ob.get_root()
    intids = getUtility(IIntIds)
    root.service_securityoverview.catalog.unindex_doc(intids.getId(ob))


class SecurityOverView(silvaviews.ZMIForm):
    grok.name('manage_main')

    def update(self):
        catalog = self.context.catalog
        self.query = self._build_query()
        logger.debug('query user roles catalog: %s' % repr(self.query))
        self.entries = catalog.searchResults(**self.query)

    def unpack_entry(self, entry):
        ul = IUserList(entry)
        ur = ul.users_roles()
        results = []
        for (user, role) in ur:
            results.append({'username': u, 'role': r, 'path': ul.path()})
        return results 

    def _build_query(self):

        def build_param(name):
            param = self.request.get(name)
            if param: param = param.strip().split(',')
            return param

        u = build_param('user')
        r = build_param('roles')
        return self.context.build_query(user=u, roles=r)


class SecurityConfig(silvaviews.ZMIView):
    grok.name('manage_config')

    message = ''

    def update(self):
        if self.request.method.lower() == 'post':
            if self.request.get('rebuild'):
                count = self.context.build()
                self.message = '%d objects indexed.' % count



from five import grok

from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.catalog.catalog import Catalog
from zope.catalog.keyword import KeywordIndex
from zope.catalog.interfaces import ICatalog
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from silva.core.services.base import SilvaService
from silva.core import conf as silvaconf

from silva.security.overview.interfaces import ISecurityOverviewService
from silva.core.interfaces import (ISecurityRoleAddedEvent,
    ISecurityRoleRemovedEvent, ISilvaObject)
from silva.security.overview.interfaces import IUserList
from silva.core.views import views as silvaviews

def build_index():
    catalog = Catalog()
    catalog['usernames'] = KeywordIndex('usernames', IUserList, True)
    return catalog


class UserList(grok.Adapter):
    grok.context(ISilvaObject)
    grok.implements(IUserList)
    grok.provides(IUserList)

    def usernames(self):
        return self.context.__ac_local_roles__.keys()


class SecurityOverviewService(SilvaService):
    """ This service is responsible for managing the security events
    """
    meta_type = 'Silva Security Overview Service'
    grok.implements(ISecurityOverviewService)
    silvaconf.icon('service.png')

    manage_options = (
        {'label':'Security overview', 'action':'manage_overview'},
        ) + SilvaService.manage_options

    def __init__(self, id, title):
        super(SecurityOverviewService, self).__init__
        self.catalog = build_index()

    def cleanup(self):
        """ Remove the entire catalog and recreates it
        """
        del self.catalog
        self.catalog = build_index()

    def build(self):
        self.cleanup()



@grok.subscribe(ISilvaObject, ISecurityRoleAddedEvent)
def RoleAdded(ob, event):
    if NoAutoIndex.providedBy(ob): return
    service = getUtility(ISecurityOverviewService)
    intids = getUtility(IIntIds)
    id = intids.getId(ob)
    service.catalog.index_doc(id, ob)


@grok.subscribe(ISecurityRoleRemovedEvent)
def RoleRemoved(ob, event):
    if NoAutoIndex.providedBy(ob): return
    service = getUtility(ISecurityOverviewService)
    intids = getUtility(IIntIds)
    id = intids.getId(ob)
    service.catalog.index_doc(id, ob)


@grok.subscribe(ISecurityOverviewService, IObjectCreatedEvent)
def configureReferenceService(service, event):
    """Configure the reference after it have been created. Register
    the relation catalog to the root local site.
    """
    root = service.get_root()
    sm = root.getSiteManager()
    sm.registerUtility(service.catalog, ICatalog)


class SecurityOverView(silvaviews.ZMIView):
    grok.name('manage_overview')

    def update(self):
        pass



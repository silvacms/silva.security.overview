from five import grok

from zope.component import getUtility
from zope.app.intids.interfaces import IIntIds
from zope.catalog.catalog import Catalog
from zope.catalog.attribute import 
from zope.catalog.keyword import KeywordIndex
from zope.catalog.catalog.interfaces import ICatalog
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from silva.core.services.base import SilvaService
from silva.core.conf import silvaconf

from silva.security.overview import ISilvaSecurityOverviewService
from silva.core.interfaces import (ISecurityRoleAddedEvent,
    ISecurityRoleRemovedEvent, ISilvaObject)
from silva.security.overview.interfaces import IUserList


def build_index():
    catalog = Catalog()
    catalog['usernames'] = KeywordIndex('usernames', IUserList, True)


class UserList(grok.Adapter):
    grok.context(ISilvaObject)
    grok.implements(IUserList)
    grok.provides(IUserList)

    def usernames(self):
        return self.context.__ac_local_roles__.keys()


class SilvaSecurityOverviewService(SilvaService):
    """ This service is responsible for managing the security events
    """
    meta_type = 'Silva Reference Service'
    grok.implements(ISilvaSecurityOverviewService)
    # silvaconf.icon('service.png')

    manage_options = (
        {'label':'Security overview', 'action':'manage_overview'},
        ) + SilvaService.manage_options

    def __init__(self):
        self.catalog = Catalog()

    def manage_overview(self):
        """ Security overview ZMI tab
        """
        pass


@grok.subscribe(ISilvaObject, ISecurityRoleAddedEvent)
def RoleAdded(ob, event):
    if NoAutoIndex.providedBy(ob): return
    service = getUtility(ISilvaSecurityOverviewService)
    intids = getUtility(IIntIds)
    id = intids.getId(ob)
    service.catalog.index_doc(id, ob)


@grok.subscribe(ISecurityRoleRemovedEvent)
def RoleRemoved(ob, event):
    if NoAutoIndex.providedBy(ob): return
    service = getUtility(ISilvaSecurityOverviewService)
    intids = getUtility(IIntIds)
    id = intids.getId(ob)
    service.catalog.index_doc(id, ob)


@grok.subscribe(ISilvaSecurityOverviewService, IObjectCreatedEvent)
def configureReferenceService(service, event):
    """Configure the reference after it have been created. Register
    the relation catalog to the root local site.
    """
    root = service.get_root()
    sm = root.getSiteManager()
    sm.registerUtility(service.catalog, ICatalog)



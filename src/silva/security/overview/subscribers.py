from five import grok
from zope.component import queryUtility
from zope.catalog.interfaces import INoAutoIndex
from zope.intid.interfaces import IIntIdAddedEvent, IIntIdRemovedEvent
from silva.core.interfaces import (ISecurityRoleAddedEvent,
    ISecurityRoleRemovedEvent)
from zope.intid.interfaces import IIntIds
from silva.core.interfaces import ISilvaObject
from silva.security.overview.interfaces import ISecurityOverviewService
from logging import getLogger
logger = getLogger('silva.security.overview.subscribers')


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

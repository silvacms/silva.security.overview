# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

from logging import getLogger

from five import grok
from zope.catalog.interfaces import INoAutoIndex
from zope.component import queryUtility
from zope.intid.interfaces import IIntIdAddedEvent, IIntIdRemovedEvent
from zope.intid.interfaces import IIntIds

from silva.core.interfaces import ISecurityRoleAddedEvent
from silva.core.interfaces import ISecurityRoleRemovedEvent
from silva.core.interfaces import ISilvaObject
from silva.security.overview.interfaces import ISecurityOverviewService

logger = getLogger('silva.security.overview.subscribers')


@grok.subscribe(ISilvaObject, ISecurityRoleAddedEvent)
def role_added(content, event):
    logger.info("role added on %s" % "/".join(content.getPhysicalPath()))
    if INoAutoIndex.providedBy(content):
        return
    service = queryUtility(ISecurityOverviewService)
    if service:
        service.index_object(content)


@grok.subscribe(ISilvaObject, ISecurityRoleRemovedEvent)
def role_removed(content, event):
    logger.info("role removed on %s" % "/".join(content.getPhysicalPath()))
    if INoAutoIndex.providedBy(content):
        return
    service = queryUtility(ISecurityOverviewService)
    if service:
        service.index_object(content)


@grok.subscribe(ISilvaObject, IIntIdRemovedEvent)
def content_removed(content, event):
    service = queryUtility(ISecurityOverviewService)
    intids = queryUtility(IIntIds)
    if intids and service:
        service.catalog.unindex_doc(intids.getId(content))


@grok.subscribe(ISilvaObject, IIntIdAddedEvent)
def content_added(content, event):
    service = queryUtility(ISecurityOverviewService)
    intids = queryUtility(IIntIds)
    if intids and service:
        service.index_object(intids.getId(content))

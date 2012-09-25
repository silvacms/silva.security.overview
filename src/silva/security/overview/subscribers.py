# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.catalog.interfaces import INoAutoIndex, INoAutoReindex
from zope.component import queryUtility
from zope.intid.interfaces import IIntIdAddedEvent, IIntIdRemovedEvent
from zope.lifecycleevent.interfaces import (
    IObjectMovedEvent, IObjectRemovedEvent)
from zope.intid.interfaces import IIntIds

from silva.core.interfaces import ISecurityRoleAddedEvent
from silva.core.interfaces import ISecurityRoleRemovedEvent
from silva.core.interfaces import ISilvaObject
from silva.security.overview.interfaces import ISecurityOverviewService

@grok.subscribe(ISilvaObject, ISecurityRoleAddedEvent)
def role_added(content, event):
    if INoAutoIndex.providedBy(content):
        return
    service = queryUtility(ISecurityOverviewService)
    if service:
        service.index_object(content)

@grok.subscribe(ISilvaObject, ISecurityRoleRemovedEvent)
def role_removed(content, event):
    if INoAutoIndex.providedBy(content):
        return
    service = queryUtility(ISecurityOverviewService)
    if service:
        service.index_object(content)

@grok.subscribe(ISilvaObject, IIntIdRemovedEvent)
def content_removed(content, event):
    if INoAutoIndex.providedBy(content):
        return
    service = queryUtility(ISecurityOverviewService)
    intids = queryUtility(IIntIds)
    if intids and service:
        service.catalog.unindex_doc(intids.register(content))

def index_object(content):
    service = queryUtility(ISecurityOverviewService)
    if service:
        try:
            service.index_object(content)
        except KeyError:
            pass

@grok.subscribe(ISilvaObject, IIntIdAddedEvent)
def content_added(content, event):
    if INoAutoIndex.providedBy(content):
        return
    index_object(content)

@grok.subscribe(ISilvaObject, IObjectMovedEvent)
def content_moved(content, event):
    if IObjectRemovedEvent.providedBy(event) or \
            INoAutoIndex.providedBy(content) or \
            INoAutoReindex.providedBy(content):
        return
    index_object(content)

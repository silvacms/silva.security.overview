# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt
# Path index implementation based on repoze.catalog.path2.PathIndex2

from zope.interface import implements
from persistent import Persistent
import BTrees

import zope.catalog.interfaces
import zope.catalog.attribute
import zope.index
import zope.index.interfaces
import zope.container.contained


_marker = object()


def iterpath(path):
    cur = path
    while len(cur) > 1:
        yield cur
        cur = cur[:-1]


class PathIndexStore(Persistent):

    implements(zope.index.interfaces.IInjection,
        zope.index.interfaces.IIndexSearch,
        zope.index.interfaces.IIndexSort)

    family = BTrees.family32

    def __init__(self, family=None):
        if family is not None:
            self.family = family
        self.clear()

    def clear(self):
        self.docid_to_path = self.family.IO.BTree()
        self.path_to_docid = self.family.OI.BTree()
        self.disjoint = self.family.OO.BTree()

    def __len__(self):
        return len(self.docid_to_path)

    def __nonzero__(self):
        return True

    def _getPathTuple(self, path):
        if not path:
            raise ValueError('path must be nonempty (not %s)' % str(path))

        if isinstance(path, basestring):
            path = path.rstrip('/')
            path = tuple(path.split('/'))

        if path[0] != '':
            raise ValueError('Path must be absolute (not %s)' % str(path))

        return tuple(path)

    def index_doc(self, docid, value):

        if value is _marker:
            self.unindex_doc(docid)
            return None

        path = self._getPathTuple(value)
        oldpath = self.docid_to_path.get(docid, path)
        if path != oldpath:
            self.unindex_doc(docid)

        self.docid_to_path[docid] = path
        self.path_to_docid[path] = docid

        for current_path in iterpath(path):
            theset = self.disjoint.get(current_path)
            if theset is None:
                theset = self.family.IF.Set()
                self.disjoint[current_path] = theset
            theset.insert(docid)

    def unindex_doc(self, docid):
        path = self.docid_to_path.get(docid)
        if path is None:
            return

        del self.docid_to_path[docid]
        del self.path_to_docid[path]

        for current_path in iterpath(path):
            self.disjoint[current_path].remove(docid)
            if not self.disjoint[current_path]:
                del self.disjoint[current_path]

    def search(self, path):
        path = self._getPathTuple(path)
        return self.disjoint.get(path, self.family.IF.Set())

    def apply(self, query):
        if isinstance(query, dict):
            query = query['query']
        return self.search(query)

    def sort(self, docids, reverse=False, limit=None):
        def get_path(docid):
            path_tuple = self.docid_to_path.get(docid)
            return "/".join(path_tuple)

        for i, docid in enumerate(sorted(docids,
                    key=get_path,
                    reverse=reverse)):
            yield docid
            if limit and i > limit:
                break


class IPathIndex(zope.catalog.interfaces.IAttributeIndex,
                 zope.catalog.interfaces.ICatalogIndex):
    pass


class PathIndex(zope.catalog.attribute.AttributeIndex,
                PathIndexStore,
                zope.container.contained.Contained):
    zope.interface.implements(IPathIndex)



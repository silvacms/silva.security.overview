# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

from zeam.utils.batch import Batch
from zope.catalog.catalog import Catalog as Zope3Catalog
from zope.intid.interfaces import IIntIds
from zope.component import getUtility
import zope.index


class Catalog(Zope3Catalog):

    def searchResults(self, request=None, **searchterms):
        sort_index = searchterms.pop('_sort_index', None)
        limit = searchterms.pop('_limit', None)
        reverse = searchterms.pop('_reverse', False)
        results = self.apply(searchterms)
        if results is not None:
            if sort_index is not None:
                index = self[sort_index]
                if not zope.index.interfaces.IIndexSort.providedBy(index):
                    raise ValueError('Index %s does not support sorting.' %
                                     sort_index)
                results = list(index.sort(results, reverse=reverse))
            else:
                if reverse:
                    results = list(results)
                    results.reverse()
            resolve = getUtility(IIntIds).getObject
            results = Batch(results, factory=resolve, count=limit,
                request=request)
        return results


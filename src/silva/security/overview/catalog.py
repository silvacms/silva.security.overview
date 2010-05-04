import zope.component
from zope.catalog.catalog import Catalog as Zope3Catalog
from zope.intid.interfaces import IIntIds
import zope.index
from zeam.utils.batch import batch


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
                    raise ValueError('Index %s does not support sorting.' % sort_index)
                results = list(index.sort(results, reverse=reverse))
            else:
                if reverse:
                    results = list(results)
                    results.reverse()
            uidutil = zope.component.getUtility(IIntIds)
            def factory(item):
                return uidutil.getObject(item)
            results = batch(results, factory=factory, count=limit,
                request=request)
        return results


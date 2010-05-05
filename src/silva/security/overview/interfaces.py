from zope.interface import Interface, Attribute
from zope.schema import Set, TextLine
from silva.core.services.interfaces import ISilvaService


class ISecurityOverviewConfiguration(Interface):
    ignored_roles = Set(title=u'Ignored roles',
        value_type=TextLine())


class ISecurityOverviewService(ISilvaService,
                               ISecurityOverviewConfiguration):
    """ Interface for security overview service
    """

    catalog = Attribute('zope.catalog object for indexing the objects')

    def build(root):
        """ clear all and walk down the root to index every permission
        """

    def index_object(ob):
        """ index one object
        """


class IUserRoleList(Interface):

    users = Attribute(u"Return a list of users that have permissions defined")
    roles = Attribute(u"Return list of roles")
    users_roles = Attribute(u"Return (user,role) tuple list")
    path = Attribute(u"Return path to the object")


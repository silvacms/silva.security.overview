from zope.interface import Interface, Attribute
from silva.core.services.interfaces import ISilvaService


class ISecurityOverviewService(ISilvaService):
    """ Interface for security overview service
    """

    catalog = Attribute('zope.catalog object for indexing the objects')

    def build(root):
        """ clear all and walk down the root to index every permission
        """

    def index_object():
        """ index one object
        """


class IUserList(Interface):

    def users():
        """ Return a list of users that have permissions defined
        """

    def roles():
        """ Return roles that are defined on object
        """

    def users_roles():
        """ Return (user,role) tuple list
        """

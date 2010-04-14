from zope.interface import Interface
from silva.core.services.interfaces import ISilvaService


class ISecurityOverviewService(ISilvaService):
    """ Interface for security overview service
    """


class IUserList(Interface):

    def usernames():
        """ Return the users that have permissions defined
        """

    def roles():
        """ Return roles that are defined on object
        """

    def users_roles():
        """ Return (user,role) tuple list
        """

from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from groupspace.mail import mailMessageFactory as _

from plone.app.vocabularies.users import UsersSource
from plone.app.vocabularies.groups import GroupsSource

from Acquisition import aq_inner
from plone.memoize.instance import memoize
from zope.component import getUtilitiesFor
from Products.GrufSpaces.interface import IRolesPageRole

class ImailView(Interface):
    """
    mail view interface
    """

    def test():
        """ test method"""


class mailView(BrowserView):
    """
    mail browser view
    """
    implements(ImailView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def test(self):
        """
        test method
        """
        dummy = _(u'a dummy string')

        return {'dummy': dummy}

    # View    
    @memoize
    def roles(self):
        """Get a list of roles that can be managed.
        
        Returns a list of dicts with keys:
        
            - id
            - title
        """
        context = aq_inner(self.context)
        portal_membership = getToolByName(context, 'portal_membership')
        
        pairs = []
        
        for name, utility in getUtilitiesFor(IRolesPageRole):
            permission = utility.required_permission
            if permission is None or portal_membership.checkPermission(permission, context):
                pairs.append(dict(id = name, title = utility.title))
                
        pairs.sort(key=lambda x: x["id"])
        return pairs

    @memoize
    def get_mails(self, role=None, user=None, group=None):
        """
        Get groupspace emails

        Returns unique emails of specific group members or groups
        """
    
        context = aq_inner(self.context)
        
        emails={}

        if user:
            userssource = UsersSource(context)
            user = userssource.get(user)
            user_mail = user.getProperty('email', None)
            if user_mail:
                emails={user:user_mail}
        elif group:
            groupssource = GroupsSource(context)
            group = groupssource.get(group)
            for member in group.getGroupMembers():
                user_name=member.getId()
                user_mail = member.getProperty('email', None)
                if user_mail:
                    emails[user_name]=user_mail
        else:
            if not role:
                groupspace_roles = set([r['id'] for r in self.roles()])
            elif role:
                if role in [r['id'] for r in self.roles()]:                    
                    groupspace_roles = set([role,])
                    
            if not context.group_roles is None:
                for group, roles in context.group_roles.items():
                    if set(roles).intersection(groupspace_roles):                    
                        groupssource = GroupsSource(context)
                        group = groupssource.get(group)
                        for member in group.getGroupMembers():
                            user = member.getId()
                            if not user in emails:
                                user_mail = member.getProperty('email', None)
                                if user_mail:
                                    emails[user]=user_mail

            if not context.user_roles is None:
                for user, roles in context.user_roles.items():
                    if not user in emails:
                        if set(roles).intersection(groupspace_roles):                    
                            userssource = UsersSource(context)
                            user = userssource.get(user)
                            user_mail = user.getProperty('email', None)
                            if user_mail:
                                emails[user]=user_mail
        
        result = {}
        
        reg_tool = getToolByName(context, 'portal_registration')
                
        # Verify all emails of the members                         
        for user,  email in emails.items():
            # We need emails for all member ids in the interface
            if email and reg_tool.isValidEmail(email):
                result[user]=email
        
        return result

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
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import Forbidden
from Products.statusmessages.interfaces import IStatusMessage

class mailView(BrowserView):
    """
    mail browser view
    """
    template = ViewPageTemplateFile('mailview.pt')

    @property
    def portal_registration(self):
        return getToolByName(self.context, 'portal_registration')

    @property
    def portal_membership(self):
        return getToolByName(self.context, 'portal_membership')
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        """Send the email or render the page
        """
        form = self.request.form
        submitted = form.get('form.submitted', False)
        send_button = form.get('form.button.Send', None) is not None    
        if submitted and send_button:
            if not self.request.get('REQUEST_METHOD','GET') == 'POST':
                raise Forbidden
            authenticator = self.context.restrictedTraverse('@@authenticator', None) 
            if not authenticator.verify(): 
                raise Forbidden
            send_to_members = form.get('send_to_members', [])
            send_from_address = form.get('send_from_address', [])
            comment = form.get('comment', "")
            
            proceed_to_send_mail = True
            if not comment:
                IStatusMessage(self.request).addStatusMessage(_(u"Please fill in a message."), type='error')
                proceed_to_send_mail = False
            if not send_to_members:
                IStatusMessage(self.request).addStatusMessage(_(u"Select at least one recipient."), type='error')
                proceed_to_send_mail = False
            if not self.portal_registration.isValidEmail(send_from_address):
                IStatusMessage(self.request).addStatusMessage(_(u"Please enter a valid email address."), type='error')              
                proceed_to_send_mail = False
            
            if proceed_to_send_mail:
                IStatusMessage(self.request).addStatusMessage(_(u"Emails sent."), type='info')
                
        return self.template()

    # View    
    @memoize
    def roles(self):
        """Get a list of roles that can be managed.
        
        Returns a list of dicts with keys:
        
            - id
            - title
        """
        context = aq_inner(self.context)
        
        pairs = []
        
        for name, utility in getUtilitiesFor(IRolesPageRole):
            permission = utility.required_permission
            if permission is None or self.portal_membership.checkPermission(permission, context):
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
     
        userssource = UsersSource(context)
        groupssource = GroupsSource(context)

        if user and not context.user_roles is None and user in context.user_roles:
            # Send mail to a specific user
            # The user does really have a local role here
            user_object = userssource.get(user)
            user_mail = user_object.getProperty('email', None)
            # Make sure the email address is valid
            if user_mail and self.portal_registration.isValidEmail(user_mail):
                user_name = user_object.getProperty('fullname', None)
                emails[user] = [user_name, user, user_mail]
            return emails.values()
            
        if group and not context.group_roles is None and group in context.user_roles:
            # Send mail to a specific group
            # The user does really have a local role here
            group_object = groupssource.get(group)
            for user_object in group_object.getGroupMembers():
                user = user_object.getId()
                # No need to consider users twice
                if not user in emails:
                    user_mail = user_object.getProperty('email', None)
                    # Make sure the email address is valid
                    if user_mail and self.portal_registration.isValidEmail(user_mail):
                        user_name = user_object.getProperty('fullname', None)
                        emails[user] = [user_name, user, user_mail]
            result = emails.values()
            # Sort by user name
            result.sort()
            return result
 
        # From here on all users and groups are considered

        # If a specific role is given, only this is considered
        # Otherwise only the allowed roles are considered 
        if not role:
            # If no specific role is given, consider them all
            groupspace_roles = set([r['id'] for r in self.roles()])
        elif role:
            # Make sure the selected role is really existing
            if role in [r['id'] for r in self.roles()]:                    
                groupspace_roles = set([role,])
 
        # Collect all users from the groups having local roles
        if not context.group_roles is None:
            for group, roles in context.group_roles.items():
                # Check that the group has a role that we are interested in
                if set(roles).intersection(groupspace_roles):
                    group_object = groupssource.get(group)
                    # We go through all users of the group to get the emails
                    for user_object in group_object.getGroupMembers():
                        user = user_object.getId()
                        # No need to consider users twice
                        if not user in emails:
                            user_mail = user_object.getProperty('email', None)
                            # Make sure the email address is valid
                            if user_mail and self.portal_registration.isValidEmail(user_mail):
                                    user_name = user_object.getProperty('fullname', None)
                                    emails[user] = [user_name, user, user_mail]

        # Collect all users having local roles
        if not context.user_roles is None:
            for user, roles in context.user_roles.items():
                # No need to consider users twice
                if not user in emails:
                    # Check that the user has a role that we are interested in
                    if set(roles).intersection(roles):
                        user_object = userssource.get(user)        
                        user_mail = user_object.getProperty('email', None)
                        # Make sure the email address is valid
                        if user_mail and self.portal_registration.isValidEmail(user_mail):
                            user_name = user.getProperty('fullname', None)
                            emails[user] = [user_name, user, user_mail]
       
        result = emails.values()
        # Sort by user name
        result.sort()
        return result

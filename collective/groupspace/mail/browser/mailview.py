"""
View for sending mail to a groupspace
"""
import sys

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from collective.groupspace.mail import MAIL_MESSAGE_FACTORY as _

from plone.app.vocabularies.users import UsersSource
from plone.app.vocabularies.groups import GroupsSource

from Acquisition import aq_inner
from plone.memoize.instance import memoize
from zope.component import getUtilitiesFor
from Products.GrufSpaces.interface import IRolesPageRole
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import Forbidden
from Products.statusmessages.interfaces import IStatusMessage
from smtplib import SMTPServerDisconnected
from smtplib import SMTPSenderRefused
from smtplib import SMTPRecipientsRefused
from smtplib import SMTPDataError
from smtplib import SMTPConnectError
from smtplib import SMTPHeloError
from smtplib import SMTPAuthenticationError
import socket

class MailView(BrowserView):
    """
    mail browser view
    """
    template = ViewPageTemplateFile('mailview.pt')

    @property
    def portal_registration(self):
        """
        Make portal_registration available as a property
        """
        return getToolByName(self.context, 'portal_registration')

    @property
    def portal_membership(self):
        """
        Make portal_membership available as a property
        """
        return getToolByName(self.context, 'portal_membership')

    @property
    def site_properties(self):
        """
        Make site_properties available as a property
        """
        return getToolByName(self.context, 'portal_properties').site_properties
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.errors = {}

    def __call__(self):
        """Send the email or render the page
        """
        form = self.request.form
        submitted = form.get('form.submitted', False)
        send_button = form.get('form.button.Send', None) is not None    
        if submitted and send_button:
            if not self.request.get('REQUEST_METHOD','GET') == 'POST':
                raise Forbidden
            authenticator = self.context.restrictedTraverse('@@authenticator', 
                                                            None) 
            if not authenticator.verify(): 
                raise Forbidden
            send_to_members = form.get('send_to_members', [])
            send_from_address = form.get('send_from_address', [])
            message = form.get('message', "")
            
            proceed_to_send_mail = True
                        
            if not message:
                msg = _(u"Please fill in a message.")
                self.errors['message'] = msg
                proceed_to_send_mail = False
            if not send_to_members:
                msg = _(u"Select at least one recipient.")
                self.errors['send_to_members'] = msg
                proceed_to_send_mail = False
            if not self.portal_registration.isValidEmail(send_from_address):
                msg = _(u"Please enter a valid email address.")
                self.errors['send_from_address'] = msg              
                proceed_to_send_mail = False
            
            status_message = IStatusMessage(self.request)
            if proceed_to_send_mail:
                # Refetch all the user mails so no fake user ids can be injected
                mails = self.get_mails(role=form.get('role', None),
                                       user=form.get('user', None),
                                       group=form.get('group', None))
                success, msg = self.send(mails, 
                                         send_from_address, 
                                         send_to_members, 
                                         message)
                if success:
                    status_message.addStatusMessage(msg, type='info')
                else:
                    status_message.addStatusMessage(msg, type='error')
            else:
                msg = _(u"Please correct the indicated errors.")
                status_message.addStatusMessage(msg, type='error')
                
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
        
        check_permission = self.portal_membership.checkPermission

        for name, utility in getUtilitiesFor(IRolesPageRole):
            permission = utility.required_permission
            if permission is None or check_permission(permission, context):
                pairs.append(dict(id = name, title = utility.title))
                
        pairs.sort(key=lambda x: x["id"])
        return pairs

    @memoize
    def get_mails(self, role=None, user=None, group=None):
        """
        Get groupspace emails

        Returns unique emails of specific group members or groups
        """
        if user:
            return self.get_user_mails()
            
        if group:
            return self._get_group_mails()

        is_valid_email = self.portal_registration.isValidEmail 
        context = aq_inner(self.context)        
        emails = {}     
        userssource = UsersSource(context)
        groupssource = GroupsSource(context)
 
        # From here on all users and groups are considered

        # If a specific role is given, only this is considered
        # Otherwise only the allowed roles are considered 
        if not role:
            # If no specific role is given, consider them all
            groupspace_roles = set([r['id'] for r in self.roles()])
        elif role:
            # Make sure the selected role is really existing
            if role in [r['id'] for r in self.roles()]:                    
                groupspace_roles = set([role, ])
 
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
                            if user_mail and is_valid_email(user_mail):
                                user_name = user_object.getProperty('fullname', 
                                                                    None)
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
                        if user_mail and is_valid_email(user_mail):
                            user_name = user_object.getProperty('fullname', 
                                                                None)
                            emails[user] = [user_name, user, user_mail]
       
        result = emails.values()
        # Sort by user name
        result.sort()
        return result

    def _get_user_mails(self, user):
        """
        Get the user information if he has local roles
        """
        is_valid_email = self.portal_registration.isValidEmail
        context = aq_inner(self.context)
        emails = {}
        userssource = UsersSource(context)
        if not context.user_roles is None and user in context.user_roles:
            # Send mail to a specific user
            # The user does really have a local role here
            user_object = userssource.get(user)
            user_mail = user_object.getProperty('email', None)
            # Make sure the email address is valid
            if user_mail and is_valid_email(user_mail):
                user_name = user_object.getProperty('fullname', None)
                emails[user] = [user_name, user, user_mail]
            return emails.values()

    def _get_group_mails(self, user):
        """
        Get the information of the members of the group if the group 
        has local roles.
        """
        is_valid_email = self.portal_registration.isValidEmail
        context = aq_inner(self.context)
        emails = {}
        groupssource = GroupsSource(context)
        if not context.group_roles is None and group in context.group_roles:
            # Send mail to a specific group
            # The user does really have a local role here
            group_object = groupssource.get(group)
            for user_object in group_object.getGroupMembers():
                user = user_object.getId()
                # No need to consider users twice
                if not user in emails:
                    user_mail = user_object.getProperty('email', None)
                    # Make sure the email address is valid
                    if user_mail and is_valid_email(user_mail):
                        user_name = user_object.getProperty('fullname', 
                                                            None)
                        emails[user] = [user_name, user, user_mail]
            result = emails.values()
            # Sort by user name
            result.sort()
            return result

    def send(self, mails, send_from_address, send_to_members, message):
        """
        Send the mail
        """

        context = aq_inner(self.context)

        encoding = self.site_properties.getProperty('default_charset', 'UTF-8')
                            
        host = context.MailHost
    
        to_emails = []
        for user_name, user_id, user_email in mails:
            if user_id in send_to_members:
                to_emails.append(user_email)
                          
        member  = self.portal_membership.getAuthenticatedMember()
        from_name = member.getProperty('fullname', member.getId())

        variables = {'content_title'  : context.Title(),
                     'content_url'    : context.absolute_url(),
                     'from_email'     : send_from_address,
                     'from_name'      : from_name,
                     'to_emails'      : ','.join(to_emails),
                     'default_charset': encoding,
                     'message'        : message,
                    }
                          
        mail_text = """To: %(to_emails)s
From: %(from_email)s
Errors-to: %(from_email)s
Subject: Message to the group "%(content_title)s"
Content-Type: text/plain; charset=%(default_charset)s
Content-Transfer-Encoding: 8bit

The following message has been written by 

    %(from_name)s

to the group 

    %(content_title)s

located at 

    %(content_url)s

%(message)s
    """ % variables
    
        try:
            host.send(mail_text)
        except (SMTPServerDisconnected,
                SMTPSenderRefused,
                SMTPRecipientsRefused,
                SMTPDataError,
                SMTPConnectError,
                SMTPHeloError,
                SMTPAuthenticationError,
                socket.error):
            exc, e, tb = sys.exc_info()
            return False, _(u"An error occurred while sending the email. %s" % str(e)) 
        except:
            raise
        return True, _(u"Emails sent.")
                    

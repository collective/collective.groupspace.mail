"""
Notification about changed roles
"""

from plone.app.vocabularies.users import UsersSource
from plone.app.vocabularies.groups import GroupsSource

from Products.MailHost.MailHost import MailHostError
from Products.CMFCore.utils import getToolByName
from Products.validation.i18n import recursiveTranslate
from Products.statusmessages.interfaces import IStatusMessage

from collective.groupspace.mail import MAIL_MESSAGE_FACTORY as _

import logging
logger = logging.getLogger('Plone')

from smtplib import SMTPServerDisconnected
from smtplib import SMTPSenderRefused
from smtplib import SMTPRecipientsRefused
from smtplib import SMTPDataError
from smtplib import SMTPConnectError
from smtplib import SMTPHeloError
from smtplib import SMTPAuthenticationError

import socket

def notify_change(obj, event):
    """
    Notify the members about their changed roles
    Roles can be changed for several members at the same time
    """
    # The roles view has a notify_user_assignment checkbox        
    request = event.request
    if request and request.has_key('notify_user_assignment'):
        notifications = get_user_notifications(obj, event)
        notifications.update(get_group_notifications(obj, event))

        success, msg = send_mail(obj, notifications)

        status_message = IStatusMessage(request)
        if success:
            status_message.addStatusMessage(msg, type='info')
        else:
            status_message.addStatusMessage(msg, type='error')

def get_user_notifications(obj, event):
    """
    Collect all the users with new/changed roles and send mail    
    """   
    registration = getToolByName(obj, 'portal_registration')

    # Unite user ids
    users = set(event.old_user_roles.keys())
    users.update(set(event.new_user_roles.keys()))

    userssource = UsersSource(obj)

    notifications = {}

    for user in users:
        old_roles = event.old_user_roles.get(user, [])
        new_roles = event.new_user_roles.get(user, [])
        # Ony notify if something has changed
        if old_roles != new_roles:
            # Get the email and if it is ok store the notification 
            # information
            user = userssource.get(user)
            user_id = user.getId()
            email = user.getProperty('email', None)
            if email and registration.isValidEmail(email):
                notifications[user_id] = {'old_roles':set(old_roles),
                                          'new_roles':set(new_roles),
                                          'email':email,
                                         }

    return notifications

def get_group_notifications(obj, event):
    """
    Collect all the users with new/changed roles and send mail    
    """   
    registration = getToolByName(obj, 'portal_registration')

    # Unite group ids
    groups = set(event.old_group_roles.keys())
    groups.update(set(event.new_group_roles.keys()))

    notifications = {}

    groupssource = GroupsSource(obj)

    for group in groups:
        old_roles = event.old_group_roles.get(group, [])
        new_roles = event.new_group_roles.get(group, [])
        # Ony notify if something has changed
        if old_roles != new_roles:
            group = groupssource.get(group)
            for member in group.getGroupMembers():
                member_id = member.getId()
                # If the user has already been considered, add to the roles
                if notifications.has_key(member_id):
                    notifications[member_id]['old_roles'].update(set(old_roles))
                    notifications[member_id]['new_roles'].update(set(new_roles))
                else:
                    # Get the email and if it is ok store the notification
                    # information
                    email = member.getProperty('email', None)
                    if email and registration.isValidEmail(email):
                        notifications[member_id] = {'old_roles':set(old_roles),
                                                    'new_roles':set(new_roles),
                                                    'email':email,
                                                   }
    return notifications
           
def send_mail(obj, notification):    
    """
    Send mail to all recipients
    """
    member = getToolByName(obj, 'portal_membership').getAuthenticatedMember()
    from_email = member.getProperty('email')

    site_props = getToolByName(obj, 'portal_properties').site_properties
    encoding = site_props.getProperty('default_charset', 'UTF-8')

    registration = getToolByName(obj, 'portal_registration')
    if from_email and registration.isValidEmail(from_email):    
        pass
    else:
        return False, _(u"Your email address is invalid: %s" % str(from_email))

    host = obj.MailHost

    errors = {}

    kw = {}
    kw['REQUEST'] = self.request

    subject = recursiveTranslate(_(u'Your roles have changed in the GroupSpace ${content_title}', mapping= {'content_title': obj.Title()}), **kw) 

    for info in notification.values():
        
        old_roles = list(info['old_roles'])
        old_roles.sort()
        new_roles = list(info['new_roles'])
        old_roles.sort()

        msg = recursiveTranslate(_(u'You now have the following roles in the group \"${content_title}\":\n\t${new_roles}\nlocated at\n${content_url}\nBefore the change, you had the following roles in the group:\n\t${old_roles}', 
                                    mapping= {'content_title': obj.Title(), 
                                              'new_roles' : str(', '.join(new_roles)), 
                                              'content_url' : obj.absolute_url(), 
                                              'old_roles' : str(', '.join(old_roles))}),
                                  **kw)

        try:
            host.send(
                safe_unicode(msg),
                mto=info['email'],
                mfrom=from_email,
                subject=safe_unicode(subject),
                charset=encoding)
        except (SMTPServerDisconnected,
                SMTPSenderRefused,
                SMTPRecipientsRefused,
                SMTPDataError,
                SMTPConnectError,
                SMTPHeloError,
                SMTPAuthenticationError,
                socket.error,
                MailHostError), e:
            logger.error("collective.groupspace.mail error: %s", e, exc_info=1)
            errors[str(e)] = True
        except Exception, e:
            logger.error("collective.groupspace.mail error: %s", e, exc_info=1)
            raise

    if errors:
        return False, _(u"An error occurred while sending the email. %s" % ','.join(errors.keys()))
    
    return True, _(u"Notification emails sent.")




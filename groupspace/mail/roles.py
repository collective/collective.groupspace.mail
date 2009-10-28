"""
Notification about changed roles
"""

from Products.CMFCore.utils import getToolByName
from plone.app.vocabularies.users import UsersSource
from plone.app.vocabularies.groups import GroupsSource

from smtplib import SMTPServerDisconnected
from smtplib import SMTPSenderRefused
from smtplib import SMTPRecipientsRefused
from smtplib import SMTPDataError
from smtplib import SMTPConnectError
from smtplib import SMTPHeloError
from smtplib import SMTPAuthenticationError

def notify_change(obj, event):
    """
    Notify the members about their changed roles
    Roles can be changed for several members at the same time
    """
    # The roles view has a notify_user_assignment checkbox        
    if obj.request.has_key('notify_user_assignment'):
        notifications = get_user_notifications(obj, event)
        notifications.update(get_group_notifications(obj, event))
        send_mail(obj, notifications)

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
                
    variables = {'content_title'  : obj.Title(),
                 'content_url'    : obj.absolute_url(),
                 'from_email'     : from_email,
                 'default_charset': encoding,
                }
    
    registration = getToolByName(obj, 'portal_registration')
    if from_email and registration.isValidEmail(from_email):    
        pass
    else:
        return

    host = obj.MailHost

    for info in notification.values():
        old_roles = list(info['old_roles'])
        old_roles.sort()
        new_roles = list(info['new_roles'])
        old_roles.sort()
        variables['new_roles'] = ', '.join(new_roles)
        variables['old_roles'] = ', '.join(old_roles)
        variables['to_email'] = info['email']
        
        mail_text = """To: %(to_email)s
From: %(from_email)s
Errors-to: %(from_email)s
Subject: Your roles have change in the GroupSpace "%(content_title)s"
Content-Type: text/plain; charset=%(default_charset)s
Content-Transfer-Encoding: 8bit

You now have the following roles in the group "%(content_title)s":

%(new_roles)s

located at 

%(content_url)s

Before the change, you had the following roles in the group:

%(old_roles)s
""" % variables
        try:
            host.send(mail_text)
        except SMTPServerDisconnected:
            raise
        except SMTPSenderRefused:
            raise
        except SMTPRecipientsRefused:
            raise
        except SMTPDataError:
            raise
        except SMTPConnectError:
            raise
        except SMTPHeloError:
            raise
        except SMTPAuthenticationError:
            raise

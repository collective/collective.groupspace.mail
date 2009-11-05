"""
Common configuration constants for collective.groupspace.mail
"""

from Products.CMFCore.permissions import setDefaultRoles

# Controls access to the "email" page
SEND_MAIL_PERMISSION = "collective.groupspace.mail: Send Mail to Group"
# The send mail permission should not be given to any role by default
# This way it is sufficient to check only this permission when showing
# the mail to group portlet. If this mail permission were available
# globally we would also have to check whether we are in the context
# of a groupspace, or below.
setDefaultRoles(SEND_MAIL_PERMISSION, ())


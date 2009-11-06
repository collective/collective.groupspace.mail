"""
A portlet for sending mails to users of a groupspace.
"""

from zope.interface import Interface
from zope.interface import implements
from zope.interface import directlyProvides

from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from zope import schema
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from collective.groupspace.mail import MAIL_MESSAGE_FACTORY as _

from Acquisition import aq_inner
from Acquisition import aq_parent

from plone.memoize.compress import xhtml_compress
from plone.memoize import ram
from plone.memoize.instance import memoize
from plone.app.portlets.cache import render_cachekey

from zope.component import queryAdapter
from plone.portlets.interfaces import IPortletContext

from zope.component import getUtilitiesFor

from collective.groupspace.roles.interfaces import IRolesPageRole
from collective.groupspace.roles.interfaces import ILocalGroupSpacePASRoles
from collective.groupspace.mail.config import SEND_MAIL_PERMISSION

from zope.component import getMultiAdapter

class IGroupMailPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IGroupMailPortlet)

    def __init__(self):
        pass

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return "Group Mail"

class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('groupmailportlet.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)
         
        context = aq_inner(self.context)
        self.membership = getToolByName(context, 'portal_membership')
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        self.portal_url = portal_state.portal_url()

    @property
    def mail_permission(self):
        """
        Check the special mail permission for the groupspace.
        """
        context = aq_inner(self.context)
        permission = SEND_MAIL_PERMISSION
        return self.membership.checkPermission(permission, context)

    @property
    def available(self):
        """
        Only make the porlet available when the user has the mail permission.
        """
        return self.mail_permission

    @memoize
    def role_settings(self):
        context = aq_inner(self.context)
        groupspace = self._get_groupspace(context)
        assert(not groupspace is None)
        view = getMultiAdapter((groupspace, self.request), name='roles')
        return view.existing_role_settings()

    def _get_groupspace(self, object):
        for obj in self._parent_chain(object):
            if  ILocalGroupSpacePASRoles.providedBy(obj):
                return obj

    def _parent_chain(self, obj):
        """Iterate over the containment chain"""
        while obj is not None:
            yield obj
            new = aq_parent(aq_inner(obj))
            # if the obj is a method we get the class
            obj = getattr(obj, 'im_self', new)
            
class AddForm(base.NullAddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """

    def create(self):
        """
        Construct the added assignment.
        """
        return Assignment()




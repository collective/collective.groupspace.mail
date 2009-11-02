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

from groupspace.mail import MAIL_MESSAGE_FACTORY as _

from Acquisition import aq_inner
from Acquisition import aq_parent

from plone.memoize.compress import xhtml_compress
from plone.memoize import ram
from plone.memoize.instance import memoize
from plone.app.portlets.cache import render_cachekey

from zope.component import queryAdapter
from plone.portlets.interfaces import IPortletContext

from zope.component import getUtilitiesFor

from Products.GrufSpaces.interface import IRolesPageRole
from groupspace.roles.interfaces import ILocalGroupSpacePASRoles

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

    @property
    def mail_permission(self):
        """
        Check the special mail permission for the groupspace.
        """
        context = aq_inner(self.context)
        permission = "GrufSpaces: Send Mail to GroupSpace Members"
        return self.membership.checkPermission(permission, context)

    @property
    def available(self):
        """
        Only make the porlet available when the user has the mail permission.
        """
        return self.mail_permission()

    @memoize
    def role_settings(self):
        context = aq_inner(self.context)
        groupspace = self._get_groupspace(context)
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
    form_fields = form.Fields(IGroupMailPortlet)

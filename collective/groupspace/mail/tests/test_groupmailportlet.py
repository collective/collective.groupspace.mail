from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

from plone.portlets.interfaces import IPortletType
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletDataProvider
from plone.portlets.interfaces import IPortletRenderer

from plone.app.portlets.storage import PortletAssignmentMapping

from collective.groupspace.mail.portlets import groupmailportlet
from collective.groupspace.mail.tests.base_groupmailportlet import TestCase
from collective.groupspace.roles.interfaces import ILocalGroupSpacePASRoles

class TestPortlet(TestCase):

    def afterSetUp(self):
        self.setRoles(('Manager',))

    def test_portlet_type_registered(self):
        portlet = getUtility(IPortletType, name='collective.groupspace.mail.portlets.GroupMailPortlet')
        self.assertEquals(portlet.addview, 'collective.groupspace.mail.portlets.GroupMailPortlet')

    def test_interfaces(self):
        # TODO: Pass any keywoard arguments to the Assignment constructor
        portlet = groupmailportlet.Assignment()
        self.failUnless(IPortletAssignment.providedBy(portlet))
        self.failUnless(IPortletDataProvider.providedBy(portlet.data))

    def test_invoke_add_view(self):
        portlet = getUtility(IPortletType, name='collective.groupspace.mail.portlets.GroupMailPortlet')
        mapping = self.portal.restrictedTraverse('++contextportlets++plone.leftcolumn')
        for m in mapping.keys():
            del mapping[m]
        addview = mapping.restrictedTraverse('+/' + portlet.addview)

    def test_obtain_renderer(self):
        context = self.folder
        request = self.folder.REQUEST
        view = self.folder.restrictedTraverse('@@plone')
        manager = getUtility(IPortletManager, name='plone.rightcolumn', context=self.portal)

        # TODO: Pass any keywoard arguments to the Assignment constructor
        assignment = groupmailportlet.Assignment()

        renderer = getMultiAdapter((context, request, view, manager, assignment), IPortletRenderer)
        self.failUnless(isinstance(renderer, groupmailportlet.Renderer))


class TestRenderer(TestCase):

    def afterSetUp(self):
        self.setRoles(('Manager',))
        alsoProvides(self.folder, ILocalGroupSpacePASRoles)
        self.folder.user_roles = None
        self.folder.group_roles = None
        self.folder.reindexObject()
        self.folder.invokeFactory('Document', 'document1')
        self.document = self.folder.document1

    def renderer(self, context=None, request=None, view=None, manager=None, assignment=None):
        context = context or self.folder
        request = request or self.folder.REQUEST
        view = view or self.folder.restrictedTraverse('@@plone')
        manager = manager or getUtility(IPortletManager, name='plone.rightcolumn', context=self.portal)

        # TODO: Pass any default keywoard arguments to the Assignment constructor
        assignment = assignment or groupmailportlet.Assignment()
        return getMultiAdapter((context, request, view, manager, assignment), IPortletRenderer)

    def test_render_on_groupspace(self):
        # TODO: Pass any keyword arguments to the Assignment constructor
        r = self.renderer(context=self.folder, assignment=groupmailportlet.Assignment())
        r = r.__of__(self.folder)
        r.update()
        output = r.render()
        # TODO: Test output

    def test_render_on_content_inside_groupspace(self):
        # TODO: Pass any keyword arguments to the Assignment constructor
        r = self.renderer(context=self.document, assignment=groupmailportlet.Assignment())
        r = r.__of__(self.document)
        r.update()
        output = r.render()
        # TODO: Test output



def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortlet))
    suite.addTest(makeSuite(TestRenderer))
    return suite

from zope.i18nmessageid import MessageFactory
mailMessageFactory = MessageFactory('groupspace.mail')

def initialize(context):
    """ Intializer called when used as a Zope 2 product.
    """

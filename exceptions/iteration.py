from .basic import BasicSecondaryException


class DoesNotBelong(BasicSecondaryException):
    """This can be used to mark failed containment check-ups"""
    pass



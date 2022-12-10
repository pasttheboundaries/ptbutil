class ValidationError(Exception):
    pass

class ContainmentError(Exception):
    pass

class DoesNotBelong(Exception):
    """This can be used to mark failed containment check-ups"""
    pass

class ParsingError(Exception):
    pass
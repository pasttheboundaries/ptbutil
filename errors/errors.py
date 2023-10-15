

# validation --------------------
class ValidationError(Exception):
    pass


# containment -------------------
class ContainmentError(ValueError):
    pass


class DoesNotBelong(ContainmentError):
    """This can be used to mark failed containment check-ups"""
    pass


class NotInDataBase(ContainmentError):
    pass


# code --------------------------
class CodeError(Exception):
    pass


class DecorationError(CodeError):
    pass


# parsing ------------------------
class ParsingError(Exception):
    pass

# machinelearning ----------------
class MachineLearningError(Exception):
    pass

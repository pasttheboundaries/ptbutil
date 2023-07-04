

class ExitCall:
    """
    This is a context manager that calls the declared callables at exit in the order of declaration
    """
    def __init__(self, *calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for call in self.calls:
            if callable(call):
                call()

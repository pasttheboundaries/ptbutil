from functools import partial


def smart_repr(*args):
    """
    class decorator

    use:
    @smart_repr('param1', 'param2')
    class MyClass:
        ....

    # adds __repr__ method that looks like this:
    <ClassName param1='X' param2=1>
    param names (str) must be given at decoration time

    if used without parameter names the repr will be
    <MyClass>

    """
    if len(args) == 1 and isinstance(args[0], type):
        return class_name_repr_decorator(args[0])
    elif len(args) >= 1 and all(isinstance(a, str) for a in args):
        return partial(class_name_repr_decorator, params=args)
    else:
        raise RuntimeError('Wrong use of a smart_repr decorator')


def class_name_repr_decorator(cls, params=tuple()):
    def repr_(self):
        s = f'<{self.__class__.__name__}'
        for param in params:
            s += f' {param}={getattr(self, param)}'
        s += '>'
        return s
    cls.__repr__ = repr_
    return cls

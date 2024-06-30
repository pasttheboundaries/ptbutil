from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
import json
from collections.abc import Mapping
from datetime import datetime


TYPE_ANNOTATION_KEY = 'TYPE__'
INIT_ANNOTATION_KEY = 'INIT__'
ATTRS_ANNOTATION_KEY = 'ATTRS__'


class PtbSerializable(ABC):
    """
    This is an abstract class but should not be used for subclassing in the traditional manner.

    It has two modes of peration:

    A. DECORATING (registering) USER CLASSES
        @PtbSerializable.register decorator should be used upon a subclass definition
        This will achieve 2 goals:
        1) add PtbSerializable to decorated class __bases__ and force joining required methods to the subclass,
        just as in normal subclassing.
        Required methods are:
        - serialization_init_params(self)
        - serialization_instance_attrs(self)

        for the methods details see methods __doc__strings

        2) will register the class with PtbSerializable.SERIALIZABLE_REGISTRY,
        which is necessary for the encoding and decoding
        while serialization and instantiation of custom classes by
        hisrobot.exchange.serialize (and deserialize) functions, using json library.


    B. Registering foreign types:
        Any type cane be registered as a foreign serializable type
        This is performed by calling  PtbSerializable.register_foreign with the type.
        For example:
        PtbSerializable.register_foreign(datetime, serializable_init_params=lambda x: {'*': x.timetuple()[:6]})
        registers datetime.datetime type and defines the serializable_init_params function
    """

    SERIALIZABLE_REGISTRY = dict()
    FOREIGN_SERIALIZABLE_REGISTRY = dict()

    @classmethod
    def register(cls, subclass):
        """
        this is a class decorator
        The decorated class will be altered so PtbSerializable will be added to the class bases
        as per PtbSerializable.__doc__

        """
        bases = tuple([b for b in subclass.__bases__ if b is not object] + [cls])
        new_type = type(subclass.__name__, bases, dict(subclass.__dict__))
        PtbSerializable.SERIALIZABLE_REGISTRY[subclass.__name__] = new_type
        return new_type

    @classmethod
    def register_foreign(cls,
                         type_: type,
                         serializable_init_params: Optional[Callable] = None,
                         serialization_instance_attrs: Optional[Callable] = None):
        """
        This is a class method to register a foreign type to be serialized.
        It accepts the following parameters:
        :param type_: type - a class of object to be serialized eg. datetime.datetime
        :param serializable_init_params: callable (optional).
            When called with a serialized instance,
            it is expected to deliver valid parameters for instantiation of the registerd type.
            The parameters must be json serializable or further foreign type registration must be provided
            If this is left None (default),
                instantiation of type will be performed without parameters on deserialization.
        :param serialization_instance_attrs: callable (optional):
            When called with a serialized instance,
            it is expected to deliver a dict of attributes that will be ascribed to the instance after instantiation.
            If this is left None (default), no attributes will be ascribed after instantiation.

        the registered methods (functions) will be used for ptbserialization
        """
        if not isinstance(type_, type):
            raise TypeError(f'argument type_ must be type.')
        if serializable_init_params and not callable(serializable_init_params):
            raise TypeError(f'serializable_init_params must be callable. See __doc__.')
        if serialization_instance_attrs and not callable(serialization_instance_attrs):
            raise TypeError(f'serializable_init_params must be callable. See __doc__.')

        PtbSerializable.FOREIGN_SERIALIZABLE_REGISTRY.update(
            {
                type_.__name__: {TYPE_ANNOTATION_KEY: type_,
                                 INIT_ANNOTATION_KEY: serializable_init_params,
                                 ATTRS_ANNOTATION_KEY: serialization_instance_attrs}
            }
        )

    @abstractmethod
    def serialization_init_params(self) -> Any:
        """
        The return of this method is supposed to be instantiation parameters ot the serialized object.
        These will be serialized as json objects: array and object (list and dict)
        together with the class of the object.
        During deserialization (decoding) of the instance object of the class,
        these parameters will be passed to the class __init__ so the serialized object is reinstantiated.

        To achieve unpacking behaviour at reinstantiation,
        like in *args or **kwargs at the method call,
        return a dictionary with keys '*' and or '**'
        like in:
        {'*' = ('John', 'Dowland'), '**': {'profession':'musician', 'age':34}}

        this will work for a class with instantiation signature:
        __init__(name, surname, *, profession=None, age=None, **kwargs)
        etc...

        ATTENTION:
            If instance is to be serialized without instantiation arguments
            {"**":{}}  or {"*":[]} must be returned.
            This is because serialization_init_params is an obligatory method in hisrobot serializable classes
            and None is allowed to be used as legal instantiation parameter ,
            so if None is returned by this method,
            it will be serialized, and treated as instantiation parameter for decoded class, at reinstantiation
            (after deserialization).

        """
        ...

    @abstractmethod
    def serialization_instance_attrs(self) -> Optional[dict]:
        """
        This method must return a dictionary of instance attributes or boolean False (like: None, 0 , {}, etc..)
        That will be added to deserializaed instance after reinstantiation
        If bool value of return is False - adding attributes after instantiation will be skipped.
        """
        ...


# registering datetime
PtbSerializable.register_foreign(datetime, serializable_init_params=lambda x: {'*': x.timetuple()[:6]})


def ptbs_preprocess(obj):
    if isinstance(obj, PtbSerializable):
        return {TYPE_ANNOTATION_KEY: obj.__class__.__name__,
                INIT_ANNOTATION_KEY: ptbs_preprocess(obj.serialization_init_params()),
                ATTRS_ANNOTATION_KEY: ptbs_preprocess(obj.serialization_instance_attrs())}
    elif PtbSerializable.FOREIGN_SERIALIZABLE_REGISTRY.get(type(obj).__name__):
        return preprocess_foreign(obj)
    elif isinstance(obj, Mapping):
        return {k: ptbs_preprocess(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [ptbs_preprocess(member) for member in obj]
    else:
        return obj


def preprocess_foreign(obj) -> dict:
    registered = PtbSerializable.FOREIGN_SERIALIZABLE_REGISTRY[type(obj).__name__]

    if init_factory := registered.get(INIT_ANNOTATION_KEY):
        inits = init_factory(obj)
    else:
        inits = None

    if attrs_factory := registered.get(ATTRS_ANNOTATION_KEY):
        attrs = attrs_factory(obj)
        if not isinstance(attrs, dict):
            raise TypeError(f'Invalid serialization_instance_attrs registered with PtbSerializable.register_foreign.'
                            f'expected type dict in return. Got {type(attrs)}')
        for key, val in attrs.items():
            attrs[key] = ptbs_preprocess(val)
    else:
        attrs = None

    return {TYPE_ANNOTATION_KEY: registered[TYPE_ANNOTATION_KEY].__name__,
            INIT_ANNOTATION_KEY: inits,
            ATTRS_ANNOTATION_KEY: attrs}


class PtbSerialisationEncoder(json.JSONEncoder):

    def __init__(self, *args, **kawrgs):
        super().__init__(*args, **kawrgs)

    def default(self, obj: Any):
        if isinstance(obj, PtbSerializable):
            return ptbs_preprocess(obj)
        super().default(obj)

    def preprocess_ptb_serializable(self, obj) -> dict:
        return {TYPE_ANNOTATION_KEY: obj.__class__.__name__,
                INIT_ANNOTATION_KEY: self.preprocess_ptb_serializable(obj.serialization_init_params()),
                ATTRS_ANNOTATION_KEY: self.preprocess_ptb_serializable(obj.serialization_instance_attrs())}


class PtbSerialisationDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode(self, obj: str):
        obj = super().decode(obj)
        obj = self.decode_dispatch(obj)
        return obj

    def decode_dispatch(self, obj):
        if isinstance(obj, list):
            return [self.decode_dispatch(member) for member in obj]
        elif isinstance(obj, Mapping):
            if TYPE_ANNOTATION_KEY in obj:
                return self.decode_generic(obj)
            return {k: self.decode_dispatch(v) for k, v in obj.items()}
        else:
            return obj

    def decode_generic(self, obj):
        if not isinstance(obj, Mapping):
            raise TypeError('Expected type Mapping')

        factory = self.get_factory(obj)
        if not factory:
            return obj

        instance = self.instantiate_serialized(factory, obj[INIT_ANNOTATION_KEY])

        postinit_attrs = obj.get(ATTRS_ANNOTATION_KEY, None)
        if postinit_attrs and isinstance(postinit_attrs, Mapping):
            instance = self.asign_attrs(instance, postinit_attrs)

        try:
            instance._was_serialized = True
        except AttributeError:
            pass  # some classes dont allow atribute ascribing

        return instance

    @staticmethod
    def get_factory(obj: Mapping):
        factory = PtbSerializable.SERIALIZABLE_REGISTRY.get(obj[TYPE_ANNOTATION_KEY], None)
        if not factory:
            registerd = PtbSerializable.FOREIGN_SERIALIZABLE_REGISTRY.get(obj[TYPE_ANNOTATION_KEY], None)
            if not registerd:
                factory = None
            else:
                factory = registerd[TYPE_ANNOTATION_KEY]
        if not factory:
            raise ValueError(f'PtbSerialisationDecoder attempted to reinstantiate {obj[TYPE_ANNOTATION_KEY]},'
                             f' but could not find any valid record.')
        return factory

    def instantiate_serialized(self, factory, args):
        args = self.decode_dispatch(args)
        if args:
            if isinstance(args, Mapping):
                unpack_keys = ("*", "**")
                if any(k in args.keys() for k in unpack_keys):
                    unpack_args = args.get("*", tuple())
                    unpack_kwargs = args.get("**", dict())
                    other_kwargs = {k: v for k, v in args.items() if k not in unpack_keys}
                    unpack_kwargs.update(other_kwargs)
                    return factory(*unpack_args, **unpack_kwargs)
                else:
                    return factory(args)
            return factory(args)
        else:
            return factory()

    @staticmethod
    def asign_attrs(instance, postinit_attrs: Mapping):
        for attr, attr_value in postinit_attrs.items():
            instance.__setattr__(attr, attr_value)
        return instance


def serialize(obj):
    """
    this is extension of the json.dumps() with emploed PtbSerialisationEncoder
    It serializes all classes registered by PtbSerializable
    """
    return json.dumps(ptbs_preprocess(obj), cls=PtbSerialisationEncoder)


def deserialize(obj):
    """
    this is an extension of the json.loads() with employed PtbSerialisationDecoder
    It deserializes all classes registered by PtbSerializable
    """
    return json.loads(obj, cls=PtbSerialisationDecoder)

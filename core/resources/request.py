import os
from itertools import chain
from future.utils import with_metaclass, iteritems

from core.resources.Option import Option


class RequestOptionsAggregator(type):

    def __new__(cls, name, bases, attrs):
        try:
            base_module_attributes = chain([base.module_attributes for base in bases])
        except AttributeError:
            attrs["module_attributes"] = {}
        else:
            attrs["module_attributes"] = {k: v for d in base_module_attributes for k, v in iteritems(d)}

        for key, value in iteritems(attrs.copy()):
            if isinstance(value, Option):
                value.label = key
                attrs["module_attributes"].update({key: [value.display_value, value.advanced]})
            elif key == "__info__":
                attrs["_{}{}".format(name, key)] = value
                del attrs[key]
            elif key in attrs["module_attributes"]:
                del attrs["module_attributes"][key]

        return super(RequestOptionsAggregator, cls).__new__(cls, name, bases, attrs)


class BaseRequest(with_metaclass(RequestOptionsAggregator, object)):
    @property
    def options(self):
        return list(self.module_attributes.keys())

    def __str__(self):
        return self.__module__.split('.', 2).pop().replace('.', os.sep)


class Request(BaseRequest):

    def run(self):
        raise NotImplementedError("You have to define your own run method")

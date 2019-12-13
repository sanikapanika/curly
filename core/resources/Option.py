from core.exceptions.exceptions import OptionValidationError


class Option(object):

    def __init__(self, default, advanced=False):
        self.label = None

        try:
            self.advanced = bool(advanced)
        except ValueError:
            raise OptionValidationError("Invalid value. Cannot cast '{}' to bool".format(advanced))

        if default or default == 0:
            self.__set__("", default)
        elif isinstance(self, OptList):
            self.value = {}
            self.display_value = {}
        else:
            self.display_value = ""
            self.value = ""

    def __get__(self, instance, owner):
        return self.value


class OptPort(Option):
    """ Option Port attribute """

    def __set__(self, instance, value):
        try:
            value = int(value)

            if 0 < value <= 65535:  # max port number is 65535
                self.display_value = str(value)
                self.value = value
            else:
                raise OptionValidationError("Invalid option. Port value should be between 0 and 65536.")
        except ValueError:
            raise OptionValidationError("Invalid option. Cannot cast '{}' to integer.".format(value))


class OptBool(Option):
    """ Option Bool attribute """

    def __init__(self, default, advanced=False):

        if default:
            self.display_value = "true"
        else:
            self.display_value = "false"

        self.value = default

        try:
            self.advanced = bool(advanced)
        except ValueError:
            raise OptionValidationError("Invalid value. Cannot cast '{}' to boolean.".format(advanced))

    def __set__(self, instance, value):
        if value == "true":
            self.value = True
            self.display_value = value
        elif value == "false":
            self.value = False
            self.display_value = value
        else:
            raise OptionValidationError("Invalid value. It should be true or false.")


class OptInteger(Option):
    """ Option Integer attribute """

    def __set__(self, instance, value):
        try:
            self.display_value = str(value)
            self.value = int(value)
        except ValueError:
            try:
                self.value = int(value, 16)
            except ValueError:
                raise OptionValidationError("Invalid option. Cannot cast '{}' to integer.".format(value))


class OptFloat(Option):
    """ Option Float attribute """

    def __set__(self, instance, value):
        try:
            self.display_value = str(value)
            self.value = float(value)
        except ValueError:
            raise OptionValidationError("Invalid option. Cannot cast '{}' to float.".format(value))


class OptString(Option):
    """ Option String attribute """

    def __set__(self, instance, value):
        try:
            self.value = self.display_value = str(value)
        except ValueError:
            raise OptionValidationError("Invalid option. Cannot cast '{}' to string.".format(value))


class OptList(Option):

    def __add__(self, other):
        try:
            self.value.extend(other)
            self.display_value.extend(other)
        except ValueError:
            raise OptionValidationError("Invalid option. Cannot append '{}' to array".format(other))

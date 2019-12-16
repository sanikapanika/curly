import atexit
import itertools
import os
import pkgutil
import readline
import sys
import traceback
from builtins import getattr, AttributeError, dict, super, dir, len, IndexError
from collections import Counter
import getopt

from core.exceptions.exceptions import CurlFrameworkException
from core.resources.utils import (
    index_modules,
    index_templates,
    pythonize_path,
    humanize_path,
    import_template,
    module_required,
    MODULES_DIR,
    stop_after)
from core.resources.printer import (
    print_info,
    print_success,
    print_error,
    print_status,
    print_table,
    pprint_dict_in_order,
    PrinterThread,
    printer_queue
)


def is_libedit():
    return "libedit" in readline.__doc__


class BaseInterpreter:
    history_file = os.path.expanduser("~/.history")
    history_length = 100
    global_help = ""

    def __init__(self):
        self.setup()
        self.banner = ""

    def setup(self):
        if not os.path.exists(self.history_file):
            with open(self.history_file, "a+") as history:
                if is_libedit():
                    history.write("History_V2_\n\n")

        readline.read_history_file(self.history_file)
        readline.set_history_length(self.history_length)
        atexit.register(readline.write_history_file, self.history_file)

        readline.parse_and_bind("set enable-keypad on")

        readline.set_completer(self.complete)

    def parse_line(self, line):
        kwargs = dict()
        command, _, arg = line.strip().partition(" ")
        args = arg.strip().split()
        for word in args:
            if "=" in word:
                (key, val) = word.split('=', 1)
                kwargs[key.lower()] = val
                arg = arg.replace(word, '')
        return command, ' '.join(arg.split()), kwargs

    @property
    def prompt(self):
        return "cfwconsole>>>"

    def get_command_handler(self, command):
        try:
            command_handler = getattr(self, "command_{}".format(command))
        except AttributeError:
            raise CurlFrameworkException("Unknown command: {}".format(command))

        return command_handler

    def start(self):
        print_info(self.banner)
        printer_queue.join()
        while True:
            try:
                command, args, kwargs = self.parse_line(input(self.prompt))
                if not command:
                    continue
                command_handler = self.get_command_handler(command)
                command_handler(args, **kwargs)
            except CurlFrameworkException as err:
                print_error(err)
            except (EOFError, KeyboardInterrupt, SystemExit):
                print_info()
                print_error("Curly stopped")
                break
            finally:
                printer_queue.join()

    def complete(self, text, state):
        if state == 0:
            original_line = readline.get_line_buffer()
            line = original_line.lstrip()
            stripped = len(original_line) - len(line)
            start_index = readline.get_begidx() - stripped
            end_index = readline.get_endidx() - stripped

            if start_index > 0:
                cmd, args, _ = self.parse_line(line)
                if cmd == "":
                    complete_function = self.default_completer
                else:
                    try:
                        complete_function = getattr(self, "complete_" + cmd)
                    except AttributeError:
                        complete_function = self.default_completer
            else:
                complete_function = self.raw_command_completer

            self.completion_matches = complete_function(text, line, start_index, end_index)

        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def commands(self, *ignored):
        return [command.rsplit("_").pop() for command in dir(self) if command.startswith("command_")]

    def raw_command_completer(self, text, line, start_index, end_index):
        return [command for command in self.suggested_commands() if command.startswith(text)]

    def default_completer(self, *ignored):
        return []

    def suggested_commands(self):
        return self.commands()


class CurlyInterpreter(BaseInterpreter):
    history_file = os.path.expanduser("~/.cfw_history")
    global_help = """
    help                             Print this help menu
    use <template>                   Use template
    exec <shell cmd> <args>          Execute a command in a shell
    search <search term>             Search for template
    exit                             Exit CurlFramework"""

    module_help = """Template commands:
    execute                             Execute the selected template with given options
    back                                De-select current template
    set <option name> <option value>    Set an option for the selected template
    setg <option name> <option value>   Set an option for all the templates
    unsetg <option name>                Unset an option that was set globally
    show [info|options]                 Print information or options for a template
    check                               Check if given host is reachable"""

    def __init__(self):
        super(CurlyInterpreter, self).__init__()
        PrinterThread().start()

        self.current_module = None
        self.raw_prompt_template = None
        self.module_prompt_template = None
        self.prompt_hostname = "cfw"
        self.show_sub_commands = ("info", "options", "advanced", "all", "templates", "modules")
        self.search_sub_commands = ("type", "payload")

        self.global_commands = sorted(["use ", "exec ", "help", "exit", "show ", "search "])
        self.module_commands = ["execute", "back", "set ", "setg ", "check"]
        self.module_commands.extend(self.global_commands)
        self.module_commands.sort()

        self.modules = index_modules()
        self.modules_count = Counter()
        self.modules_count.update([module.split('.')[0] for module in self.modules])
        self.saved_templates = index_templates()
        self.saved_templates_count = Counter()
        self.saved_templates_count.update([template.split('.')[0] for template in self.saved_templates])
        self.main_modules_dirs = [module for module in os.listdir(MODULES_DIR) if not module.startswith("__")]

        self.__parse_prompt()
        self.banner = """
_________              .__         
\_   ___ \ __ _________|  | ___.__.
/    \  \/|  |  \_  __ \  |<   |  |
\     \___|  |  /|  | \/  |_\___  |
 \______  /____/ |__|  |____/ ____|
        \/                  \/     
        
        Curl framework || By AjferSanjo
        
 Codename: Curly
 Version: 0.1.0
 
 Modules: {module_count} Saved Post Templates: {saved_templates} 
""".format(module_count=self.modules_count["modules"],
           saved_templates=self.saved_templates_count["post"])

    def __parse_prompt(self):
        raw_prompt_default_template = "\001\033[4m\002{host}\001\033[0m\002 > "
        raw_prompt_template = os.getenv("CFW_RAW_PROMPT", raw_prompt_default_template).replace('\\033', '\033')
        self.raw_prompt_template = raw_prompt_template if '{host}' in raw_prompt_template else raw_prompt_default_template

        module_prompt_default_template = "\001\033[4m\002{host}\001\033[0m\002 (\001\033[91m\002{module}\001\033[0m\002) > "
        module_prompt_template = os.getenv("CFW_TEMPLATE_PROMPT", module_prompt_default_template).replace('\\033',
                                                                                                          '\033')
        self.module_prompt_template = module_prompt_template if all(
            map(lambda x: x in module_prompt_template, ['{host}', "{module}"])) else module_prompt_default_template

    def __handle_if_noninteractive(self, argv):
        self.nonInteractive(argv)

    def nonInteractive(self, argv):
        module = ""
        set_opts = []

        try:
            opts, args = getopt.getopt(argv[1:], "hm:s", ["help=", "module=", "set="])
        except getopt.GetoptError:
            print_info("{} -m <module> -s \"<option> <value>\"".format(argv[0]))
            printer_queue.join()
            return

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print_info("{} -m <module> -s \"<option> <value>\"".format(argv[0]))
                printer_queue.join()
                return
            elif opt in ("-m", "--module"):
                module = arg
            elif opt in ("-s", "--set"):
                set_opts.append(arg)

        if not len(module):
            print_error('A module is required when running non-interactively')
            printer_queue.join()
            return

        self.command_use(module)

        for opt in set_opts:
            self.command_set(opt)

        self.command_run()

        printer_queue.join()

        return

    @property
    def module_metadata(self):
        return getattr(self.current_module, "_{}__info__".format(self.current_module.__class__.__name__))

    @property
    def prompt(self):
        if self.current_module:
            try:
                return self.module_prompt_template.format(host=self.prompt_hostname,
                                                          module=self.module_metadata['name'])
            except (AttributeError, KeyError):
                return self.module_prompt_template.format(host=self.prompt_hostname, module="UnnamedModule")
        else:
            return self.raw_prompt_template.format(host=self.prompt_hostname)

    def available_modules_completion(self, text):
        text = pythonize_path(text)
        all_possible_matches = filter(lambda x: x.startswith(text), self.modules)
        matches = set()
        for match in all_possible_matches:
            head, sep, tail = match[len(text):].partition('.')
            if not tail:
                sep = ""
            matches.add("".join((text, head, sep)))
        return list(map(humanize_path, matches))

    def suggested_commands(self):
        if self.current_module and GLOBAL_OPTS:
            return sorted(itertools.chain(self.module_commands, ("unsetg",)))
        elif self.current_module:
            return self.module_commands
        else:
            return self.global_commands

    def command_back(self, *args, **kwargs):
        self.current_module = None

    def command_use(self, module_path, *args, **kwargs):
        module_path = pythonize_path(module_path)
        module_path = ".".join(("core", "modules", module_path))
        try:
            self.current_module = import_template(module_path)()
        except CurlFrameworkException as err:
            print_error(str(err))

    @stop_after(2)
    def complete_use(self, text, *args, **kwargs):
        if text:
            return self.available_modules_completion(text)
        else:
            return self.main_modules_dirs

    @module_required
    def command_run(self, *args, **kwargs):
        print_status("Running module {}...".format(self.current_module))
        try:
            self.current_module.run()
        except KeyboardInterrupt:
            print_info()
            print_error("Operation cancelled by user")
        except Exception:
            print_error(traceback.format_exc(sys.exc_info()))

    @module_required
    def command_save(self, *args, **kwargs):
        # try:
        if args[0] is not None and args[0] is not '':
            self.current_module.save(args=args)
        else:
            print_error("Template name must be specified")
        # except Exception:
        # print_error("Error saving template")

    @module_required
    def command_load(self, *args, **kwargs):
        if args[0] is not None and args[0] is not '':
            self.current_module.load(args=args)
        else:
            print_error("Template name must be specified")

    @module_required
    def command_set(self, *args, **kwargs):
        key, _, value = args[0].partition(" ")
        if key in self.current_module.options:
            if isinstance(self.current_module.module_attributes[key][0], dict):
                print_error("Cannot set value for field {}, use add command instead".format(key))
                return
            setattr(self.current_module, key, value)
            self.current_module.module_attributes[key][0] = value

            if kwargs.get("glob", False):
                GLOBAL_OPTS[key] = value
            print_success("{} => {}".format(key, value))
        else:
            print_error("You can't set option: '{}'.\n"
                        "Available options: {}".format(key, self.current_module.options))

    @stop_after(2)
    def complete_set(self, text, *args, **kwargs):
        if text:
            return [" ".join((attr, "")) for attr in self.current_module.options if attr.startswith(text)]

    @module_required
    def command_add(self, *args, **kwargs):
        key, _, value = args[0].partition(" ")
        if key in self.current_module.options:
            if 'value' in kwargs:
                templist = getattr(self.current_module, key)
                templist[value] = kwargs.get('value')
                setattr(self.current_module, key, templist)
                self.current_module.module_attributes[key][0][value] = kwargs.get('value')

                print_success("{} => {}: {}".format(key, value, kwargs.get('value')))

    @module_required
    def command_delete(self, *args, **kwargs):
        key, _, value = args[0].partition(" ")
        if key in self.current_module.options:
            templist = getattr(self.current_module, key)
            if not isinstance(templist, dict):
                print_error("Cannot delete attribute {}, only dictionary entries can be deleted, overwrite it instead"
                            .format(key))
                return
            del templist[value]
            setattr(self.current_module, key, templist)
            del self.current_module.module_attributes[key][0][value]

            print_error("{} => {}".format(key, value))

    @module_required
    def command_setg(self, *args, **kwargs):
        kwargs['glob'] = True
        self.command_set(*args, **kwargs)

    @stop_after(2)
    def complete_setg(self, text, *args, **kwargs):
        return self.complete_set(text, *args, **kwargs)

    @module_required
    def command_unsetg(self, *args, **kwargs):
        key, _, value = args[0].partition(' ')
        try:
            del GLOBAL_OPTS[key]
        except KeyError:
            print_error("Cannot unset global option '{}'.\n"
                        "Available global options: {}".format(key, list(GLOBAL_OPTS.keys())))
        else:
            print_success({key: value})

    @stop_after(2)
    def complete_unsetg(self, text, *args, **kwargs):
        if text:
            return [' '.join((attr, "")) for attr in GLOBAL_OPTS.keys() if attr.startswith(text)]
        else:
            return list(GLOBAL_OPTS.keys())

    @module_required
    def get_opts(self, *args):
        for opt_key in args:
            try:
                # opt_description = self.current_module.module_attributes[opt_key][1]
                opt_display_value = self.current_module.module_attributes[opt_key][0]
                if self.current_module.module_attributes[opt_key][1]:
                    continue
            except (KeyError, IndexError, AttributeError):
                pass
            else:
                yield opt_key, opt_display_value

    @module_required
    def get_opts_adv(self, *args):
        for opt_key in args:
            try:
                opt_description = self.current_module.template_attributes[opt_key][1]
                opt_display_value = self.current_module.template_attributes[opt_key][0]
            except (KeyError, AttributeError):
                pass
            else:
                yield opt_key, opt_display_value, opt_description

    @module_required
    def _show_info(self, *args, **kwargs):
        pprint_dict_in_order(
            self.module_metadata,
            ("name", "description", "devices", "authors", "references"),
        )
        print_info()

    @module_required
    def _show_options(self, *args, **kwargs):
        # TODO: WILL NEED UPDATE
        # target_names = ["target", "port", "ssl", "rhost", "rport", "lhost", "lport"]
        target_opts = [opt for opt in self.current_module.options]
        module_opts = [opt for opt in self.current_module.options]
        headers = ("Name", "Current settings")

        print_info("\nTarget options:")
        print_table(headers, *self.get_opts(*target_opts))

        if module_opts:
            print_info("\Module options:")
            print_table(headers, *self.get_opts(*module_opts))

        print_info()

    def _show_advanced(self, *args, **kwargs):
        target_names = ["target", "port", "ssl", "rhsot", "rport", "lhost", "lport"]
        target_opts = [opt for opt in self.current_module.options if opt in target_names]
        module_opts = [opt for opt in self.current_module.options if opt not in target_opts]
        headers = ("Name", "Current settings", "Description")

        print_info("\nTarget options:")
        print_table(headers, *self.get_opts(*target_opts))

        if module_opts:
            print_info("\nModule options:")
            print_table(headers, *self.get_opts_adv(*module_opts))

        print_info()

    def _show_modules(self, root=''):
        for module in [module for module in self.modules if module.startswith(root)]:
            print_info(module.replace('.', os.sep))

    def _show_all(self, *args, **kwargs):
        self._show_modules()

    def _show_templates(self, *args, **kwargs):
        if 'module' in kwargs.keys():
            for template in [template for template in self.saved_templates if template.startswith(kwargs.get('module'))]:
                print_info(template.replace('.', os.sep))
        else:
            print_error("You must specify for which module. Available: {}".format(self.modules))

    def command_show(self, *args, **kwargs):
        sub_command = args[0]
        try:
            getattr(self, "_show_{}".format(sub_command))(*args, **kwargs)
        except AttributeError:
            print_error("Unknown 'show' subcommand '{}'. "
                        "Possible choices: {}".format(sub_command, self.show_sub_commands))

    @stop_after(2)
    def complete_show(self, text, *args, **kwargs):
        if text:
            return [command for command in self.show_sub_commands if command.startswith(text)]
        else:
            return self.show_sub_commands

    def command_help(self, *args, **kwargs):
        print_info(self.global_help)
        if self.current_module:
            print_info("\n", self.module_help)

    def command_search(self, *args, **kwargs):
        mod_type = ''
        mod_detail = ''
        mod_vendor = ''
        existing_modules = [name for _, name, _ in pkgutil.iter_modules([MODULES_DIR])]
        # TODO: Probably gonna need refractoring
        devices = [name for _, name, _ in pkgutil.iter_modules([os.path.join(MODULES_DIR, 'exploits')])]
        payloads = [name for _, name, _ in pkgutil.iter_modules([os.path.join(MODULES_DIR, 'payloads')])]

        try:
            keyword = args[0].strip("'\"").lower()
        except IndexError:
            keyword = ''

        if not (len(keyword) or len(kwargs.keys())):
            print_error("Please specify at least one search keyword")
            print_error("You can specify options, eg 'search type=exploits etc'")

        for (key, value) in kwargs.items():
            if key == 'type':
                if value not in existing_modules:
                    print_error("Unknown module type")
                    return
                mod_type = "{}.".format(value)
            elif key in ['device', 'language', 'payload']:
                if key == 'device' and (value not in devices):
                    print_error("Unknown exploit type")
                    return
                elif key == 'payload' and (value not in payloads):
                    print_error("Unknown payload type")
                    return
                mod_detail = ".{}.".format(value)
            elif key == 'vendor':
                mod_vendor = ".{}.".format(value)

        for module in self.modules:
            if mod_type not in str(module):
                continue
            if mod_detail not in str(module):
                continue
            if mod_vendor not in str(module):
                continue
            if not all(word in str(module) for word in keyword.split()):
                continue

            found = humanize_path(module)

            if len(keyword):
                for word in keyword.split():
                    found = found.replace(word, "\033[31m{}\033[0m".format(word))

            print_info(found)

    def complete_search(self, text, *args, **kwargs):
        if text:
            return [command for command in self.search_sub_commands if command.startswith(text)]
        else:
            return self.search_sub_commands

    def command_exit(self, *args, **kwargs):
        raise EOFError

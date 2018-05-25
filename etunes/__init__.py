import shlex
import traceback
import yaml

class Error(Exception):
    """
    Error that should be printed to stderr. The messages are a list of
    either messages, which are printed as is, or 2-tuples, where the
    first element is a message type and the second element is the
    message.
    """
    def __init__(self, messages):
        self.messages = messages

def error(message):
    """
    Error that prints the given message, prefixed by "etunes: ".
    """
    return Error([("etunes", message)])

def fancy_error(message):
    """
    Error that prints the given message as is.
    """
    return Error([message])

def with_usage(e, usage):
    """
    Wrap an error with a message prefixed by "usage: ". If e is an
    Error, its preexisting messages are preserved and the usage
    message is printed last. Otherwise, the error is converted to a
    string and that is printed first.
    """
    if isinstance(e, Error):
        return Error(e.messages + [("usage", usage)])
    else:
        return Error([str(e), ("usage", usage)])

def with_extra(e, *hints):
    """
    Wrap an error with extra data. If e is not an Error, it is first
    turned into one by using str(e) as the message. Then, the hints
    are added to the messages list.
    """
    if isinstance(e, Error):
        return Error(e.messages + list(hints))
    else:
        return Error([str(e)] + list(hints))

def remove_newline(s):
    """
    Remove a trailing newline from the string, if one exists.
    """
    if s.endswith("\n"):
        return s[:-1]
    return s

def locate_dominating_file(io, filename, directory=None):
    """
    Find a file or directory with the given name, either in the given
    (defaults to current) directory or a parent. Return the full path,
    or None if the root of the filesystem is reached before finding a
    matching file.
    """
    if directory is None:
        directory = io.getcwd()
    last, directory = None, io.abspath(directory)
    while directory != last:
        path = io.join(directory, filename)
        if io.exists(path):
            return path
        last, directory = directory, io.dirname(directory)
    return None

def file_to_yaml(io, filename):
    """
    Read a YAML file and return the contents as a Python object. If
    reading or parsing fails, throw an error.
    """
    try:
        with io.open(filename, "r") as f:
            return yaml.load(f)
    except FileNotFoundError as e:
        raise error("could not read YAML file {}: {}"
                    .format(repr(filename), str(e)))
    except yaml.YAMLError as e:
        raise error("malformed YAML file {}: {}"
                    .format(repr(filename), str(e)))

def yaml_to_file(io, obj, filename):
    """
    Write a Python object to a YAML file. If writing fails, throw an
    error.
    """
    try:
        with io.open(filename, "w") as f:
            yaml.dump(obj, f,
                      # Actually render YAML instead of just JSON.
                      default_flow_style=False,
                      # Quote strings.
                      default_style='|')
    except FileNotFoundError as e:
        raise error("could not write to YAML file {}: {}"
                    .format(repr(filename), str(e)))

def git_not_installed_error(e):
    """
    Given an error object, wrap it so that a hint about Git needing to
    be installed is also displayed.
    """
    return with_extra(
        error("unexpected failure while running 'git': {}".format(str(e))),
        ("note", "Git must be installed in order to use eTunes"))

def git_config_value(io, key):
    """
    Return the value for the given Git configuration key, as a
    string. If there is no value, throw an error and suggest to the
    user how they can set the key.
    """
    try:
        result = io.run(["git", "config", "--get", key],
                        stdout=io.PIPE)
        if result.returncode != 0:
            raise with_extra(
                error("Git configuration value {} is not set"
                      .format(repr(key))),
                ("hint",
                 "to set, run 'git config {} <value>'"
                 .format(shlex.quote(key))))
        return remove_newline(result.stdout.decode())
    except OSError as e:
        raise git_not_installed_error(e)

# The name of the file that eTunes searches for with library metadata,
# and the filename used by 'etunes init'.
DEFAULT_LIBRARY_FILENAME = "etunes.yml"

# The default library metadata. The keys and values are strings,
# except that if a value is a function then it is converted to a
# string by calling it with an IO object.
#
# This is used by 'etunes init', and also to infer missing metadata
# values.
DEFAULT_LIBRARY = {
    "deduplication-threshold": "0.75",
    "git-email": lambda io: git_config_value(io, "user.email"),
    "git-name": lambda io: git_config_value(io, "user.name"),
    "media-path": "media/{album-artist}/{album}/{title}.{ext}",
    "metadata-path": "metadata/{album-artist}/{album}.yml",
}

# General command syntax for the top-level CLI of eTunes.
USAGE = """[--library=<library-file>] <subcommand>"""

# List of normal subcommands supported by eTunes.
SUBCOMMANDS = ["init"]

# Subcommand usage syntax.
SUBCOMMAND_USAGE = {
    "init": "<path>",
}

assert sorted(SUBCOMMANDS) == sorted(SUBCOMMAND_USAGE)

def subcommand_usage(subcommand):
    """
    Return a string demonstrating usage of the given subcommand. For
    example,

    >>> subcommand_usage('init')
    'init <path>'
    """
    return "{} {}".format(subcommand, SUBCOMMAND_USAGE[subcommand])

def usage(subcommand=None):
    """
    Return a string demonstrating full usage of the given subcommand,
    or etunes as a whole. The string starts with 'etunes'.
    """
    if subcommand is not None:
        return "etunes {}".format(subcommand_usage(subcommand))
    else:
        lines = ["    {}".format(subcommand_usage(subcommand))
                 for subcommand in SUBCOMMANDS]
        return "etunes {}\n\nSubcommands:\n{}".format(USAGE, "\n".join(lines))

def get_option(io, options, key, filename):
    """
    Return the value of a library metadata option. options is the map
    containing library metadata; filename is only used in error
    messages.

    This may raise an error if the option is not set and getting the
    default value requires performing some actions that can fail.
    """
    val = options.get(key, DEFAULT_LIBRARY[key])
    if callable(val):
        try:
            return val(io)
        except Error as e:
            raise with_extra(
                e,
                ("note",
                 "error occurred while generating default value for option {}"
                 .format(repr(key))),
                ("hint",
                 "set option directly in {}".format(repr(filename))))
    else:
        return val

def decode_option(io, options, key, filename, decoder):
    """
    Helper function for the decode_options function. It looks up a
    value in the library metadata, runs a decoder function on it, and
    puts the result back into the metadata in place of the original
    value.
    """
    val = get_option(io, options, key, filename)
    options[key] = decoder(val, key)

def decode_options(io, options, filename):
    """
    Given the library metadata option, convert it to the internal
    representation and return a new map. The filename is used only in
    error messages.
    """
    if not isinstance(options, dict):
        raise error("library file {} does not contain map at top level"
                    .format(repr(filename)))
    for key, val in options.items():
        if not isinstance(key, str):
            raise error("library file {} contains non-string key: {}"
                        .format(repr(filename), repr(key)))
        if not isinstance(val, str):
            raise error("library file {} contains non-string value: {}"
                        .format(repr(filename), repr(val)))
    def decode_float(val, key):
        try:
            return float(val)
        except ValueError:
            raise error(("library file {} contains malformed "
                         "floating-point value for key {}: {}")
                        .format(repr(filename), repr(key), repr(val)))
    decode_option(
        io, options, "deduplication-threshold", filename, decode_float)
    return options

def task_init(io, path=None):
    """
    Initialize a new eTunes library metadata file. The path may be
    either a file (to put the metadata in) or a directory (where
    DEFAULT_LIBRARY_FILENAME) is then used to get the full path. If
    omitted, the current directory is used.
    """
    if path is None:
        path = io.getcwd()
    if io.isdir(path):
        path = io.join(path, DEFAULT_LIBRARY_FILENAME)
    if io.exists(path) or io.islink(path):
        raise error("cannot create library file, already exists: {}"
                    .format(repr(path)))
    options = {}
    for key, val in DEFAULT_LIBRARY.items():
        if callable(val):
            options[key] = val(io)
        else:
            options[key] = val
    yaml_to_file(io, options, path)

def handle_args(io, args):
    """
    Parse command-line arguments and take the appropriate action.
    """
    literal = False
    library = None
    subcommand = None
    config = {}
    while args:
        arg = args[0]
        if arg.startswith("-") and not literal:
            if arg == "--":
                literal = True
            elif arg.startswith("--library="):
                library = arg[len("--library="):]
                args = args[1:]
            elif arg == "--library":
                if len(args) >= 2:
                    library = args[1]
                    args.pop(0)
                else:
                    raise with_usage(
                        error("missing argument for flag '--library'"),
                        usage())
            else:
                raise with_usage(
                    error("unrecognized flag: {}".format(repr(arg))),
                    usage())
        elif subcommand is None:
            if arg == "init":
                subcommand = "init"
            else:
                raise with_usage(
                    error("unrecognized subcommand: {}".format(repr(arg))),
                    usage())
        elif subcommand == "init":
            if "path" not in config:
                config["path"] = arg
            else:
                raise with_usage(
                    error("unexpected argument: {}".format(repr(arg))),
                    usage("init"))
        args.pop(0)
    if subcommand is None:
        raise with_usage(error("no subcommand given"), usage())
    if subcommand == "init":
        task_init(io, path=config.get("path"))
        return
    if library is None:
        library = locate_dominating_file(io, DEFAULT_LIBRARY_FILENAME)
        if library is None:
            raise with_extra(
                error("cannot find file {} in working or parent directories"
                      .format(repr(DEFAULT_LIBRARY_FILENAME))),
                ("hint", "to create, run 'etunes init'"))
    options = file_to_yaml(library)
    options = decode_options(io, options, library)

def main(io, exec_name, args):
    """
    Parse command-line arguments and execute. Any errors that were
    raised are turned into messages on stderr and an exit code is
    returned.
    """
    try:
        handle_args(io, args)
        return 0
    except Error as e:
        lines = []
        for message in e.messages:
            if isinstance(message, str):
                lines.append(message)
            else:
                lines.append("{}: {}".format(*message))
        print("\n".join(lines), file=io.stderr)
    except:
        traceback.print_exc()
    return 1

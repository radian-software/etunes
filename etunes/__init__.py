import shlex
import yaml

class Error(Exception):
    """
    Error that should be printed to stderr, prefixed by the name of
    the executable.
    """
    def __init__(self, message):
        self.message = message

class FancyError(Exception):
    """
    Error that should be printed to stderr as is.
    """
    def __init__(self, message):
        self.message = message

class ErrorWithUsage(Exception):
    """
    Like Error, but additionally includes a usage message.
    """
    def __init__(self, message, usage):
        self.message = message
        self.usage = usage

class ErrorWithDescription(Exception):
    """
    Like Error, but additionally includes an extended description.
    """
    def __init__(self, message, description):
        self.message = message
        self.description = description

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
        raise Error("could not read YAML file {}: {}"
                    .format(repr(filename), str(e)))
    except yaml.YAMLError as e:
        raise Error("malformed YAML file {}: {}"
                    .format(repr(filename), str(e)))

def yaml_to_file(io, obj, filename):
    """
    Write a Python object to a YAML file. If writing fails, throw an
    error.
    """
    try:
        with io.open(filename, "w") as f:
            yaml.dump(obj, f, default_flow_style=False)
    except FileNotFoundError as e:
        raise Error("could not write to YAML file {}: {}"
                    .format(repr(filename), str(e)))

def git_not_installed_error(e):
    """
    Given an error object, wrap it so that a hint about Git needing to
    be installed is also displayed.
    """
    return ErrorWithDescription(
        "unexpected failure while running 'git': {}".format(str(e)),
        "note: Git must be installed in order to use eTunes")

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
            raise ErrorWithDescription(
                "Git configuration value {} is not set".format(repr(key)),
                "hint: to set, run 'git config {} <value>'"
                .format(shlex.quote(key)))
        return remove_newline(result.stdout.decode())
    except OSError as e:
        raise git_not_installed_error(e)

DEFAULT_LIBRARY_FILENAME = "etunes.yml"

DEFAULT_LIBRARY = {
    "deduplication-threshold": "0.75",
    "git-email": lambda io: git_config_value(io, "user.email"),
    "git-name": lambda io: git_config_value(io, "user.name"),
    "media-path": "media/{album-artist}/{album}/{title}.{ext}",
    "metadata-path": "metadata/{album-artist}/{album}.yml",
}

USAGE = """[--library=<library-file>] <subcommand>"""

SUBCOMMANDS = ["init"]

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

def validate_options(options, filename):
    if not isinstance(options, dict):
        raise Error("library file {} does not contain map at top level"
                    .format(repr(filename)))
    for key, val in options.items():
        if not isinstance(key, str):
            raise Error("library file {} contains non-string key: {}"
                        .format(repr(filename), repr(key)))
        if not isinstance(val, str):
            raise Error("library file {} contains non-string value: {}"
                        .format(repr(filename), repr(val)))

def task_init(io, path=None):
    if path is None:
        path = io.getcwd()
    if io.isdir(path):
        path = io.join(path, DEFAULT_LIBRARY_FILENAME)
    if io.exists(path) or io.islink(path):
        raise Error("cannot create library file, already exists: {}"
                    .format(repr(path)))
    options = {}
    for key, val in DEFAULT_LIBRARY.items():
        if callable(val):
            options[key] = val(io)
        else:
            options[key] = val
    yaml_to_file(io, options, path)

def handle_args(io, args):
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
                    raise ErrorWithUsage(
                        "missing argument for flag '--library'", usage())
            else:
                raise ErrorWithUsage(
                    "unrecognized flag: {}".format(repr(arg)), usage())
        elif subcommand is None:
            if arg == "init":
                subcommand = "init"
            else:
                raise ErrorWithUsage(
                    "unrecognized subcommand: {}".format(repr(arg)), usage())
        elif subcommand == "init":
            if "path" not in config:
                config["path"] = arg
            else:
                raise ErrorWithUsage(
                    "unexpected argument: {}".format(repr(arg)),
                    usage("init"))
        args.pop(0)
    if subcommand is None:
        raise ErrorWithUsage("no subcommand given", usage())
    if subcommand == "init":
        task_init(io, path=config.get("path"))
        return
    if library is None:
        library = locate_dominating_file(io, DEFAULT_LIBRARY_FILENAME)
        if library is None:
            raise ErrorWithDescription(
                "cannot find file {} in working or parent directories"
                .format(repr(DEFAULT_LIBRARY_FILENAME)),
                "hint: to create, run 'etunes init'")
    options = file_to_yaml(library)
    validate_options(options, library)

def main(io, exec_name, args):
    try:
        handle_args(io, args)
        return 0
    except Error as e:
        print("{}: {}".format(exec_name, e.message), file=io.stderr)
    except FancyError as e:
        print(e.message, file=io.stderr)
    except ErrorWithUsage as e:
        print("{}: {}".format(exec_name, e.message), file=io.stderr)
        print(file=io.stderr)
        print("usage: {}".format(e.usage))
    except ErrorWithDescription as e:
        print("{}: {}".format(exec_name, e.message), file=io.stderr)
        print(file=io.stderr)
        print(e.description)
    return 1

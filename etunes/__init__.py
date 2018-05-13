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
    try:
        with io.open(filename, "w") as f:
            yaml.dump(obj, f, default_flow_style=False)
    except FileNotFoundError as e:
        raise Error("could not write to YAML file {}: {}"
                    .format(repr(filename), str(e)))

DEFAULT_LIBRARY_FILENAME = "etunes.yml"

DEFAULT_LIBRARY = {
    "deduplication-threshold": "0.75",
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
    return "{} {}".format(subcommand, SUBCOMMAND_USAGE[subcommand])

def usage(subcommand=None):
    if subcommand is not None:
        return "etunes {}".format(subcommand_usage(subcommand))
    else:
        lines = ["    {}".format(subcommand_usage(subcommand))
                 for subcommand in SUBCOMMANDS]
        return "etunes {}\n\nSubcommands:\n{}".format(USAGE, "\n".join(lines))

def validate_options(options):
    ...

def task_init(io, path=None):
    if path is None:
        path = io.getcwd()
    if io.isdir(path):
        path = io.join(path, DEFAULT_LIBRARY_FILENAME)
    if io.exists(path) or io.islink(path):
        raise Error("cannot create library file, already exists: {}"
                    .format(repr(path)))
    yaml_to_file(io, DEFAULT_LIBRARY, path)

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
            raise Error("cannot find file {} in working or parent directories"
                        .format(repr(DEFAULT_LIBRARY_FILENAME)))
    options = file_to_yaml(library)
    validate_options(options)

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
    return 1

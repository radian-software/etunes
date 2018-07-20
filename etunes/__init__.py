import shlex

import json
import jsonschema
import psutil
import uuid
import yaml

open = None
print = None

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

def quote_command(args):
    return " ".join(shlex.quote(arg) for arg in args)

def run_and_check(io, args, **kwargs):
    result = io.run(args, **kwargs)
    if result.returncode != 0:
        raise error("command failed: {}".format(quote_command(result.args)))
    return result

def locate_dominating_file(io, filename, directory=None):
    """
    Find a file or directory with the given name, either in the given
    (defaults to current) directory or a parent. Return the full path,
    or None if the root of the filesystem is reached before finding a
    matching file.
    """
    if directory is None:
        directory = io.getcwd()
    last, directory = None, io.realpath(directory)
    while directory != last:
        path = io.join(directory, filename)
        if io.exists(path) or io.islink(path):
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
    error. Writing is guaranteed to be atomic.
    """
    try:
        with io.NamedTemporaryFile() as f:
            yaml.dump(obj, f,
                      # Actually render YAML instead of just JSON.
                      default_flow_style=False,
                      # Quote strings.
                      default_style='|')
            io.rename(f.name, filename)
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
    "media-path": "media/{album-artist}/{album}/{title}.{ext}",
    "metadata-path": "metadata/{album-artist}/{album}.yml",
}

# General command syntax for the top-level CLI of eTunes.
USAGE = """[--library=<library-file>] <subcommand>"""

# List of normal subcommands supported by eTunes.
SUBCOMMANDS = ["init", "query", "help", "version"]

# Subcommand usage syntax.
SUBCOMMAND_USAGE = {
    "init": "<path>",
    "query": "(<json> | @<query-file> | -)",
    "help": None,
    "version": None
}

assert sorted(SUBCOMMANDS) == sorted(SUBCOMMAND_USAGE)

def subcommand_usage(subcommand):
    """
    Return a string demonstrating usage of the given subcommand. For
    example,

    >>> subcommand_usage('init')
    'init <path>'
    """
    desc = SUBCOMMAND_USAGE[subcommand]
    if desc:
        return "{} {}".format(subcommand, desc)
    else:
        return subcommand

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

def get_version():
    return "etunes development version"

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

def validate_library_options(io, options, filename):
    """
    Given the library file data structure, throw an error if it is
    malformed. The filename is used only in error messages.
    """
    if not isinstance(options, dict):
        raise error("library file {} does not contain map at top level"
                    .format(repr(filename)))
    for key, val in options.items():
        if not isinstance(val, str):
            raise error("library file {} contains non-string value: {}"
                        .format(repr(filename), repr(val)))
        if key not in DEFAULT_LIBRARY:
            raise error("library file {} contains unexpected key: {}"
                        .format(repr(filename), repr(key)))

def decode_float(value):
    try:
        return float(value)
    except ValueError:
        raise error("malformed floating-point value: {}"
                    .format(repr(value)))

def decode_option(name, value):
    try:
        if name == "deduplication-threshold":
            return decode_float(value)
        return value
    except Error as e:
        raise error("for option {}: {}".format(name, e))

def task_init(io, path=None):
    """
    Initialize a new eTunes library metadata file. The path may be
    either a file (to put the metadata in) or a directory (where
    DEFAULT_LIBRARY_FILENAME is then used to get the full path). If
    omitted, the current directory is used.
    """
    if path is None:
        path = io.getcwd()
    else:
        path = io.realpath(path)
    if io.isdir(path):
        path = io.join(path, DEFAULT_LIBRARY_FILENAME)
    library_file = path
    library_dir = io.dirname(path)
    try:
        if not io.isdir(library_dir):
            io.mkdir(library_dir)
    except OSError as e:
        raise error("could not create library directory {}: {}"
                    .format(repr(library_dir), e))
    io.chdir(library_dir)
    preexisting_library_file = locate_dominating_file(
        io, DEFAULT_LIBRARY_FILENAME, library_dir)
    git_dir = locate_dominating_file(io, ".git", library_dir)
    if git_dir:
        io.print("note: not initializing Git repository, already exists: {}"
                 .format(repr(git_dir)))
    else:
        try:
            git_dir = io.getcwd()
            run_and_check(io, ["git", "init"])
            commit_working_tree(io, "Add pre-existing files")
        except OSError as e:
            raise git_not_installed_error(e)
    gitignore_path = io.join(git_dir, ".gitignore")
    if io.exists(gitignore_path) or io.islink(gitignore_path):
        io.print("note: not creating .gitignore, already exists: {}"
                 .format(repr(gitignore_path)))
        io.print("note: please make sure '/work/' is in your .gitignore")
    else:
        ensure_working_tree_clean(io)
        with io.open(gitignore_path, "w") as f:
            f.write("/work/")
            f.write("\n")
        commit_working_tree(io, "Add .gitignore for '/work/'")
    if preexisting_library_file:
        io.print("note: not creating library file, already exists: {}"
                 .format(repr(preexisting_library_file)))
    else:
        ensure_working_tree_clean(io)
        options = {}
        for key, val in DEFAULT_LIBRARY.items():
            if callable(val):
                options[key] = val(io)
            else:
                options[key] = val
        yaml_to_file(io, options, library_file)
        io.print("Created library file with default settings in {}"
                 .format(path), file=io.stderr)
        commit_working_tree(io, "Create library.yml with default settings")

# jsonschema for filters. Used in QUERY_SCHEMA.
MATCHER_SCHEMA = {
    "anyOf": [
        {
            "type": "string",
        },
        {
            "type": "object",
            "properties": {
                "type": {
                    "anyOf": [
                        {
                            "type": "string",
                            "pattern": "^literal$",
                        },
                        {
                            "type": "string",
                            "pattern": "^regex$",
                        },
                    ]
                },
                "query": {
                    "type": "string",
                },
                "substring": {
                    "type": "boolean",
                },
                "case-fold": {
                    "type": "boolean",
                },
            },
            "required": ["type", "query"],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "pattern": "^literal$",
                },
                "query": {
                    "type": "string",
                },
            },
        },
        {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "pattern": "^missing$",
                },
                "query": {
                    "type": "boolean",
                },
            },
            "required": ["type", "query"],
            "additionalProperties": False,
        },
    ]
}

# jsonschema for queries.
QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
        },
        "last-id": {
            "type": "string",
        },
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "value": {
                        "type": "string",
                    },
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        "songs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "object",
                        "additionalProperties": MATCHER_SCHEMA,
                    },
                    "get": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "set": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "string",
                        },
                    },
                    "extract": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "embed": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "rename": {
                        "type": "boolean",
                    },
                    "check": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            },
        },
        "import": {
            "type": "array",
            "items": MATCHER_SCHEMA,
        },
    }
}

def validate_query(query, query_name):
    """
    If the query does not match QUERY_SCHEMA according to jsonschema,
    raise an error. query_name is used to identify the query in error
    messages.
    """
    try:
        jsonschema.validate(query, QUERY_SCHEMA)
    except jsonschema.ValidationError as e:
        raise with_extra(error("{} was malformed: {}"
                               .format(query_name, str(e))),
                         "\nquery:\n" + json.dumps(query, indent=2))

def is_working_tree_clean(io):
    """
    Determine if there are unstaged files, or staged files, or
    untracked files. In other words, check if 'git status' would
    report anything out of the ordinary.
    """
    try:
        # Make sure working tree matches the index.
        result = io.run(["git", "diff-files", "--quiet"])
        if result.returncode != 0:
            return False
        # Make sure index matches HEAD. Or, if HEAD does not exist,
        # make sure there are no files in the index.
        result = io.run(["git", "rev-parse", "HEAD"],
                        stdout=io.DEVNULL, stderr=io.DEVNULL)
        no_commits_yet = result.returncode != 0
        if no_commits_yet:
            result = io.run(["git", "ls-files"], stdout=io.PIPE)
            if result.stdout:
                return False
        else:
            result = io.run(
                ["git", "diff-index", "--cached", "--quiet", "HEAD"])
            if result.returncode != 0:
                return False
        # Make sure there are no untracked files.
        result = run_and_check(
            io, ["git", "ls-files", "--others", "--exclude-standard"],
            stdout=io.PIPE)
        if result.stdout:
            return False
        return True
    except OSError as e:
        raise git_not_installed_error(e)

def ensure_working_tree_clean(io):
    if not is_working_tree_clean(io):
        try:
            io.run(["git", "status"])
        except OSError as e:
            raise git_not_installed_error(e)
        raise with_extra(error("working directory is not clean"),
                         ("hint",
                          "you should clean up manually in {}"
                          .format(repr(io.getcwd()))))

def commit_working_tree(io, message, optional=False):
    try:
        run_and_check(io, ["git", "add", "-A"])
        if not optional or not is_working_tree_clean(io):
            run_and_check(
                io, ["git", "commit", "--allow-empty", "-m", message])
    except OSError as e:
        raise git_not_installed_error(e)

PROCESS_FILENAME = "process"
LAST_ID_FILENAME = "last-id"

def return_query_result(io, query, response, last_id_file):
    transaction_id = str(uuid.uuid4())
    try:
        with io.open(last_id_file, "w") as f:
            f.write(transaction_id)
            f.write("\n")
    except OSError as e:
        response["errors"].append({
            "reason": "os-error",
            "message": str(e),
            "file": last_id_file,
        })
    response["success"] = not response["errors"]
    json.dump(response, io.stdout, indent=2)
    io.print()
    if response["success"]:
        commit_working_tree(io, query.get("description", "Unnamed query"),
                            optional=True)

def execute_query(io, query, query_name, library_file):
    ensure_working_tree_clean(io)
    options = file_to_yaml(io, library_file)
    validate_library_options(io, options, library_file)
    work_dir = io.join(io.dirname(library_file), "work")
    io.makedirs(work_dir, exist_ok=True)
    process_file = io.join(work_dir, PROCESS_FILENAME)
    try:
        with io.open(process_file) as f:
            lines = f.read().splitlines()
            pid, create_time = lines
            pid = int(pid)
            create_time = float(create_time)
            prev_process = psutil.Process(pid)
            real_create_time = prev_process.create_time()
            if abs(create_time - real_create_time) < 0.1:
                raise error("another query is already running (PID {})"
                            .format(pid))
    except (OSError, ValueError, psutil.NoSuchProcess):
        pass
    errors = []
    response = {
        "partial": False,
        "errors": errors,
    }
    last_id_file = io.join(work_dir, LAST_ID_FILENAME)
    expected_last_id = query.get("last-id")
    if expected_last_id:
        try:
            with io.open(last_id_file) as f:
                actual_last_id = f.read().strip()
                if expected_last_id != actual_last_id:
                    errors.append({
                        "reason": "intervening-transaction",
                        "message":
                        ("Another transaction ({}) happened after {} "
                         "but before this one")
                        .format(actual_last_id, expected_last_id)
                    })
        except OSError:
            pass
    new_options = dict(options)
    new_options_decoded = {}
    for name, value in options.items():
        try:
            new_options_decoded[name] = decode_option(name, value)
        except Error as e:
            raise error(
                "library file {} contains malformed value {} for option {}"
                .format(repr(library_file), repr(value), repr(name)))
    if "options" in query:
        unknown_options = set()
        for option_setting in query["options"]:
            name = option_setting["name"]
            if name not in DEFAULT_LIBRARY:
                unknown_options.add(name)
                continue
            if "value" in option_setting:
                value = option_setting["value"]
                new_options[name] = value
                try:
                    new_options_decoded[name] = decode_option(name, value)
                except Error as e:
                    errors.append({
                        "reason": "malformed-option-value",
                        "message": ("Malformed value {} for option {}"
                                    .format(repr(value), repr(name))),
                        "name": name,
                        "value": value,
                    })
        options_response = []
        for option_setting in query["options"]:
            options_response.append(new_options[option_setting["name"]])
        response["options"] = options_response
        for unknown_option in unknown_options:
            errors.append({
                "reason": "unknown-option",
                "message": "Unknown option {}".format(repr(unknown_option)),
                "name": unknown_option,
            })
    if errors:
        return_query_result(io, query, response, last_id_file)
    # Now we start changing things on disk, if there were no errors.
    if new_options != options:
        try:
            yaml_to_file(io, new_options, library_file)
            response["partial"] = True
        except Error as e:
            errors.append({
                "reason": "os-error",
                "message": str(e),
                "file": library_file,
            })
    response["partial"] = False
    return_query_result(io, query, response, last_id_file)

def task_query(io, query_source, library_file, orig_cwd):
    """
    Execute a query against the eTunes database. The query is taken
    from stdin or a file, or is given on the command line. The query
    response is written to stdout.

    Failed queries have their errors reported in the query response,
    while malformed queries result in a message on stderr and a
    nonzero exit code.
    """
    if query_source == "-":
        query_text = io.stdin.read()
        query_name = "query from stdin"
    elif query_source.startswith("@"):
        filename = query_source[1:]
        filename = io.join(orig_cwd, filename)
        try:
            with io.open(filename, "r") as f:
                query_text = f.read()
                query_name = "query from file {}".format(repr(filename))
        except OSError as e:
            raise error("could not read query file {}: {}"
                        .format(repr(filename), str(e)))
    elif query_source.startswith("{") or query_source.startswith("["):
        query_text = query_source
        query_name = "query from command-line argument"
    else:
        raise with_usage(error("string {} does not identify a query"),
                         usage("query"))
    try:
        query = json.loads(query_text)
    except json.decoder.JSONDecodeError as e:
        raise with_extra(error("could not parse query JSON: {}"
                               .format(str(e))),
                         "query:\n" + query_text)
    validate_query(query, query_name)
    execute_query(io, query, query_name, library_file)

def handle_args(io, args):
    """
    Parse command-line arguments and take the appropriate action.
    """
    literal = False
    library_file = None
    subcommand = None
    config = {}
    while args:
        arg = args[0]
        if arg.startswith("-") and arg != "-" and not literal:
            if arg == "--":
                literal = True
            elif arg in ("-h", "-?", "-help", "--help"):
                io.print(usage())
                return
            elif arg in ("-v", "-V", "-version", "--version"):
                io.print(get_version(), file=io.stderr)
                return
            elif arg.startswith("--library="):
                library_file = arg[len("--library="):]
                args = args[1:]
            elif arg == "--library":
                if len(args) >= 2:
                    library_file = args[1]
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
            if arg in SUBCOMMANDS:
                subcommand = arg
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
        elif subcommand == "query":
            if "query_source" not in config:
                config["query_source"] = arg
            else:
                raise with_usage(
                    error("unexpected argument: {}".format(repr(arg))),
                    usage("query"))
        args.pop(0)
    if subcommand is None:
        raise with_usage(error("no subcommand given"), usage())
    if subcommand == "help":
        io.print(usage())
        return
    if subcommand == "version":
        io.print(get_version(), file=io.stderr)
        return
    if subcommand == "init":
        task_init(io, path=config.get("path"))
        return
    if library_file is None:
        library_file = io.environ.get("ETUNES_LIBRARY")
    if library_file is None:
        library_file = locate_dominating_file(io, DEFAULT_LIBRARY_FILENAME)
        if library_file is None:
            raise with_extra(
                error("cannot find file {} in working or parent directories"
                      .format(repr(DEFAULT_LIBRARY_FILENAME))),
                ("hint", "to create, run 'etunes init'"))
    if io.isdir(library_file):
        library_file = io.join(library_file, DEFAULT_LIBRARY_FILENAME)
    if not io.isfile(library_file):
        raise error(
            "library file does not exist: {}".format(repr(library_file)))
    orig_cwd = io.getcwd()
    io.chdir(io.dirname(library_file))
    if subcommand == "query":
        if "query_source" not in config:
            raise with_usage(error("no query given"),
                             usage("query"))
        task_query(io, query_source=config["query_source"],
                   library_file=library_file,
                   orig_cwd=orig_cwd)
        return

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
        io.print("\n".join(lines), file=io.stderr)
    except Exception:
        io.print_exc()
    return 1

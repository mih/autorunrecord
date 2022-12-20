# Sphinx autorunrecord extension

This is an extension for the [Sphinx documentation system](sphinx-doc.org). It
provides a `runrecord` directive that works like `literalinclude`. However,
instead of just loading content from a file, the content is first generated by
executing a command (Python or shell), and capturing its output.

This extension is used heavily for the [DataLad
handbook](http://handbook.datalad.org).

## Configuration

There are two main configuration settings. A base directory for all
per-runrecord working directories, and a custom runtime environment
specification, used for all command executions. The desired setup for both is
added to a Sphinx project's `conf.py`:

    # autorunrecord setup (extension used to run and capture the output of
    # examples)
    autorunrecord_basedir = '/home/me'
    # pre-crafted artificial environment to run the code examples in
    autorunrecord_env = {
        # make everything talk in english
        'LANG': 'en_US.UTF-8',
        'LANGUAGE': 'en_US:en',
        'LC_CTYPE': 'en_US.UTF-8',
        # use very common shell
        'SHELL': '/bin/bash',
        # keep username extra short to save on line length
        'USER': 'me',
        'USERNAME': 'me',
        'HOME': autorunrecord_basedir,
        # earned a PhD in 1678 and taught mathematics at the University of Padua
        'GIT_AUTHOR_EMAIL': 'elena@example.net',
        'GIT_AUTHOR_NAME': 'Elena Piscopia',
        'HOST': 'padua',
        # maintain the PATH to keep all installed software functional
        'PATH': os.environ['PATH'],
        'GIT_EDITOR': 'vim',
    }
    if 'VIRTUAL_ENV' in os.environ:
        # inherit venv, if there is any
        autorunrecord_env.update(VIRTUAL_ENV=os.environ['VIRTUAL_ENV'])

To complete the setup, the `autorunrecord` extension needs to be added to the
list of Sphinx extensions to load for a project (again in `conf.py`):

    # Add any Sphinx extension module names here, as strings. They can be extensions
    # coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
    extensions = [
        ...
        'sphinxcontrib.autorunrecord',
    ]

## Usage

When this extension is loaded, Sphinx recognized `runrecord` directives. This
additional directive is derived from the standard `literalinclude`
([documentation](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-literalinclude))
directive, hence supports all its features, like line selection and
highlighting.

On top of that, however, one can specify code to generate the content to
"literalinclude" to begin with. Here is how this can look:

    .. runrecord:: output/example1
       :language: console
       :workdir: workdirs/group1

       # this is a comment
       $ echo 123

This directive will execute the shell command `echo 123`, and write its output
into the file `output/example1`. This file is located *relative* to the parent
directory of the file containing the `runrecord` directive.

The output file will not only have a command's output, but actually start with
the body of the directive, i.e. any comments and commands. Comment lines (only
copied into the output file) are distinguished from command lines (copied into
the output, and also executed) by a configurable prefix. This is `$ ` for
console/shell commands, and `>>> ` for Python code. The active set for a
`runrecord` is determined by the `language` option (`console` or `python`).

Only one joint set of commands is executed per `runrecord`, and only a single
consecutive stream of outputs from all commands of a `runrecord` is captured.
For more complex procedures it can be useful to intersperse individual commands
with additional documentation. This can be achieved by splitting such blocks of
commands into multiple runrecords. The code in them can operate incrementally
when one and the same `workdir` is declared. All working directories are
located underneath `autorunrecord_basedir`. If no specific working directory is
declared, the default working directory is derived from the name and location
of the source file containing the `runrecord` directive. This means that all
runrecords from the same source file will run incrementally in the same working
directory.

In order to decouple Sphinx-builds of the documentation from executing the code
snippets, code execution will only be attempted when the output file does *not*
exist. Removing these files to trigger a full rebuild must be managed
externally, for example via a Makefile. Moreover, also the working directories
need to be cleaned up separately.


## Additional options

### Hidden commands: `realcommand`

Sometimes it is necessary to simplify a command to be included in the document
in comparison to a command that is executed to generate a desired output.  A
"hidden" `realcommand` can include error-handling, or retry-logic for remote
service requests to improve robustness of execution, without imposing the
associated complexity on a documentation reader. A `:realcommand:` option can
be declared in a `runrecord` with any such alternative command. If found,
command lines from the `runrecord` directive's body are merely copied into the
output, and `realcommand` is executed instead.

### Output normalization

When command output is tracked in a version control system, or is generated
by multiple entities, it can make sense to normalize it. For example, to
standardize timestamps, line-endings, or user names.

The configuration setting `autorunrecord_line_replace` can be set in `conf.py`.
It must be a list with 2-tuples. The first item in each tuple is a match
expression, and the second item a replacement value. The syntax for both must
match the requirements of the `sub()` function of the Python `re` module.
As indicated by the configuration item name, the replacement (matching) is
performed line-by-line.

Here is an example for removing trailing spaces on each output line:

    autorunrecord_line_replace = [
        # trailing space removal
        (r'[ ]+$', ''),
    ]

Normalization expressions can also be configured per `runrecord` using the
`:linereplace:` field. Each line in the body of this field is considered
a replacement specification. The syntax is similar to UNIX `sed`. The first
character on the line defines a delimiting character. This delimiter must
also be repeated as the last character on that line. The only other occurrence
of this character must be the boundary between match expression and
replacement expression. Here is an example to replace a particular path name
with a placeholder.

    .. runrecord:: output1
       :language: console
       :linereplace:
         %/home/myname/%HOME%

Any number of replacement specifications can be provided. They will be
executed in the order of their specification and *following* any specifications
declared via `autorunrecord_line_replace` in `conf.py`.

### Expected failures

By default, the code of a runrecord is expected to execute without errors
yielding an exitcode of zero. If that is not the case, a `RuntimeException` is
raised. However, it is often educational to demonstrate error conditions.
To enable purposeful execution errors, a `runrecord` can be annotated with
an `exitcode` option to declare expected exitcodes (other than 0):

    .. runrecord:: output1
       :language: console
       :exitcode: 3

       $ exit 3

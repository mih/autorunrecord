# -*- coding: utf-8 -*-

from pathlib import Path
import os
from six import (
    text_type,
)
import re
from subprocess import (
    Popen,
    PIPE,
    STDOUT,
)

from docutils.parsers.rst import directives
from sphinx.errors import SphinxError
from sphinx.directives.code import LiteralInclude

castcount = 0


class RunRecordError(SphinxError):
    category = 'runrecord error'


class AutoRunRecord(object):
    here = os.path.abspath(__file__)
    pycon = os.path.join(os.path.dirname(here),'pycon.py')
    config = dict(
        pycon='python ' + pycon,
        pycon_prefix_str='>>> ',
        console='bash',
        console_prefix_str='$ ',
    )

    @classmethod
    def builder_init(cls, app):
        cls.config.update(app.builder.config.autorunrecord_languages)


class RunRecord(LiteralInclude):
    has_content = True
    option_spec = dict(
        LiteralInclude.option_spec,
        language=directives.unchanged_required,
        realcommand=directives.unchanged_required,
        workdir=directives.unchanged_required,
        cast=directives.unchanged,
        notes=directives.unchanged
    )

    def run(self):
        doc_dir = Path(self.env.srcdir)
        src_file = Path(self.state_machine.get_source(self.lineno))
        capture_file = src_file.parent / self.arguments[0]
        base_wdir = Path(self.env.app.doctreedir).parent \
            if self.config.autorunrecord_basedir is None \
            else Path(self.config.autorunrecord_basedir)
        work_dir = base_wdir / self.options.get(
            'workdir',
            # default is to place the workdir under a relpath that
            # is the same as the source file's in the doc tree
            src_file.relative_to(doc_dir).parent / src_file.stem)
        if not capture_file.exists():
            if not work_dir.exists():
                work_dir.mkdir(parents=True)

            self.capture_output(
                capture_file,
                work_dir,
                self.config.autorunrecord_env,
            )

        # to build cast, have CAST_DIR env variable configured with path
        cast_dir = self.config.autorunrecord_env.get('CAST_DIR')
        if cast_dir:
            cast_dir = Path(cast_dir)
            if not cast_dir.exists():
                cast_dir.mkdir()
            # get file name where to write the cast to
            cast = self.options.get('cast', None)
            if cast is not None:

                # counter for code snippets
                global castcount
                castcount += 1

                capture_file_cast = cast_dir / cast
                code_cast = self.options.get('cast') + '_code.rst'
                length = len(code_cast)
                name = os.path.basename(capture_file_cast)
                capture_code_list = cast_dir / code_cast
                self.write_cast(capture_file_cast, castcount)
                self.write_commands(capture_code_list,
                                    castcount,
                                    length,
                                    name)

        docnodes = super(RunRecord, self).run()
        return docnodes

    def capture_output(self, capture_file, work_dir, env):
        config = AutoRunRecord.config
        language = self.options.get('language', 'console')
        if language not in config:
            raise RunRecordError('Unknown language %s' % language)

        # Get configuration values for the language
        args = config[language].split()
        output_encoding = config.get(language + '_output_encoding', 'utf-8')

        # Build the code text
        code = self.get_code(encode=True)

        proc = Popen(
            args,
            bufsize=-1,
            stdin=PIPE,
            stdout=PIPE,
            # capture both in a merged stream
            stderr=STDOUT,
            cwd=text_type(work_dir),
            env=env,
        )

        # Run the code
        stdout, stderr = proc.communicate(code)

        # turn into str
        output = stdout.decode(output_encoding)

        line_replace = self.config.autorunrecord_line_replace
        if line_replace:
            for repl_match, repl in line_replace:
                output = re.sub(repl_match, repl, output, flags=re.MULTILINE)

        # Process output
        out = '{}\n{}'.format(
            '\n'.join(self.content),
            output,
        )

        if not capture_file.parent.exists():
            capture_file.parent.mkdir(parents=True)
        capture_file.write_text(out)

    def get_code(self, encode=False):
        """Extract code examples from a runrecord

        Parameters
        ----------
        encode : bool
            If True, encode code according to AutoRunRecords config
        Returns
        -------
        code : str
        """

        config = AutoRunRecord.config
        language = self.options.get('language', 'console')
        prefix_str = config.get(language + '_prefix_str', '')
        input_encoding = config.get(language + '_input_encoding', 'utf-8')

        code = self.options.get('realcommand', None)
        if code is None:
            codelines = (
                line[len(prefix_str):] if line.startswith(
                    prefix_str) else line
                for line in self.content
            )
            code = u'\n'.join(codelines)
        if encode:
            code = code.encode(input_encoding)
        return code

    def write_cast(self, capture_file_cast, castcount):
        """Write a cast from tagged code examples"""
        import shlex
        notes = self.options.get('notes', None)
        code = self.get_code(encode=False)
        code = '### Code snippet {}\n{}'.format(castcount,
                                                code)
        # Build the code text; first try realcommand
        # write the cast
        # TODO: make clean has to clean the casts, else we'll append and
        # append and append with every build from scratch
        mode = 'a' if capture_file_cast.exists() else 'w'
        with open(capture_file_cast, mode) as f:
            if notes is not None:
                f.write('say {}\n'.format(shlex.quote(notes)))
            f.write('run {}\n'.format(shlex.quote(code)))

    def write_commands(self, capture_code_list, castcount, length, name):
        """Writes a list of all code commands from the runrecords into an
        rst file, and formats code to be displayed as code by Sphinx."""
        from textwrap import indent
        code = self.get_code(encode=False)
        code = indent(code, ' ' * 3)
        mode = 'a' if capture_code_list.exists() else 'w'
        with open(capture_code_list, mode) as f:
            if mode == 'w':
                header = "Code from chapter: {}\n----------{}\n\n".format(
                    name,
                    '-' * length,
                )
                f.write(header)
            f.write('Code snippet {}::\n\n{}\n\n\n'.format(
                castcount,
                code,
            ))


def setup(app):
    app.add_directive('runrecord', RunRecord)
    app.connect('builder-inited', AutoRunRecord.builder_init)
    app.add_config_value(
        'autorunrecord_languages',
        AutoRunRecord.config,
        'env',
    )
    app.add_config_value('autorunrecord_basedir', None, 'env')
    app.add_config_value('autorunrecord_env', None, 'env')
    app.add_config_value('autorunrecord_line_replace', None, 'env')

# vim: set expandtab shiftwidth=4 softtabstop=4 :

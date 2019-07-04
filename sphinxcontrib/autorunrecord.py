# -*- coding: utf-8 -*-

from pathlib import Path
import os
from six import (
    text_type,
)
from subprocess import (
    Popen,
    PIPE,
    STDOUT,
)

from docutils.parsers.rst import directives
from sphinx.errors import SphinxError
from sphinx.directives.code import LiteralInclude


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
    )

    def run(self):
        doc_dir = Path(self.env.srcdir)
        src_file = Path(self.state_machine.get_source(self.lineno))
        capture_file = src_file.parent / self.arguments[0]
        work_dir = Path(self.env.app.doctreedir).parent / \
            'wdirs' / src_file.relative_to(doc_dir).parent / src_file.stem
        if not work_dir.exists():
            work_dir.mkdir(parents=True)

        if not capture_file.exists():
            self.capture_output(capture_file, work_dir)

        docnodes = super(RunRecord, self).run()
        return docnodes

    def capture_output(self, capture_file, work_dir):
        config = AutoRunRecord.config
        language = self.options.get('language', 'console')
        if language not in config:
            raise RunRecordError('Unknown language %s' % language)

        # Get configuration values for the language
        args = config[language].split()
        input_encoding = config.get(language + '_input_encoding', 'utf-8')
        output_encoding = config.get(language + '_output_encoding', 'utf-8')
        prefix_str = config.get(language + '_prefix_str', '')

        # Build the code text
        code = self.options.get('realcommand', None)
        if code is None:
            codelines = (
                line[len(prefix_str):] if line.startswith(prefix_str) else line
                for line in self.content
            )
            code = u'\n'.join(codelines)
        code = code.encode(input_encoding)

        proc = Popen(
            args,
            bufsize=1,
            stdin=PIPE,
            stdout=PIPE,
            # capture both in a merged stream
            stderr=STDOUT,
            cwd=text_type(work_dir),
        )

        # Run the code
        stdout, stderr = proc.communicate(code)

        # Process output
        out = '{}\n{}'.format(
            u'\n'.join(self.content),
            stdout.decode(output_encoding),
        )

        if not capture_file.parent.exists():
            capture_file.parent.mkdir(parents=True)
        capture_file.write_text(out)


def setup(app):
    app.add_directive('runrecord', RunRecord)
    app.connect('builder-inited', AutoRunRecord.builder_init)
    app.add_config_value('autorunrecord_languages', AutoRunRecord.config, 'env')

# vim: set expandtab shiftwidth=4 softtabstop=4 :

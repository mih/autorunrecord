# Sphinx autorunrecord extension

This is an extension for the [Sphinx documentation system](sphinx-doc.org). It
provides a `runrecord` directive that works like `literalinclude`. However,
instead of just loading content from a file, the content is first generated by
executing a command (Python or shell), and capturing its output.

This extension is used heavily for the [DataLad
handbook](http://handbook.datalad.org).
import tempfile
import shutil
from pathlib import Path
from sphinx.application import Sphinx
from docutils.frontend import OptionParser
from sphinx.util.docutils import sphinx_domains
from docutils.io import StringOutput
from sphinx.util import rst, relative_uri
from os import path
from sphinx.io import read_doc
import time


class Timer:
    def __init__(self, description):
        self.description = description

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        print(self.description, 'took', self.end - self.start)


class DocGenerator:
    def __init__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.doc_dir = Path(self.temp_dir.name) / 'doc'
        self.doc_file = self.doc_dir / 'index.rst'
        shutil.copytree(Path('./resources/doc_template'), self.doc_dir)
        absolute_path = str(self.doc_dir.absolute())
        app = Sphinx(absolute_path, absolute_path, absolute_path, absolute_path, 'html', freshenv=True)
        config = app.builder.config
        app.builder.env.srcdir = app.builder.srcdir
        app.builder.env.doctreedir = app.builder.doctreedir
        app.builder.env.find_files(config, app.builder.env.app.builder)
        app.builder.env.config = config
        app.builder.env._nitpick_ignore = set(app.builder.env.config.nitpick_ignore)
        # added, changed, removed = app.builder.env.get_outdated_files(False)
        self.app = app
        docnames = ['index']
        app.builder.env.app.emit('env-before-read-docs', app.builder.env, docnames)

        docname = 'index'
        app.emit('env-purge-doc', app.builder.env, docname)
        app.builder.env.clear_doc(docname)
        app.builder.env.prepare_settings(docname)
        docutilsconf = path.join(app.builder.env.srcdir, 'docutils.conf')
        OptionParser.standard_config_files[1] = docutilsconf
        if path.isfile(docutilsconf):
            app.builder.env.note_dependency(docutilsconf)
        self.destination = StringOutput(encoding='utf-8')

    def make_html(self, docstring):
        with Timer('make_html'):
            with open(self.doc_file, 'w') as f:
                f.write(docstring)
            app = self.app
            docname = 'index'
            with sphinx_domains(app.builder.env), rst.default_role(docname, app.builder.env.config.default_role):
                doctree = read_doc(app.builder.env.app, app.builder.env, app.builder.env.doc2path(docname))
            for domain in app.builder.env.domains.values():
                domain.process_doc(app.builder.env, docname, doctree)
            app.emit('doctree-read', doctree)
            app.builder.prepare_writing({docname})
            doctree = app.builder.env.get_and_resolve_doctree(docname, app.builder, doctree)
            app.builder.write_doc_serialized(docname, doctree)
            doctree.settings = app.builder.docsettings
            app.builder.secnumbers = app.builder.env.toc_secnumbers.get(docname, {})
            app.builder.fignumbers = app.builder.env.toc_fignumbers.get(docname, {})
            app.builder.imgpath = relative_uri(app.builder.get_target_uri(docname), '_images')
            app.builder.dlpath = relative_uri(app.builder.get_target_uri(docname), '_downloads')
            app.builder.current_docname = docname
            app.builder.docwriter.write(doctree, self.destination)
            app.builder.docwriter.assemble_parts()
            body = app.builder.docwriter.parts['fragment']
        return body


if __name__ == "__main__":
    rst_input_string = '''Basic use
---------

Importing the main class::

    >>> from pathlib import Path
'''
    doc_generator = DocGenerator()
    print(doc_generator.make_html(rst_input_string))

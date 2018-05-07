from docutils.core import Publisher
from docutils.frontend import OptionParser
from docutils.io import NullOutput, StringOutput
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.io import SphinxStandaloneReader, SphinxDummyWriter, SphinxDummySourceClass
from sphinx.util.docutils import sphinx_domains
from sphinx.util import rst, relative_uri
from pathlib import Path
from os import path
from sphinx.io import read_doc
from sphinx.util.parallel import SerialTasks
from sphinx.application import ENV_PICKLE_FILENAME
from time import time

absolute_path = str(Path('sphinx_input').absolute())

app = Sphinx(absolute_path, absolute_path, absolute_path, absolute_path, 'html', freshenv=True)
# app.build(True, ['sphinx_input/pathlib.rst'])
# app.builder.build_specific(['sphinx_input/pathlib.rst'])

# app.builder.build([absolute_path + '/pathlib.rst'])





# updated_docnames = set(app.builder.env.update(app.builder.config, app.builder.srcdir, app.builder.doctreedir))
config = app.builder.config
config_changed = False
app.builder.env.srcdir = app.builder.srcdir
app.builder.env.doctreedir = app.builder.doctreedir
app.builder.env.find_files(config, app.builder.env.app.builder)
app.builder.env.config = config
app.builder.env._nitpick_ignore = set(app.builder.env.config.nitpick_ignore)
added, changed, removed = app.builder.env.get_outdated_files(config_changed)
print('added:', added)
print('changed:', changed)
print('removed:', removed)
# docnames = sorted(added | changed)
docnames = ['pathlib']
app.builder.env.app.emit('env-before-read-docs', app.builder.env, docnames)

start_time = time()
# app.builder.env._read_serial(docnames, app.builder.env.app)
for docname in docnames:
    app.emit('env-purge-doc', app.builder.env, docname)
    app.builder.env.clear_doc(docname)
    # app.builder.env.read_doc(docname, app)
    app.builder.env.prepare_settings(docname)
    docutilsconf = path.join(app.builder.env.srcdir, 'docutils.conf')
    # read docutils.conf from source dir, not from current dir
    OptionParser.standard_config_files[1] = docutilsconf
    if path.isfile(docutilsconf):
        app.builder.env.note_dependency(docutilsconf)

    with sphinx_domains(app.builder.env), rst.default_role(docname, app.builder.env.config.default_role):
        doctree = read_doc(app.builder.env.app, app.builder.env, app.builder.env.doc2path(docname))

    # post-processing
    for domain in app.builder.env.domains.values():
        domain.process_doc(app.builder.env, docname, doctree)

    # allow extension-specific post-processing
    if app:
        app.emit('doctree-read', doctree)

print('docnames', docnames)
updated_docnames = set(docnames)
print('updated_docnames:', updated_docnames)


# app.builder.write(set(), list(updated_docnames), 'update')
docnames = set(updated_docnames)
app.builder.prepare_writing(docnames)
# app.builder._write_serial(sorted(docnames))
for docname in docnames:
    doctree = app.builder.env.get_and_resolve_doctree(docname, app.builder, doctree)
    app.builder.write_doc_serialized(docname, doctree)
    # app.builder.write_doc(docname, doctree)
    destination = StringOutput(encoding='utf-8')
    doctree.settings = app.builder.docsettings

    app.builder.secnumbers = app.builder.env.toc_secnumbers.get(docname, {})
    app.builder.fignumbers = app.builder.env.toc_fignumbers.get(docname, {})
    app.builder.imgpath = relative_uri(app.builder.get_target_uri(docname), '_images')
    app.builder.dlpath = relative_uri(app.builder.get_target_uri(docname), '_downloads')  # type: unicode
    app.builder.current_docname = docname
    app.builder.docwriter.write(doctree, destination)
    app.builder.docwriter.assemble_parts()
    body = app.builder.docwriter.parts['fragment']
    print(body)

print('time elapsed:', time() - start_time)
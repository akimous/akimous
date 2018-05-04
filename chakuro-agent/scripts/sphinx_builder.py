from docutils.core import Publisher
from docutils.io import NullOutput
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.io import SphinxStandaloneReader, SphinxDummyWriter, SphinxDummySourceClass
from sphinx.util.docutils import sphinx_domains
from sphinx.util import rst
from pathlib import Path
from os import path
from sphinx.util.parallel import SerialTasks
from sphinx.application import ENV_PICKLE_FILENAME

absolute_path = str(Path('sphinx_input').absolute())

app = Sphinx(absolute_path, absolute_path, absolute_path, absolute_path, 'html', freshenv=True)
# app.build(True, ['sphinx_input/pathlib.rst'])
# app.builder.build_specific(['sphinx_input/pathlib.rst'])

# app.builder.build([absolute_path + '/pathlib.rst'])





updated_docnames = set(app.builder.env.update(app.builder.config, app.builder.srcdir, app.builder.doctreedir))
# env.update


print('updated_docnames:', updated_docnames)

if updated_docnames:
    app.builder.env.topickle(path.join(app.builder.doctreedir, ENV_PICKLE_FILENAME))

app.builder.write(set(), list(updated_docnames), 'update')





# with sphinx_domains(app.env), rst.default_role('Not being used~', app.env.config.default_role):
    # filename = str(Path('sphinx_input/pathlib.rst').absolute())
    # app.env.temp_data['docname'] = filename
    # input_class = app.registry.get_source_input(filename)
    # reader = SphinxStandaloneReader(app)
    # source = input_class(app, app.env, source=None, source_path=filename,
    #                      encoding=app.env.config.source_encoding)
    # parser = app.registry.create_source_parser(app, filename)
    #
    # pub = Publisher(reader=reader,
    #                 parser=parser,
    #                 writer=SphinxDummyWriter(),
    #                 source_class=SphinxDummySourceClass,
    #                 destination=NullOutput())
    # pub.set_components(None, 'restructuredtext', None)
    # pub.process_programmatic_settings(None, app.env.settings, None)
    # pub.set_source(source, filename)
    # pub.publish()
    # print(pub.writer.parts)


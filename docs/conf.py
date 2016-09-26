# -*- coding: utf-8 -*-
import sys

sys.path.insert(0, '../')
import sprockets_dynamodb

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode'
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'sprockets-dynamodb'
copyright = u'2016, AWeber Communications'
author = u'AWeber Communications'

release = sprockets_dynamodb.__version__
version = '.'.join(release.split('.')[0:1])

language = None
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = 'sphinx'
todo_include_todos = False
html_static_path = ['_static']
htmlhelp_basename = 'sprockets-dynamodbdoc'
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.5', None),
    'tornado_aws': ('https://tornado-aws.readthedocs.io/en/stable/', None),
    'tornado': ('https://tornado.readthedocs.io/en/stable/', None)
}

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'crispy'
copyright = '2022, John A. Armstrong'
author = 'John A. Armstrong'

# The full version, including alpha/beta/rc tags
release = '1.0.2'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.napoleon", "sphinx.ext.autodoc", "sphinx.ext.intersphinx", "sphinx.ext.linkcode", "sphinx.ext.githubpages", "sphinx_gallery.gen_gallery"
]
autodoc_member_order = "bysource"

sphinx_gallery_conf = {
     'examples_dirs': ['../examples', '../tutorials'],   # path to your example scripts
     'gallery_dirs': ['auto_examples', 'tutorials'],  # path to where to save gallery generated output,
     'run_stale_examples' : True
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'p-greenblue'
# from PSphinxTheme import utils
# p, html_theme, needs_sphinx = utils.set_psphinxtheme(html_theme)
# html_theme_path = p
# html_theme = 'sphinx_theme_pd'
# import sphinx_theme_pd
# html_theme_path = [sphinx_theme_pd.get_html_theme_path()]
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


#-- Options for link code ------------------------------------------------------
def linkcode_resolve(domain, info):
    if domain != 'py':
        return None
    if not info['module']:
        return None
    filename = info['module'].replace('.', '/')
    return "https://github.com/bionictoucan/crispy/blob/main/%s.py" % filename

import warnings
warnings.filterwarnings("ignore")
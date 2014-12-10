"""
PyBuilder configuration file

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

from pybuilder.core import use_plugin, init

use_plugin('python.core')
use_plugin('python.unittest')
# use_plugin('python.coverage')
use_plugin('python.flake8')
use_plugin('python.install_dependencies')
# use_plugin('python.distutils')

default_task = ['install_dependencies', 'analyze', 'publish']


import sys
import os
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)


@init
def initialize(project):
    project.depends_on_requirements("requirements.txt")
    project.build_depends_on_requirements("requirements_dev.txt")

    project.set_property('dir_source_main_python', 'app')

    project.set_property('dir_source_unittest_python', 'tests')
    project.set_property('unittest_module_glob', '*_tests')
    project.set_property('coverage_break_build', False)

    project.set_property('flake8_include_test_sources', True)
    project.set_property('flake8_break_build', True)

    # F401: Unused import
    # E501: long time
    # E128: visual indent
    project.set_property('flake8_ignore', 'F401,E501,E128')
    project.set_property('flake8_max_line_length', 160)

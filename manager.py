#!/usr/bin/env python
# encoding: utf-8

"""
CLI for development

I usually use:
>>> pyhton.exe manager.py dev

Otherwise:
>>> python.exe manager.py --help

:Author: Fabio Scala <fabio.scala@gmail.com>
"""


import os

from app import create_app, db
import config
from flask.ext.script import Manager, Shell, Server, Command


app = create_app(os.getenv('FLASK_CONFIG') or config.CONFIG_TYPE)
manager = Manager(app)


@manager.command
def dev():
    app.run(host='127.0.0.1', port=5000, threaded=True, use_debugger=True, use_reloader=True)


def make_shell_context():
    return dict(app=app, db=db)

manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()

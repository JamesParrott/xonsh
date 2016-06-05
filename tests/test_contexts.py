"""Tests xonsh contexts."""
from nose.tools import assert_equal, assert_is, assert_is_not

from tools import (mock_xonsh_env, execer_setup, check_exec, check_eval,
    check_parse, skip_if)

from xonsh.contexts import Block

#
# helpers
#

def setup():
    execer_setup()


X1_WITH = ('x = 1\n'
           'with Block() as b:\n')
SIMPLE_WITH = 'with Block() as b:\n'
FUNC_WITH = ('x = 1\n'
             'def func():\n'
             '    y = 1\n'
             '    with Block() as b:\n'
             '{body}'
             '    y += 1\n'
             '    return b\n'
             'x += 1\n'
             'rtn = func()\n'
             'x += 1\n')

FUNC_OBSG = {'x': 3}
FUNC_OBSL = {'y': 1}

def block_checks_glb(name, glbs, body, obs=None):
    block = glbs[name]
    obs = obs or {}
    for k, v in obs.items():
        yield assert_equal, v, glbs[k]
    if isinstance(body, str):
        body = body.splitlines()
    yield assert_equal, body, block.lines
    yield assert_is, glbs, block.glbs
    yield assert_is, None, block.locs


def block_checks_func(name, glbs, body, obsg=None, obsl=None):
    block = glbs[name]
    obsg = obsg or {}
    for k, v in obsg.items():
        yield assert_equal, v, glbs[k]
    if isinstance(body, str):
        body = body.splitlines()
    yield assert_equal, body, block.lines
    yield assert_is, glbs, block.glbs
    # local context tests
    locs = block.locs
    yield assert_is_not, None, locs
    obsl = obsl or {}
    for k, v in obsl.items():
        yield assert_equal, v, locs[k]


#
# tests
#

def test_block_noexec():
    s = ('x = 1\n'
         'with Block():\n'
         '    x += 42\n')
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    assert_equal(1, glbs['x'])


def test_block_oneline():
    body = '    x += 42\n'
    s = X1_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, body, {'x': 1})


def test_block_manylines():
    body = ('    ![echo wow mom]\n'
            '# bad place for a comment\n'
            '    x += 42')
    s = X1_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, body, {'x': 1})


def test_block_leading_comment():
    # leading comments do not show up in block lines
    body = ('    # I am a leading comment\n'
            '    x += 42\n')
    s = X1_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, ['    x += 42'], {'x': 1})


def test_block_trailing_comment():
    # trailing comments do not show up in block lines
    body = ('    x += 42\n'
            '    # I am a trailing comment\n')
    s = X1_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, ['    x += 42'], {'x': 1})


def test_block_trailing_line_continuation():
    body = ('    x += \\\n'
            '         42\n')
    s = X1_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, body, {'x': 1})


def test_block_trailing_close_paren():
    body = ('    x += int("42"\n'
            '             )\n')
    s = X1_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, body, {'x': 1})


def test_block_trailing_close_many():
    body = ('    x = {None: [int("42"\n'
            '                    )\n'
            '                ]\n'
            '         }\n')
    s = SIMPLE_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, body)


def test_block_trailing_triple_string():
    body = ('    x = """This\n'
            'is\n'
            '"probably"\n'
            '\'not\' what I meant.\n'
            '"""\n')
    s = SIMPLE_WITH + body
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_glb('b', glbs, body)


def test_block_func_oneline():
    body = '        x += 42\n'
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, body, FUNC_OBSG, FUNC_OBSL)


def test_block_func_manylines():
    body = ('        ![echo wow mom]\n'
            '# bad place for a comment\n'
            '        x += 42\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, body, FUNC_OBSG, FUNC_OBSL)


def test_block_func_leading_comment():
    # leading comments do not show up in block lines
    body = ('        # I am a leading comment\n'
            '        x += 42\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, '        x += 42\n',
                                 FUNC_OBSG, FUNC_OBSL)


def test_block_func_trailing_comment():
    # trailing comments do not show up in block lines
    body = ('        x += 42\n'
            '        # I am a trailing comment\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, '        x += 42\n',
                                 FUNC_OBSG, FUNC_OBSL)


def test_blockfunc__trailing_line_continuation():
    body = ('        x += \\\n'
            '             42\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, body, FUNC_OBSG, FUNC_OBSL)


def test_block_func_trailing_close_paren():
    body = ('        x += int("42"\n'
            '                 )\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, body, FUNC_OBSG, FUNC_OBSL)


def test_block_func_trailing_close_many():
    body = ('        x = {None: [int("42"\n'
            '                        )\n'
            '                    ]\n'
            '             }\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, body, FUNC_OBSG, FUNC_OBSL)


def test_block_func_trailing_triple_string():
    body = ('        x = """This\n'
            'is\n'
            '"probably"\n'
            '\'not\' what I meant.\n'
            '"""\n')
    s = FUNC_WITH.format(body=body)
    glbs = {'Block': Block}
    check_exec(s, glbs=glbs, locs=None)
    yield from block_checks_func('rtn', glbs, body, FUNC_OBSG, FUNC_OBSL)

from __future__ import absolute_import, print_function

import os
import unittest
from nose.tools import raises
from nose.config import Config
from nose.plugins.doctests import Doctest
from nose.plugins.manager import PluginManager
from nose.plugins.skip import Skip, SkipTest
from rudolf import *  # noqa

BASE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__)))


class TestXterm(unittest.TestCase):
    def test_ok(self):
        self.assertEquals(xterm_from_rgb_string("000000"), 16)
        self.assertEquals(xterm_from_rgb_string("FF0000"), 196)

    @raises(ValueError)
    def test_ko_imcomplete(self):
        xterm_from_rgb_string("0000")

    @raises(ValueError)
    def test_ko_string(self):
        xterm_from_rgb_string("blah")


class TestCubeVals(unittest.TestCase):
    def test_ok(self):
        self.assertEquals(cube_vals(CUBE_START), (0, 0, 0))
        self.assertEquals(cube_vals(GRAY_START - 1), (5, 5, 5))

    @raises(AssertionError)
    def test_ko_lower(self):
        cube_vals(15)

    @raises(AssertionError)
    def test_ko_over(self):
        cube_vals(232)


class TestRgbFromXterm(unittest.TestCase):
    def test_ok(self):
        self.assertEquals(rgb_from_xterm(CUBE_START), (0, 0, 0))
        self.assertEquals(rgb_from_xterm(TABLE_END - 1), (238, 238, 238))

    @raises(AssertionError)
    def test_ko_lower(self):
        rgb_from_xterm(15)

    @raises(AssertionError)
    def test_ko_upper(self):
        rgb_from_xterm(256)


class TestXterm256Color(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(Xterm256Color(196).terminal_code(), '\x1b[38;5;196m')


class DictComparision(unittest.TestCase):
    def assertEquals(self, *args, **kwargs):
        args = [a.__dict__ for a in args]
        return super(DictComparision, self).assertEquals(*args, **kwargs)


class TestParseColor(DictComparision):
    def test_ok_ansi_colors(self):
        # Names for the 16 ANSI colours
        self.assertEquals(parse_color("black"), Ansi16Color(0, None))
        self.assertEquals(parse_color("red"), Ansi16Color(1, None))
        self.assertEquals(parse_color("darkred"), Ansi16Color(1, False))
        self.assertEquals(parse_color("lightred"), Ansi16Color(1, True))
        self.assertEquals(parse_color("brightred"), Ansi16Color(1, True))
        self.assertEquals(parse_color("boldred"), Ansi16Color(1, True))

    def test_ok_rgb_colors(self):

        # RGB colours
        self.assertEquals(parse_color("rgb(ff0000)"), Xterm256Color(196))
        self.assertEquals(parse_color("rgb(FF0000)"), Xterm256Color(196))

    def test_ok_xterm_color_codes(self):
        # xterm colour codes
        self.assertEquals(parse_color("0"), Xterm256Color(0))
        self.assertEquals(parse_color("140"), Xterm256Color(140))

    # Bad colours
    @raises(ValueError)
    def test_ko_moored(self):
        parse_color("moored")

    @raises(ValueError)
    def test_ko_boldpink(self):
        parse_color("boldpink")

    @raises(ValueError)
    def test_ko_256(self):
        parse_color("256")

    @raises(ValueError)
    def test_ko_minus_one(self):
        parse_color("-1")

    @raises(ValueError)
    def test_ko_no_rgb_func(self):
        parse_color("ff0000")

    @raises(ValueError)
    def test_ko_bad_rgb_func(self):
        parse_color("rgb(fg0000)")

    @raises(ValueError)
    def test_ko_long_rgb_func(self):
        parse_color("rgb(ff0000f)")

    @raises(ValueError)
    def test_ko_short_rgb_func(self):
        parse_color("rgb(0000)")


class TestRelativeLocations(unittest.TestCase):
    def test_ok(self):
        self.assertEquals(relative_location("/a/b/", "/a/b/c"),  'c')
        self.assertEquals(relative_location("a/b", "a/b/c/d"), 'c/d')
        self.assertEquals(relative_location("/z", "/a/b"), '../a/b')

        relative = relative_location("/a/b/", "a/b/c")
        self.assertEquals(relative, "../.." + BASE_PATH + "/a/b/c")

        nr_dirs_up_to_root = os.path.join(BASE_PATH, "a", "b").count(os.sep)
        expected = "/".join([".."] * nr_dirs_up_to_root) + "/a/b/c/d"
        self.assertEquals(relative_location("a/b", "/a/b/c/d/"), expected)


class TestParseColorScheme(DictComparision):
    def test_ok(self):
        colors = parse_colorscheme("fail=red,pass=rgb(00ff00),error=40")
        scheme = {
            'error': Xterm256Color(40),
            'fail': Ansi16Color(1, None),
            'pass': Xterm256Color(46),
        }
        for name, color in sorted(colors.items()):
            self.assertEquals(scheme[name], color)

    @raises(ValueError)
    def test_ko_imporperlyConfigured(self):
        parse_colorscheme("fail:red,pass=green")

    @raises(ValueError)
    def test_ko_smap(self):
        parse_colorscheme("fail=spam")

    @raises(ValueError)
    def test_ko_format(self):
        parse_colorscheme("fail=")


class TestRudolf(object):
    """ integration tests. """

    def _run(self, *args, **kwargs):
        env = kwargs.pop('env', {})
        plugins = kwargs.pop('plugins', [TestColorOutputPlugin(), Skip()])

        options = {
            'argv': ['nosetests', '--with-color'] + list(args),
            'config': Config(env=env, plugins=PluginManager(plugins=plugins))
        }
        options.update(kwargs)
        nose.core.run(**options)

    def test_rudolf_dotted(self):
        self._run("test:DumpResults")

    def test_rudolf_verbose(self):
        self._run("-v", "test:DumpResults")

    def test_rudolf_againts_plugins(self):
        self._run('-v', '--with-spam', 'test:DumpResults',
                  plugins=[TestColorOutputPlugin(), Skip(), SpamPlugin()])

    def test_rudolf_doctests(self):
        self._run('-v', '--with-doctest', 'test:DoctestResults',
                  plugins=[TestColorOutputPlugin(), Skip(), Doctest()])


class TestColorfulOutputFormatter(ColorfulOutputFormatter):
    __test__ = False

    def _format_seconds(self, n_seconds, normal="normal"):
        return "%s seconds" % (self.colorize("number", "...", normal))


class TestColorOutputPlugin(ColorOutputPlugin):
    __test__ = False

    formatter_class = TestColorfulOutputFormatter
    clean_tracebacks = True

    def __init__(self):
        ColorOutputPlugin.__init__(self)
        self.base_dir = BASE_PATH


class SpamPlugin(nose.plugins.Plugin):
    name = 'spam'
    score = TestColorOutputPlugin.score - 1

    def setOutputStream(self, stream):
        self.stream = stream

    def startTest(self, test):
        self.stream.write('spam')


class DumpResults(object):
    def test_good(self):
        assert True

    def test_bad(self):
        assert False, 'Failure example, to show the colors.'

    def test_boom(self):
        raise ValueError('Example of Really bad bad Wolf, I mean Error.')

    def test_skip(self):
        raise SkipTest('Example of Skip test.')


class DoctestResults(object):
    """
    Testing doctests.
    >>> True
    True
    >>> False, 'Failure example.'
    True
    >>> raise ValueError('Error example.')
    True
    >>> print('Ferpect Exmaple')
    ... # doctest: +REPORT_NDIFF
    Perfect Example
    """

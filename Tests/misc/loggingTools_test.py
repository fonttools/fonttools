from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.loggingTools import (
    LevelFormatter,
    Timer,
    configLogger,
    ChannelsFilter,
    LogMixin,
    StderrHandler,
    LastResortLogger,
    _resetExistingLoggers,
)
import logging
import textwrap
import time
import re
import sys
import pytest


def logger_name_generator():
    basename = "fontTools.test#"
    num = 1
    while True:
        yield basename+str(num)
        num += 1

unique_logger_name = logger_name_generator()


@pytest.fixture
def logger():
    log = logging.getLogger(next(unique_logger_name))
    configLogger(logger=log, level="DEBUG", stream=StringIO())
    return log


def test_LevelFormatter():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    formatter = LevelFormatter(
        fmt={
            '*':     '[%(levelname)s] %(message)s',
            'DEBUG': '%(name)s [%(levelname)s] %(message)s',
            'INFO':  '%(message)s',
        })
    handler.setFormatter(formatter)
    name = next(unique_logger_name)
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    log.debug("this uses a custom format string")
    log.info("this also uses a custom format string")
    log.warning("this one uses the default format string")

    assert stream.getvalue() == textwrap.dedent("""\
        %s [DEBUG] this uses a custom format string
        this also uses a custom format string
        [WARNING] this one uses the default format string
        """ % name)


class TimerTest(object):

    def test_split(self):
        timer = Timer()
        time.sleep(0.01)
        fist_lap =  timer.split()
        assert timer.elapsed == fist_lap
        time.sleep(0.1)
        second_lap = timer.split()
        assert second_lap > fist_lap
        assert timer.elapsed == second_lap

    def test_time(self):
        timer = Timer()
        time.sleep(0.01)
        overall_time = timer.time()
        assert overall_time > 0

    def test_context_manager(self):
        with Timer() as t:
            time.sleep(0.01)
        assert t.elapsed > 0

    def test_using_logger(self, logger):
        with Timer(logger, 'do something'):
            time.sleep(0.01)

        assert re.match(
            r"Took [0-9]\.[0-9]{3}s to do something",
            logger.handlers[0].stream.getvalue())

    def test_using_logger_calling_instance(self, logger):
        timer = Timer(logger)
        with timer():
            time.sleep(0.01)

        assert re.match(
            r"elapsed time: [0-9]\.[0-9]{3}s",
            logger.handlers[0].stream.getvalue())

        # do it again but with custom level
        with timer('redo it', level=logging.WARNING):
            time.sleep(0.02)

        assert re.search(
            r"WARNING: Took [0-9]\.[0-9]{3}s to redo it",
            logger.handlers[0].stream.getvalue())

    def test_function_decorator(self, logger):
        timer = Timer(logger)

        @timer()
        def test1():
            time.sleep(0.01)
        @timer('run test 2', level=logging.INFO)
        def test2():
            time.sleep(0.02)

        test1()

        assert re.match(
            r"Took [0-9]\.[0-9]{3}s to run 'test1'",
            logger.handlers[0].stream.getvalue())

        test2()

        assert re.search(
            r"Took [0-9]\.[0-9]{3}s to run test 2",
            logger.handlers[0].stream.getvalue())


def test_ChannelsFilter(logger):
    n = logger.name
    filtr = ChannelsFilter(n+".A.B", n+".C.D")
    handler = logger.handlers[0]
    handler.addFilter(filtr)
    stream = handler.stream

    logging.getLogger(n+".A.B").debug('this record passes through')
    assert 'this record passes through' in stream.getvalue()

    logging.getLogger(n+'.A.B.C').debug('records from children also pass')
    assert 'records from children also pass' in stream.getvalue()

    logging.getLogger(n+'.C.D').debug('this one as well')
    assert 'this one as well' in stream.getvalue()

    logging.getLogger(n+'.A.B.').debug('also this one')
    assert 'also this one' in stream.getvalue()

    before = stream.getvalue()
    logging.getLogger(n+'.A.F').debug('but this one does not!')
    assert before == stream.getvalue()

    logging.getLogger(n+'.C.DE').debug('neither this one!')
    assert before == stream.getvalue()


def test_LogMixin():

    class Base(object):
        pass

    class A(LogMixin, Base):
        pass

    class B(A):
        pass

    a = A()
    b = B()

    assert hasattr(a, 'log')
    assert hasattr(b, 'log')
    assert isinstance(a.log, logging.Logger)
    assert isinstance(b.log, logging.Logger)
    assert a.log.name == "loggingTools_test.A"
    assert b.log.name == "loggingTools_test.B"


@pytest.mark.skipif(sys.version_info[:2] > (2, 7), reason="only for python2.7")
@pytest.mark.parametrize(
    "reset", [True, False], ids=["reset", "no-reset"]
)
def test_LastResortLogger(reset, capsys, caplog):
    current = logging.getLoggerClass()
    msg = "The quick brown fox jumps over the lazy dog"
    try:
        if reset:
            _resetExistingLoggers()
        else:
            caplog.set_level(logging.ERROR, logger="myCustomLogger")
        logging.lastResort = StderrHandler(logging.WARNING)
        logging.setLoggerClass(LastResortLogger)
        logger = logging.getLogger("myCustomLogger")
        logger.error(msg)
    finally:
        del logging.lastResort
        logging.setLoggerClass(current)

    captured = capsys.readouterr()
    if reset:
        assert msg in captured.err
        msg not in caplog.text
    else:
        msg in caplog.text
        msg not in captured.err

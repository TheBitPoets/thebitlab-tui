"""Linux PTY integration evidence for the private POSIX input backend."""

from __future__ import annotations

import copy
import os
import sys

import pytest


pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Linux PTY only"
)


def test_linux_pty_preserves_prequeued_input_and_restores_exact_attributes() -> None:
    import dataclasses
    import pty
    import termios

    from thebitlab_tui import Key, KeyEvent, KeyReader
    from thebitlab_tui import terminal
    from thebitlab_tui._posix_input import _PosixInputBackend, _default_ops

    master, slave = pty.openpty()
    stream = os.fdopen(os.dup(slave), "rb", buffering=0)
    original = copy.deepcopy(termios.tcgetattr(slave))
    try:
        os.write(master, b"x\n")
        backend = _PosixInputBackend(
            0.02, ops=dataclasses.replace(_default_ops(), stream=stream)
        )
        old_factory = terminal._create_backend
        terminal._create_backend = lambda escape_timeout: backend
        try:
            with KeyReader() as reader:
                active = termios.tcgetattr(slave)
                expected = copy.deepcopy(original)
                expected[3] &= ~(termios.ECHO | termios.ICANON)
                expected[6][termios.VMIN] = active[6][termios.VMIN]
                expected[6][termios.VTIME] = active[6][termios.VTIME]
                assert active == expected
                assert active[6][termios.VMIN] in (1, b"\x01")
                assert active[6][termios.VTIME] in (0, b"\x00")
                assert reader.read(0.5) == KeyEvent(Key.CHARACTER, "x")
                assert reader.read(0.5) == KeyEvent(Key.ENTER)
        finally:
            terminal._create_backend = old_factory
        assert termios.tcgetattr(slave) == original
    finally:
        try:
            termios.tcsetattr(slave, termios.TCSANOW, original)
        finally:
            stream.close()
            os.close(master)
            os.close(slave)


@pytest.mark.parametrize(
    "body_error", [RuntimeError("body failed"), KeyboardInterrupt()]
)
def test_linux_pty_restores_exact_attributes_after_body_error(
    body_error: BaseException,
) -> None:
    import dataclasses
    import pty
    import termios

    from thebitlab_tui import KeyReader
    from thebitlab_tui import terminal
    from thebitlab_tui._posix_input import _PosixInputBackend, _default_ops

    master, slave = pty.openpty()
    stream = os.fdopen(os.dup(slave), "rb", buffering=0)
    original = copy.deepcopy(termios.tcgetattr(slave))
    backend = _PosixInputBackend(
        0.02, ops=dataclasses.replace(_default_ops(), stream=stream)
    )
    old_factory = terminal._create_backend
    terminal._create_backend = lambda escape_timeout: backend
    try:
        with pytest.raises(type(body_error)):
            with KeyReader():
                raise body_error
        assert termios.tcgetattr(slave) == original
    finally:
        terminal._create_backend = old_factory
        try:
            termios.tcsetattr(slave, termios.TCSANOW, original)
        finally:
            stream.close()
            os.close(master)
            os.close(slave)


def test_linux_pty_restores_exact_attributes_after_read_error() -> None:
    import dataclasses
    import pty
    import termios

    from thebitlab_tui import KeyReader
    from thebitlab_tui import terminal
    from thebitlab_tui._posix_input import _PosixInputBackend, _default_ops

    master, slave = pty.openpty()
    stream = os.fdopen(os.dup(slave), "rb", buffering=0)
    original = copy.deepcopy(termios.tcgetattr(slave))

    def fail_read(fd: int, size: int) -> bytes:
        raise OSError("read failed")

    ops = dataclasses.replace(_default_ops(), stream=stream, read=fail_read)
    backend = _PosixInputBackend(0.02, ops=ops)
    old_factory = terminal._create_backend
    terminal._create_backend = lambda escape_timeout: backend
    try:
        with pytest.raises(OSError, match="read failed"):
            with KeyReader() as reader:
                os.write(master, b"x")
                reader.read(0.5)
        assert termios.tcgetattr(slave) == original
    finally:
        terminal._create_backend = old_factory
        try:
            termios.tcsetattr(slave, termios.TCSANOW, original)
        finally:
            stream.close()
            os.close(master)
            os.close(slave)


def test_linux_pty_real_hangup_latches_eof_and_reports_restore_failure() -> None:
    import dataclasses
    import pty
    import termios
    import time

    from thebitlab_tui._posix_input import _PosixInputBackend, _default_ops

    master, slave = pty.openpty()
    stream = os.fdopen(os.dup(slave), "rb", buffering=0)
    backend = _PosixInputBackend(
        0.02, ops=dataclasses.replace(_default_ops(), stream=stream)
    )
    try:
        backend.activate()
        os.close(master)
        master = -1
        with pytest.raises(EOFError):
            backend.read(time.monotonic() + 0.5)
        with pytest.raises(EOFError):
            backend.read(time.monotonic() + 0.5)
        with pytest.raises(termios.error):
            backend.restore()
    finally:
        stream.close()
        if master >= 0:
            os.close(master)
        os.close(slave)

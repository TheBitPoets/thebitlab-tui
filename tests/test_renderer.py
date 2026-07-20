from io import StringIO

import thebitlab_tui.renderer as renderer
from thebitlab_tui import (
    Label,
    ResizeWatcher,
    TerminalSize,
    render,
    render_terminal,
    supports_color,
)


def test_renderer_returns_text_and_never_prints(capsys) -> None:
    assert render(Label("hello"), 7, 1) == "hello  "
    assert capsys.readouterr().out == ""


def test_terminal_renderer_recalculates_size_each_frame(monkeypatch) -> None:
    sizes = iter([TerminalSize(5, 1), TerminalSize(8, 1)])
    monkeypatch.setattr(renderer, "get_terminal_size", lambda fallback: next(sizes))
    assert render_terminal(Label("abcdefgh")) == ["ab..."]
    assert render_terminal(Label("abcdefgh")) == ["abcdefgh"]


def test_resize_watcher_reports_only_changes() -> None:
    sizes = iter([TerminalSize(80, 24), TerminalSize(80, 24), TerminalSize(100, 30)])
    watcher = ResizeWatcher(lambda: next(sizes))
    assert watcher.poll() == TerminalSize(80, 24)
    assert watcher.poll() is None
    assert watcher.poll() == TerminalSize(100, 30)


class _TTY(StringIO):
    def isatty(self) -> bool:
        return True


def test_linux_and_windows_color_policies() -> None:
    stream = _TTY()
    assert supports_color(stream=stream, environ={"TERM": "xterm"}, platform="linux")
    assert not supports_color(stream=stream, environ={}, platform="win32")
    assert supports_color(stream=stream, environ={"WT_SESSION": "1"}, platform="win32")


def test_no_color_flag_and_environment_override_platform() -> None:
    stream = _TTY()
    assert not supports_color(no_color=True, stream=stream, environ={}, platform="linux")
    assert not supports_color(stream=stream, environ={"NO_COLOR": "1"}, platform="win32")


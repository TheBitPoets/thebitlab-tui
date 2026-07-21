Phase 3 terminal input contracts
================================

Status
------

This design record is proposed in issue `#30
<https://github.com/TheBitPoets/thebitlab-tui/issues/30>`_ under parent issue `#24
<https://github.com/TheBitPoets/thebitlab-tui/issues/24>`_. It adds no implementation or public
export. The names and signatures below become approved only when the design pull request merges;
implementation remains split into later child issues and pull requests.

Goals and boundaries
--------------------

Phase 3 adds dependency-free Windows and Linux keyboard input while preserving the current
architecture:

- platform adapters normalize input into the existing ``KeyEvent`` model;
- the application owns commands, focus, selection, persistence, event dispatch, and redraw;
- the reader never prints, clears the screen, renders, installs an event loop, or starts a thread;
- ``ResizeWatcher`` remains independent and application-polled;
- unsupported modifier combinations always have an unmodified application command;
- redirected input is not silently reinterpreted as interactive keyboard input;
- terminal restoration is attempted on every Python control-flow path that leaves the context
  manager, with failures reported explicitly.

Mouse input, drag and drop, tmux-specific behavior, application integration, global hotkeys,
animation timing, and a library-owned event loop remain outside this phase.

Proposed public namespace
-------------------------

Phase 3 adds one public concrete facade and leaves ``Key`` and ``KeyEvent`` unchanged:

.. code-block:: python

   from thebitlab_tui import KeyReader

   with KeyReader(escape_timeout=0.05) as keys:
       event = keys.read(timeout=0.1)

The proposed shape is:

.. code-block:: python

   KeyReader(*, escape_timeout: float = 0.05)

   KeyReader.__enter__() -> Self

   KeyReader.read(timeout: float | None = None) -> KeyEvent | None

``KeyReader`` lives in ``thebitlab_tui.terminal``, is exported from ``thebitlab_tui``, and is
listed in ``thebitlab_tui.__all__`` by the implementation pull request. Platform backends and
decoders remain private modules. The facade is a single-use context manager. Construction validates
scalar arguments but has no terminal side effects. Its lifecycle is explicit:

.. list-table:: Reader lifecycle
   :header-rows: 1

   * - State
     - ``__enter__``
     - ``read``
   * - New
     - Activates the backend and changes the state to active.
     - Raises ``RuntimeError``.
   * - Active
     - Raises ``RuntimeError``; nested entry is not supported.
     - Reads at most one event.
   * - Exited
     - Raises ``RuntimeError``; an instance cannot be reused.
     - Raises ``RuntimeError``.

``__exit__`` restores any state owned by an active backend and permanently changes the facade to
exited, including when the context body or restoration raises. An attempted activation is also
single-use: if setup fails, restoration is attempted where necessary and the facade becomes exited.

``__enter__`` returns the same public facade instance, never a backend or proxy. After successful
restoration, ``__exit__`` returns ``False`` and never suppresses an exception raised by the context
body. A restoration failure follows the precedence rules below instead of returning normally.

There is no public protocol, abstract base class, backend factory, ``open`` method, or ``close``
method in the initial contract. Requiring ``with`` keeps the restoration boundary visible and
keeps the public surface small. Backend and clock/I/O injection points remain private test seams.

A reader returns at most one event per call. Complete later events remain in its private FIFO.
The object is not thread-safe or re-entrant, and concurrent readers for the same terminal are not
supported.

Timeout contract
----------------

``timeout`` and ``escape_timeout`` are seconds measured against ``time.monotonic()``. A read
``timeout`` follows these rules:

- ``timeout=None`` waits until one supported event, EOF, interruption, or OS error;
- ``timeout=0`` polls without sleeping;
- a positive finite timeout is a total deadline for the call;
- expiration without a complete supported event returns ``None``;
- negative, infinite, or NaN values raise ``ValueError``.

``escape_timeout`` has a deliberately narrower domain: it must be positive and finite. Zero,
negative, infinite, and NaN values raise ``ValueError`` at construction. Requiring a non-zero
ambiguity window makes decoding invariant when the same bytes are delivered in different chunks.

An event already buffered is returned immediately. Before declaring a deadline expired, a backend
checks for and drains input already queued by the OS that is needed to finish one logical event.
Polling therefore never sleeps but may consume all already-available units of an arrow sequence or
Unicode scalar. Unknown input and interrupted system calls do not restart a finite deadline.

Partial decoder state survives a timeout. ``None`` means only that no complete supported event was
available by the deadline; it never means EOF. Applications that also watch resize use a small
finite timeout, call ``ResizeWatcher.poll()``, update their own state, and decide whether to redraw.

Key normalization
-----------------

The portable guarantees remain deliberately narrow:

- arrows produce ``Key.UP``, ``Key.DOWN``, ``Key.LEFT``, or ``Key.RIGHT``;
- carriage return or line feed produces ``Key.ENTER``;
- an unambiguous Escape produces ``Key.ESCAPE``;
- horizontal tab produces ``Key.TAB``;
- a supported text scalar produces ``Key.CHARACTER`` with one-code-point ``character``;
- non-character events always use ``character=None``.

After semantic Enter, Tab, and Escape handling, a supported text scalar is defined exactly as a
Unicode scalar for which Python ``str.isprintable()`` returns ``True``. This includes ordinary
space and printable combining marks, but excludes C0/C1 controls, Delete, format controls such as
zero-width space, and every surrogate. The reader emits code points, not grapheme clusters, and
performs no normalization. A valid replacement-character scalar ``U+FFFD`` is printable and is
preserved when the terminal actually transmits it; malformed input never manufactures one.

A terminal, input method, or platform may not transmit every non-ASCII character. Both backends
apply the same scalar predicate and never emit a lone UTF-16 surrogate.

Modifier flags describe only information representable without guessing:

- POSIX reports ``alt=True`` for an Escape-prefixed supported text scalar completed within the
  Escape deadline, except the reserved ``[`` and ``O`` control-sequence prefixes, and
  ``ctrl=True`` for unambiguous Ctrl-letter control bytes;
- Windows reports modifier state only from the matching console input record;
- neither backend infers Shift from character case;
- on POSIX, Tab versus Ctrl+I, Enter versus Ctrl+M, and Escape versus Ctrl+[ are byte-identical and
  normalize to the semantic key with modifier flags ``False``;
- Windows virtual-key records preserve the distinction: physical Tab, Enter, and Escape remain
  semantic keys with reported modifiers, while Ctrl+I and Ctrl+M can be characters with
  ``ctrl=True``;
- Ctrl+C remains the normal process interruption and is never converted to ``KeyEvent``.

Other C0/C1 controls, function keys, Home/End, and unsupported sequences are consumed and ignored.
They do not expand ``Key`` with a speculative ``UNKNOWN`` member and do not become false application
characters. Applications must not require modifier combinations for a workflow because terminals
do not report every combination consistently across platforms.

POSIX backend
-------------

The POSIX backend uses the caller's interactive standard-input file descriptor. Activation:

1. obtains the descriptor and rejects a missing descriptor or non-TTY with
   ``io.UnsupportedOperation``;
2. saves an exact ``termios.tcgetattr()`` snapshot;
3. enters a conservative cbreak mode by clearing ``ECHO`` and ``ICANON`` and setting ``VMIN=1``
   and ``VTIME=0``;
4. applies and restores attributes with ``termios.TCSANOW`` so activation does not discard queued
   input.

The implementation does not rely on the return value of ``tty.setcbreak()``, which differs
between supported Python versions. It does not set ``O_NONBLOCK``. ``select.select()`` provides
readiness and deadlines; ``os.read()`` consumes available bytes. Cbreak deliberately preserves
signal processing, so Ctrl+C and other configured terminal signals retain their normal behavior.

Before changing terminal state, activation captures ``sys.stdin.encoding`` and validates its codec;
only a missing or empty value falls back to UTF-8. An unknown codec raises ``LookupError`` without
changing the terminal. A registered codec is supported only when every single byte from ``0x00``
through ``0x7f``, decoded independently and strictly from initial state, produces its identical
Unicode code point and no buffered state. An incompatible codec raises
``io.UnsupportedOperation`` before terminal mutation. This keeps the byte-level ASCII control
grammar valid while permitting normal ASCII-superset terminal encodings.

The private pure decoder uses the selected codec's strict incremental decoder. Malformed byte
sequences are consumed through the decoder-reported invalid span, reset the affected decoder
fragment, and emit no event; remaining bytes are processed again from initial decoder state so
valid following text remains decodable. Every split point in a multibyte character or control
sequence must produce the same final event.

The decoder recognizes CSI ``ESC [ A/B/C/D`` and SS3 ``ESC O A/B/C/D`` arrows before applying the
printable-scalar rule. Its byte grammar is exact:

- after ``ESC [``, zero or more parameter bytes ``0x30`` through ``0x3f`` may be followed by zero
  or more intermediate bytes ``0x20`` through ``0x2f`` and exactly one final byte ``0x40`` through
  ``0x7e``;
- after ``ESC O``, exactly one final byte ``0x40`` through ``0x7e`` completes the SS3 sequence;
- only final ``A``, ``B``, ``C``, or ``D`` with no CSI parameter or intermediate bytes maps to an
  arrow; every other syntactically complete sequence is consumed as unknown;
- a byte outside the allowed position consumes the buffered control fragment including that byte
  as malformed; the next byte starts normal decoding and is not swallowed;
- the private length bound is checked after each byte is appended. Exceeding it consumes the whole
  buffered fragment including the byte that crossed the bound; the exact bound remains private.

Unambiguous Ctrl-letter bytes ``0x01`` through ``0x1a`` produce the matching lowercase
``Key.CHARACTER`` with ``ctrl=True``, except Tab, line feed, carriage return, Escape, and Ctrl+C.
The semantic controls retain their mappings; byte ``0x03`` is always consumed so Ctrl+C can never
become an event even if the terminal's interrupt character was remapped or disabled.

Escape is inherently ambiguous on a byte stream. A lone ``ESC`` becomes ``Key.ESCAPE`` only after
``escape_timeout``. If the caller's deadline expires first, ``read`` returns ``None`` and keeps the
pending Escape. Decoder priority and replay are deterministic:

- ``ESC [`` and ``ESC O`` start the supported control-sequence grammar;
- ``ESC`` plus one complete supported text scalar before the Escape deadline always produces that
  character with ``alt=True``, except that ``[`` and ``O`` are reserved by the control grammar;
- a second ``ESC`` completes the first as ``Key.ESCAPE`` and starts a fresh pending Escape;
- a semantic control such as Tab or Enter completes the first as ``Key.ESCAPE`` and is replayed as
  the next logical input unit;
- a complete unsupported control sequence, an incomplete CSI/SS3 sequence, or an incomplete
  Escape-prefixed multibyte text scalar at its Escape deadline is consumed as unknown and is never
  replayed as application commands.

The private control-sequence buffer is bounded. Reaching the bound consumes the sequence as
unknown. These outcomes depend on bytes and monotonic deadlines, not on how reads split the bytes.

An empty ``os.read()`` result latches EOF. Already-complete queued events are returned first, then
``read`` raises ``EOFError``; subsequent reads raise immediately. Incomplete text or control
fragments are discarded at EOF.

Windows backend
---------------

The Windows backend uses standard-library ``ctypes`` bindings to the narrow console APIs needed by
the contract: ``GetConsoleMode``, ``WaitForSingleObject``, and ``ReadConsoleInputW``. It does not use
``select()``, which supports sockets rather than console handles on Windows, and it does not use
``msvcrt.getwch()`` because ``U+00E0`` is indistinguishable there from the documented extended-key
prefix. Redirected input or a handle that is not a console raises ``io.UnsupportedOperation``.

The private backend borrows the standard-input handle obtained through
``msvcrt.get_osfhandle(sys.stdin.fileno())`` and never closes it. Activation reads but does not
change the input mode. ``ENABLE_PROCESSED_INPUT`` must already be enabled so Ctrl+C retains the
normal console interruption behavior; otherwise activation raises ``io.UnsupportedOperation``.
The backend never installs a signal handler or mutates console mode, so context exit has no Windows
console state to restore.

``WaitForSingleObject`` applies the common blocking, polling, and monotonic-deadline policy to the
console handle. Even an unbounded read uses bounded private waits so Python can regularly observe a
pending ``KeyboardInterrupt``. Once signalled, ``ReadConsoleInputW`` drains bounded batches of
queued records. A failed wait or read raises ``OSError``. Ignored records do not reset the original
deadline. Non-key records and key-up records are consumed and ignored without becoming false
commands. Per the Win32 contract, a successful read always contains at least one record; a
zero-record success is not part of the backend contract.

Before normalizing a key-down ``KEY_EVENT_RECORD``, the backend consumes synthetic Ctrl+C when Ctrl
is reported, the virtual key is C, and ``UnicodeChar`` is NUL, ETX, ``c``, or ``C``. A distinct
printable scalar remains text even when Windows also reports Ctrl and Right Alt for an AltGr
combination. All remaining records use this exact priority:

1. virtual-key codes map arrows, Enter, Escape, and Tab;
2. a text or paste record with virtual-key zero and ``UnicodeChar`` CR, LF, Tab, or Escape maps to
   the corresponding semantic key;
3. a printable ``UnicodeChar`` maps to ``Key.CHARACTER``;
4. Ctrl plus virtual-key A through Z derives a lowercase character only when ``UnicodeChar`` is
   NUL or the matching C0 code ``0x01`` through ``0x1a``; synthetic Ctrl+C is ignored.

``dwControlKeyState`` supplies Shift, Alt, and Ctrl flags exactly as reported; lock and enhanced-key
bits are ignored, and the backend does not infer a modifier from case. Printable text takes
priority over Ctrl-letter derivation so an AltGr-style record preserves its transmitted scalar.
The earlier virtual-key rules still distinguish physical Ctrl+I and Ctrl+M from Tab and Enter while
retaining semantic paste controls. Function keys, navigation keys outside the portable set,
dead-key records with no printable scalar, and other unsupported records are consumed.

A positive ``wRepeatCount`` represents that many identical logical events and is retained as
private run-length state so each public read still returns one event. A zero repeat is malformed and
is consumed. ``UnicodeChar`` is one UTF-16 code unit: a high surrogate remains private across calls
until a following low surrogate with matching relevant modifiers and repeat count completes one
Python scalar. Otherwise the pending high surrogate is discarded and a non-low current record is
processed normally. Lone low surrogates are consumed, and no surrogate reaches ``KeyEvent``.

Errors and restoration
----------------------

The initial contract uses standard exceptions rather than adding a public exception hierarchy:

- unsupported platform, unavailable descriptor, redirected input, or non-interactive input raises
  ``io.UnsupportedOperation``;
- POSIX EOF raises and latches ``EOFError``; the Windows console-record backend has no EOF result;
- setup, readiness, read, and restoration failures propagate as ``OSError``;
- an unknown POSIX input codec raises ``LookupError`` and a registered but ASCII-incompatible
  codec raises ``io.UnsupportedOperation``, both before terminal mutation;
- invalid timeouts raise ``ValueError``;
- invalid lifecycle use raises ``RuntimeError``;
- ``KeyboardInterrupt`` and ``SystemExit`` propagate.

If POSIX activation fails after a state snapshot, the backend attempts restoration before
re-raising. Context exit restores the exact saved attributes after normal completion and every
unwinding Python exception. A restoration failure on normal exit raises ``OSError``. If the body
already raised, its exception remains primary and the restoration failure is attached as a note
when supported rather than replacing it. The same precedence applies when activation and its
compensating restoration both fail: the activation error remains primary, the restoration error is
attached as a note, and the facade remains exited.

The library cannot restore state after ``SIGKILL``, ``os._exit()``, interpreter or process crash,
or a terminating signal that does not unwind Python. It installs no ``atexit`` or signal handler;
applications own broader process shutdown policy. The input descriptor must remain open for the
reader's lifetime.

Responsibility flow
-------------------

.. code-block:: text

   OS readiness/read
       -> private POSIX or Windows backend
       -> private deterministic decoder and FIFO
       -> KeyReader.read()
       -> KeyEvent
       -> application command and state update
       -> optional ResizeWatcher.poll()
       -> application-owned redraw

No step in the library binds a key to a command or mutates focus, selection, scrolling, modal
visibility, persisted layout, or application dictionaries.

Implementation slices
---------------------

After approval, implementation remains split into focused child issues:

1. shared ``KeyReader`` facade, timeout policy, pure decoder seams, and public documentation;
2. POSIX backend, decoder, PTY integration tests, and restoration tests;
3. Windows console-record backend, UTF-16 decoding, and injected platform tests;
4. cross-platform example, manual verification protocol, guide/image updates, and release
   closeout.

Exact internal module names, buffer limits, Windows wait-slice duration, and issue numbering remain
reversible until those slices are created. No implementation pull request may broaden the public
contract without returning to a design issue.

Required automated verification
-------------------------------

Pure and facade tests on all CI platforms must cover:

- every supported key and exact ``KeyEvent`` equality;
- FIFO ordering and one event per ``read``;
- every split point in POSIX CSI/SS3 and multibyte text, plus Windows surrogate pairs;
- lone Escape before and after its grace period, an outer timeout shorter than that period,
  deterministic Alt text, reserved Alt+``[``/``O``, repeated Escape, Escape before semantic
  controls, and an Escape-prefixed partial multibyte scalar at its deadline;
- the exact printable-scalar predicate, valid ``U+FFFD``, malformed input without replacement,
  codec selection, registered ASCII-incompatible rejection, and all required decoding split
  points;
- supported, unsupported-complete, malformed, and overlong CSI/SS3 sequences at every split point,
  without false characters and with following valid text preserved;
- ``None``, zero, positive, negative, infinite, and NaN read-timeout values;
- positive, zero, negative, infinite, and NaN ``escape_timeout`` constructor values;
- already-queued continuation units at a zero or expired deadline;
- EOF with complete events, empty state, and partial state;
- interrupted and failed operations without deadline reset;
- reading in each lifecycle state, nested entry, attempted reuse after exit, normal exit,
  exceptional exit, and setup failure.
- context entry returning the identical facade, body exceptions never being suppressed, and the
  documented restoration-error precedence.

POSIX-specific tests use injected operations plus a real Linux pseudo-terminal to verify the exact
cbreak flag delta, no activation flush, reads, EOF, and exact restoration after normal completion,
``KeyboardInterrupt``, read error, and body exception. Restore-failure behavior and retryable
internal state are deterministic unit tests. Injected decoding also verifies that byte ``0x03`` is
ignored when terminal signal processing does not intercept it. A setup failure followed by a
restoration failure verifies the primary exception, attached note, and permanently exited facade.

Windows-specific tests inject console-mode, wait, record-read, and clock operations. They cover the
``ctypes`` ABI, all four arrows, key-up and non-key records, unsupported virtual keys, semantic
virtual keys, virtual-key-zero CR/LF/Tab/Escape records, printable BMP text including ``U+00E0``,
an AltGr-style Ctrl+Right-Alt record with printable text, supplementary characters, record
modifiers, repeat counts, malformed surrogates, redirected input, processed-input rejection,
wait/read failures, Ctrl+C records with NUL, ETX, ``c``, and ``C``, and the absence of POSIX-only
imports. Windows CI also performs an import and console-policy smoke test.

Required manual verification
----------------------------

The release protocol covers a real Linux terminal plus Windows Terminal from PowerShell and
``cmd.exe``:

- arrows, Enter, Escape latency, Tab, ASCII text, and available non-ASCII input;
- fallback commands that do not require modifiers;
- Ctrl+C with a usable terminal after interruption;
- normal and exceptional context exit with echo and line input restored;
- finite-timeout reads interleaved with resize polling and stable redraw;
- redirected standard input producing the documented fallback error.

The design pull request changes no rendering, so it requires no new ASCII snapshot. The later
example must remain application-driven and must not become an event loop owned by the library.

Rejected alternatives
---------------------

One-shot ``read_key()``
   Rejected because fragmented Escape, UTF-8, extended-key, and surrogate state would require a
   hidden global buffer, while POSIX mode changes would repeat for every call.

Public ``PosixKeyReader`` and ``WindowsKeyReader`` classes
   Rejected because they make applications branch on the OS and expose backend details as stable
   API. One facade selects a private backend.

Public factory plus ``Protocol`` or abstract base class
   Rejected as premature extension machinery. Private injection is sufficient for deterministic
   tests; an additive public protocol remains possible if real third-party backends appear.

Public ``open``/``close`` lifecycle
   Rejected initially because it permits callers to forget restoration. A required context manager
   makes the lifetime explicit with fewer public methods.

``TimeoutError`` for ordinary polling
   Rejected because no-event is an expected result. ``None`` keeps polling concise while EOF and
   failures remain distinct exceptions.

Public ``Key.UNKNOWN``
   Rejected because callers cannot act portably on opaque platform codes. Unsupported sequences
   are consumed deterministically and new semantic keys can be added only for demonstrated needs.

POSIX raw mode or ``O_NONBLOCK``
   Rejected because they alter more terminal behavior than required. Conservative cbreak plus
   readiness polling preserves signal handling and avoids unspecified ``O_NONBLOCK`` interactions
   with ``VMIN``/``VTIME``.

Windows ``msvcrt.getwch()`` backend
   Rejected because its documented ``\xe0`` extended-key prefix collides with the valid printable
   character ``U+00E0``. A console-record backend distinguishes virtual keys from Unicode text and
   exposes modifier and repeat metadata without adding public API.

Common ``select()`` backend
   Rejected because Windows ``select`` accepts sockets, not console input handles.

Reader-owned resize, dispatch, redraw, or animation
   Rejected because those are application lifecycle and presentation concerns. Finite reads compose
   with the existing ``ResizeWatcher`` without coupling them.

Reversibility and compatibility
-------------------------------

Before the first implementation merge, ``KeyReader`` naming, constructor defaults, exception
choices, timeout details, and backend placement remain reversible through this design review. Once
released, the context-managed lifecycle, ``read`` signature, ``None`` timeout result, Escape grace,
cross-call buffering, standard exception categories, supported key mapping, and state-ownership
boundary become compatibility commitments.

Internal decoder structure, control-sequence buffer size, Windows polling interval, OS capability
probes, and recognition of additional unambiguous sequences remain private. Support for additional
semantic keys or reliably reported modifiers can be additive after a concrete consumer need and
focused tests. Existing rendering, widget, layout, terminal-size, resize, style, and event APIs
remain unchanged by this design pull request.

Primary references
------------------

- `Python 3.11 termios <https://docs.python.org/3.11/library/termios.html>`_;
- `Python 3.11 tty <https://docs.python.org/3.11/library/tty.html>`_ and `Python 3.13 tty
  <https://docs.python.org/3.13/library/tty.html>`_ for the supported-version return difference;
- `Python 3.11 select <https://docs.python.org/3.11/library/select.html>`_;
- `Python 3.11 msvcrt <https://docs.python.org/3.11/library/msvcrt.html>`_ for the rejected prefix
  interface;
- `Microsoft GetConsoleMode <https://learn.microsoft.com/en-us/windows/console/getconsolemode>`_;
- `Microsoft WaitForSingleObject
  <https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject>`_;
- `Microsoft ReadConsoleInput
  <https://learn.microsoft.com/en-us/windows/console/readconsoleinput>`_;
- `Microsoft KEY_EVENT_RECORD
  <https://learn.microsoft.com/en-us/windows/console/key-event-record-str>`_.

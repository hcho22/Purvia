"""Run one backend test module with guarded current-suite dependencies.

This provides deterministic local seams for the dependency paths exercised by
the discovered suite. It is not an OS-level egress sandbox for child processes.
"""

from __future__ import annotations

import runpy
import socket
import sys
from collections.abc import Callable
from typing import Any


class BlockedSocketPathError(OSError):
    pass


_NETWORK_FAMILIES = frozenset({socket.AF_INET, socket.AF_INET6})
_runtime_installed = False


def _install_local_tokenizer() -> None:
    import tiktoken

    encoding = tiktoken.Encoding(
        name="purvia_offline_bytes",
        pat_str=r"(?s).",
        mergeable_ranks={bytes([rank]): rank for rank in range(256)},
        special_tokens={},
    )
    original = tiktoken.get_encoding

    def get_encoding(encoding_name: str) -> tiktoken.Encoding:
        if encoding_name == "cl100k_base":
            return encoding
        return original(encoding_name)

    tiktoken.get_encoding = get_encoding


def _install_dotenv_guard() -> None:
    import dotenv

    dotenv.load_dotenv = lambda *args, **kwargs: False


def _blocked(operation: str) -> BlockedSocketPathError:
    return BlockedSocketPathError(
        f"offline test blocked Python socket path: socket.{operation}"
    )


def _guard_socket_method(name: str) -> None:
    original: Callable[..., Any] = getattr(socket.socket, name)

    def guarded(sock: socket.socket, *args: object, **kwargs: object) -> Any:
        if sock.family in _NETWORK_FAMILIES:
            raise _blocked(name)
        return original(sock, *args, **kwargs)

    setattr(socket.socket, name, guarded)


def _install_python_socket_guards() -> None:
    for name in ("bind", "connect", "connect_ex", "sendto"):
        _guard_socket_method(name)

    def blocked_create_connection(*args: object, **kwargs: object) -> socket.socket:
        raise _blocked("create_connection")

    def blocked_getaddrinfo(*args: object, **kwargs: object) -> list[object]:
        raise _blocked("getaddrinfo")

    socket.create_connection = blocked_create_connection
    socket.getaddrinfo = blocked_getaddrinfo  # type: ignore[assignment]


def install_offline_runtime() -> None:
    global _runtime_installed
    if _runtime_installed:
        return
    _install_local_tokenizer()
    _install_dotenv_guard()
    _install_python_socket_guards()
    _runtime_installed = True


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m backend.offline_test_bootstrap MODULE")
    module = sys.argv[1]
    install_offline_runtime()
    sys.argv = [module]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()

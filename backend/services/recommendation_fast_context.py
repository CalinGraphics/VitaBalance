"""Context pentru generare rapidă de recomandări (fără apeluri OpenFoodFacts)."""
from __future__ import annotations

from contextvars import ContextVar, Token

_fast_bulk_mode: ContextVar[bool] = ContextVar("recommendation_fast_bulk_mode", default=False)


def is_fast_bulk_mode() -> bool:
    return _fast_bulk_mode.get()


def enter_fast_bulk_mode() -> Token:
    return _fast_bulk_mode.set(True)


def exit_fast_bulk_mode(token: Token) -> None:
    _fast_bulk_mode.reset(token)

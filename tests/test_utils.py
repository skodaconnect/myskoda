"""Unit tests for utilities."""

import asyncio

import pytest

from myskoda.utils import async_debounce


@pytest.mark.asyncio
async def test_async_debounce() -> None:
    """Test the async_debounce decorator.

    Debounced function:
    - Only executes once when called multiple times within 'wait'.
    - Executes twice when called two times with a delay > 'wait'.
    """
    test_val = 0

    @async_debounce(wait=0.2)
    async def increment() -> None:
        nonlocal test_val
        test_val += 1

    await increment()
    await increment()
    await asyncio.sleep(0.1)
    await increment()
    await asyncio.sleep(0.3)
    assert test_val == 1

    await increment()
    await asyncio.sleep(0.3)
    await increment()
    await asyncio.sleep(0.3)
    assert test_val == 3  # noqa: PLR2004


@pytest.mark.asyncio
async def test_async_debounce_immediate() -> None:
    """Test the async_debounce decorator when immediate is True.

    Debounced function:
    - Executes immediatally the first time called.
    - Subsequent calls are executed (once) after wait time.
    """
    test_val = 0

    @async_debounce(wait=0.2, immediate=True)
    async def increment() -> None:
        nonlocal test_val
        test_val += 1

    await increment()
    assert test_val == 1
    await increment()
    await increment()
    await asyncio.sleep(0.3)
    assert test_val == 2  # noqa: PLR2004


@pytest.mark.asyncio
async def test_async_debounce_immediate_noqueue() -> None:
    """Test the async_debounce decorator when immediate is True and queue is False.

    Debounced function:
    - Executes immediatally the first time called.
    - Subsequent calls are executed (once) after wait time.
    """
    test_val = 0

    @async_debounce(wait=0.2, immediate=True, queue=False)
    async def increment() -> None:
        nonlocal test_val
        test_val += 1

    await increment()
    assert test_val == 1
    await increment()
    await increment()
    await asyncio.sleep(0.3)
    assert test_val == 1

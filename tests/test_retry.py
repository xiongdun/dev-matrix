import pytest
import asyncio

from app.utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    def test_retry_with_backoff_success(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_with_backoff_failure_then_success(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 3

    def test_retry_with_backoff_max_retries_exceeded(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fail()
        assert call_count == 3  # initial + 2 retries

    def test_retry_with_backoff_specific_exception(self):
        call_count = 0

        @retry_with_backoff(
            max_retries=1,
            base_delay=0.01,
            exceptions=(RuntimeError,),
        )
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retried")

        with pytest.raises(ValueError, match="Not retried"):
            raise_value_error()
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_backoff_async_success(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def async_success():
            nonlocal call_count
            call_count += 1
            return "async_success"

        result = await async_success()
        assert result == "async_success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_backoff_async_failure(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def async_always_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Async fails")

        with pytest.raises(RuntimeError, match="Async fails"):
            await async_always_fail()
        assert call_count == 3

    def test_retry_with_backoff_on_retry_callback(self):
        retry_events = []

        def on_retry(exc, attempt, delay):
            retry_events.append((str(exc), attempt, delay))

        call_count = 0

        @retry_with_backoff(
            max_retries=2,
            base_delay=0.01,
            on_retry=on_retry,
        )
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count}")
            return "success"

        result = fail_twice()
        assert result == "success"
        assert len(retry_events) == 2
        assert "Attempt 1" in retry_events[0][0]
        assert retry_events[0][1] == 1
        assert "Attempt 2" in retry_events[1][0]
        assert retry_events[1][1] == 2

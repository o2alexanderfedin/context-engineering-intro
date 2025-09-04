"""Rate limiting for API calls and actions."""

import asyncio
import random
import time


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """Token bucket rate limiter with daily limits."""

    def __init__(
        self,
        daily_limit: int = 50,
        search_delay: tuple[float, float] = (5.0, 15.0),
        apply_delay: tuple[float, float] = (10.0, 30.0),
    ):
        """Initialize rate limiter."""
        self.daily_limit = daily_limit
        self.search_delay = search_delay
        self.apply_delay = apply_delay
        self.applications_today = 0
        self.last_reset = time.time()
        self.last_action_time = 0

    async def acquire_search(self) -> None:
        """Acquire permission to perform a search."""
        await self._wait_for_cooldown()

        # Add human-like random delay
        delay = random.uniform(*self.search_delay)
        await asyncio.sleep(delay)

        self.last_action_time = time.time()

    async def acquire_apply(self) -> None:
        """Acquire permission to submit an application."""
        # Check daily limit
        self._check_daily_reset()

        if self.applications_today >= self.daily_limit:
            raise RateLimitExceeded(
                f"Daily application limit of {self.daily_limit} reached"
            )

        await self._wait_for_cooldown()

        # Add human-like random delay
        delay = random.uniform(*self.apply_delay)
        await asyncio.sleep(delay)

        self.applications_today += 1
        self.last_action_time = time.time()

    def _check_daily_reset(self) -> None:
        """Check if daily counter should reset."""
        current_time = time.time()
        # Reset after 24 hours
        if current_time - self.last_reset >= 86400:
            self.applications_today = 0
            self.last_reset = current_time

    async def _wait_for_cooldown(self) -> None:
        """Wait for minimum cooldown between actions."""
        min_cooldown = 2.0  # Minimum 2 seconds between any actions
        time_since_last = time.time() - self.last_action_time

        if time_since_last < min_cooldown:
            await asyncio.sleep(min_cooldown - time_since_last)

    def get_remaining_applications(self) -> int:
        """Get remaining applications for today."""
        self._check_daily_reset()
        return max(0, self.daily_limit - self.applications_today)

    def is_limit_reached(self) -> bool:
        """Check if daily limit is reached."""
        self._check_daily_reset()
        return self.applications_today >= self.daily_limit


class CircuitBreaker:
    """Circuit breaker for handling repeated failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def get_state(self) -> str:
        """Get current circuit breaker state."""
        return self.state

    def reset(self) -> None:
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"


class ExponentialBackoff:
    """Exponential backoff for retries."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize exponential backoff."""
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.attempt = 0

    async def wait(self) -> None:
        """Wait with exponential backoff."""
        delay = min(
            self.base_delay * (self.exponential_base ** self.attempt),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay = delay * (0.5 + random.random())

        await asyncio.sleep(delay)
        self.attempt += 1

    def reset(self) -> None:
        """Reset backoff counter."""
        self.attempt = 0

    async def retry(self, func, max_attempts: int = 5):
        """Retry function with exponential backoff."""
        last_exception = None

        for attempt in range(max_attempts):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    await self.wait()
                else:
                    break

        raise last_exception

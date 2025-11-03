"""User-Agent rotation for HTTP requests."""

import random
from typing import Optional

try:
    from fake_useragent import UserAgent

    FAKE_USERAGENT_AVAILABLE = True
except ImportError:
    FAKE_USERAGENT_AVAILABLE = False

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserAgentRotator:
    """Rotates User-Agent headers for requests."""

    def __init__(self, use_fake_useragent: bool = True):
        """Initialize User-Agent rotator.

        Args:
            use_fake_useragent: Whether to use fake-useragent library
        """
        self.use_fake_useragent = use_fake_useragent and FAKE_USERAGENT_AVAILABLE
        self.default_user_agents = settings.get_default_user_agents()
        self._user_agent = None

        if self.use_fake_useragent:
            try:
                self._user_agent = UserAgent()
                logger.info("user_agent_initialized", method="fake_useragent")
            except Exception as e:
                logger.warning(
                    "user_agent_fallback",
                    error=str(e),
                    fallback="default_user_agents",
                )
                self.use_fake_useragent = False

        if not self.use_fake_useragent:
            logger.info("user_agent_initialized", method="default_user_agents")

    def get_random(self) -> str:
        """Get a random User-Agent string.

        Returns:
            User-Agent string
        """
        if self.use_fake_useragent and self._user_agent:
            try:
                return self._user_agent.random
            except Exception as e:
                logger.warning(
                    "user_agent_error",
                    error=str(e),
                    fallback="default_user_agents",
                )
                # Fallback to default
                return random.choice(self.default_user_agents)

        return random.choice(self.default_user_agents)

    def get_chrome(self) -> str:
        """Get a Chrome User-Agent string.

        Returns:
            Chrome User-Agent string
        """
        if self.use_fake_useragent and self._user_agent:
            try:
                return self._user_agent.chrome
            except Exception:
                pass

        # Return first default (Chrome on Mac)
        return self.default_user_agents[0]

    def get_firefox(self) -> str:
        """Get a Firefox User-Agent string.

        Returns:
            Firefox User-Agent string
        """
        if self.use_fake_useragent and self._user_agent:
            try:
                return self._user_agent.firefox
            except Exception:
                pass

        # Return Firefox from defaults
        firefox_agents = [ua for ua in self.default_user_agents if "Firefox" in ua]
        if firefox_agents:
            return firefox_agents[0]

        return self.default_user_agents[0]

    def get_safari(self) -> str:
        """Get a Safari User-Agent string.

        Returns:
            Safari User-Agent string
        """
        if self.use_fake_useragent and self._user_agent:
            try:
                return self._user_agent.safari
            except Exception:
                pass

        # Return Safari from defaults
        safari_agents = [
            ua for ua in self.default_user_agents if "Safari" in ua and "Chrome" not in ua
        ]
        if safari_agents:
            return safari_agents[0]

        return self.default_user_agents[2]  # Safari on Mac


# Global User-Agent rotator instance
_user_agent_rotator: Optional[UserAgentRotator] = None


def get_user_agent_rotator() -> UserAgentRotator:
    """Get or create global User-Agent rotator instance.

    Returns:
        UserAgentRotator instance
    """
    global _user_agent_rotator
    if _user_agent_rotator is None:
        _user_agent_rotator = UserAgentRotator()
    return _user_agent_rotator


def get_random_user_agent() -> str:
    """Get a random User-Agent string (convenience function).

    Returns:
        User-Agent string
    """
    return get_user_agent_rotator().get_random()

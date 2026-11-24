import os
import json
from unittest.mock import patch
from boardroom_provider import ProviderError, deliberate, capabilities

def test_live_calls_disabled_by_default():
    with patch.dict(os.environ, {"BOARDROOM_LIVE_PROVIDER":"false"}):
        try: deliberate("system","user")
        except ProviderError as e: assert "disabled" in str(e)
        else: assert False

def test_limits_and_config():
    with patch.dict(os.environ, {"BOARDROOM_PROVIDER_TIMEOUT":"91"}):
        try: capabilities()
        except ValueError as e: assert "between 1 and 90" in str(e)
        else: assert False

def test_prompt_limit_requires_optin():
    with patch.dict(os.environ, {"BOARDROOM_LIVE_PROVIDER":"true","BOARDROOM_PROVIDER_BASE_URL":"http://localhost:11434/v1","BOARDROOM_PROVIDER_TIMEOUT":"5"}):
        try: deliberate("s","u"*20001)
        except ProviderError as e: assert "limit" in str(e)
        else: assert False

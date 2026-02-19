"""Telegram WebApp initData hash validation."""
import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote


def validate_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData and return parsed data.

    Raises ValueError if validation fails.
    """
    parsed = parse_qs(init_data, keep_blank_values=True)

    # Extract the hash
    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        raise ValueError("Missing hash in initData")

    # Build data-check-string: sorted key=value pairs (excluding hash)
    data_pairs = []
    for key, values in parsed.items():
        if key == "hash":
            continue
        data_pairs.append(f"{key}={values[0]}")

    data_pairs.sort()
    data_check_string = "\n".join(data_pairs)

    # Compute HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("initData hash mismatch")

    # Parse user object
    result = {}
    for key, values in parsed.items():
        result[key] = values[0]

    if "user" in result:
        try:
            result["user"] = json.loads(result["user"])
        except (json.JSONDecodeError, TypeError):
            pass

    return result


def extract_user_id(init_data: str, bot_token: str) -> int:
    """Validate initData and extract the Telegram user ID."""
    data = validate_init_data(init_data, bot_token)
    user = data.get("user")
    if isinstance(user, dict):
        uid = user.get("id")
        if uid is not None:
            return int(uid)
    raise ValueError("Could not extract user_id from initData")

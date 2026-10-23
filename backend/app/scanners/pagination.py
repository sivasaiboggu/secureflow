"""Bounded AWS page traversal with explicit incomplete-coverage failures."""
from typing import Any, Dict, Iterator
from app.scanners.base import ScanUnavailable


def aws_items(client, operation: str, result_key: str, *, request_token='NextToken',
              response_token='NextToken', truncated_key=None, max_pages=1000,
              **parameters) -> Iterator[Dict[str, Any]]:
    """Follow the operation's SDK token contract, preserving request filters.

    A repeated/missing continuation token or page bound fails the scan instead
    of silently publishing a partial clean result. Provider exceptions propagate
    to the scanner's safe failure handler. No synthetic fallback is provided.
    """
    seen = set()
    for _ in range(max_pages):
        page = getattr(client, operation)(**parameters)
        items = page.get(result_key, [])
        if not isinstance(items, list):
            raise ScanUnavailable('AWS returned an invalid resource page.')
        yield from items
        token = page.get(response_token)
        truncated = page.get(truncated_key, False) if truncated_key else bool(token)
        if not truncated:
            return
        if not isinstance(token, str) or not token or token in seen:
            raise ScanUnavailable('AWS pagination did not provide a valid next page. Coverage is incomplete.')
        seen.add(token)
        parameters[request_token] = token
    raise ScanUnavailable('AWS page limit reached. Coverage is incomplete.')

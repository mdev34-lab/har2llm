import json
import re
from collections import defaultdict
from urllib.parse import urlparse


def simplify_url(url):
    """Replaces IDs in URLs with templates to group similar requests."""
    parsed = urlparse(url)
    path = parsed.path
    # Replace UUIDs
    path = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{UUID}", path
    )
    # Replace numeric IDs
    path = re.sub(r"/\d+(?=/|$)", "/{ID}", path)
    return f"{parsed.netloc}{path}"


def summarize_json(data, max_list_len=1):
    """Summarizes JSON to show structure and sample values without bulk."""
    if isinstance(data, list):
        if len(data) == 0:
            return []
        sample = [summarize_json(data[0], max_list_len)]
        if len(data) > 1:
            sample.append(f"... (+{len(data) - 1} more items)")
        return sample
    elif isinstance(data, dict):
        return {k: summarize_json(v, max_list_len) for k, v in data.items()}
    elif isinstance(data, str) and len(data) > 300:
        return f"{data[:50]}...[Truncated {len(data)} chars]...{data[-10:]}"
    return data


def extract_essential_headers(headers):
    """Filters out boring browser headers."""
    boring = {
        "host",
        "connection",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "user-agent",
        "sec-ch-ua-platform",
        "accept",
        "sec-fetch-site",
        "sec-fetch-mode",
        "sec-fetch-dest",
        "referer",
        "accept-encoding",
        "accept-language",
        "priority",
        "content-length",
    }
    return {
        h["name"].lower(): h["value"]
        for h in headers
        if h["name"].lower() not in boring
    }


def process_har(input_file):
    with open(input_file, encoding="utf-8") as f:
        har = json.load(f)

    entries = har["log"]["entries"]

    # 1. Global Header Analysis
    header_counts = defaultdict(int)
    total_entries = len(entries)
    all_headers = []

    for e in entries:
        h = extract_essential_headers(e["request"].get("headers", []))
        all_headers.append(h)
        for k, v in h.items():
            header_counts[f"{k}: {v}"] += 1

    global_headers = [
        h for h, count in header_counts.items() if count > (total_entries * 0.8)
    ]

    # 2. Group and Compact Entries
    compact_log = []

    for i, entry in enumerate(entries):
        req = entry["request"]
        res = entry["response"]

        # Simplify Request
        url = req["url"]
        method = req["method"]

        # Headers (only those not in global)
        local_headers = {
            k: v
            for k, v in extract_essential_headers(req.get("headers", [])).items()
            if f"{k}: {v}" not in global_headers
        }

        # Request Body
        req_body = ""
        if "postData" in req and "text" in req["postData"]:
            try:
                body_json = json.loads(req["postData"]["text"])
                req_body = summarize_json(body_json)
            except Exception:
                req_body = req["postData"]["text"][:200]

        # Response Body
        res_body = ""
        if "content" in res and "text" in res["content"]:
            try:
                res_json = json.loads(res["content"]["text"])
                res_body = summarize_json(res_json)
            except Exception:
                res_body = "[Non-JSON or Large Blob]"

        entry_data = {
            "m": method,
            "u": url,
            "s": res.get("status"),
            "h": local_headers,
            "q": {p["name"]: p["value"] for p in req.get("queryString", [])},
            "req_b": req_body,
            "res_b": res_body,
        }

        # Check for duplication with previous entry (Sequence Compression)
        if (
            compact_log
            and compact_log[-1]["u"] == entry_data["u"]
            and compact_log[-1]["m"] == entry_data["m"]
        ):
            if "repeat" not in compact_log[-1]:
                compact_log[-1]["repeat"] = 1
            compact_log[-1]["repeat"] += 1
        else:
            compact_log.append(entry_data)

    # 3. Final String Building (The DSL)
    output = []
    output.append("# GLOBAL HEADERS (Common to 80%+ of requests)")
    for h in global_headers:
        output.append(f"  {h}")
    output.append("\n# REQUEST LOG")

    for e in compact_log:
        repeat_str = f" [Repeated {e['repeat']}x]" if "repeat" in e else ""
        output.append(f"## {e['m']} {e['u']}{repeat_str}")
        if e["q"]:
            output.append(f"  Query: {json.dumps(e['q'])}")
        if e["h"]:
            output.append(f"  Headers: {json.dumps(e['h'])}")
        if e["req_b"]:
            output.append(f"  Body: {json.dumps(e['req_b'])}")
        output.append(f"  <- Response {e['s']}: {json.dumps(e['res_b'])}")
        output.append("")

    return "\n".join(output)


# Execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python compact_har.py input.har output.txt")
    else:
        result = process_har(sys.argv[1])
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Compressed to {len(result.split())} words / {len(result)} chars")

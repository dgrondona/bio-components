"""Live figures from the GitHub API.

Note on languages: this reports the *count* of distinct languages, never a
byte-weighted ranking. GitHub's language API measures bytes checked into a repo,
which counts vendored dependencies as authored code -- on this account a single
coursework repo with a committed virtualenv contributes 24.7 MB of Python, 96%
of the whole footprint, which would render the author as a 97% Python developer
whose actual 137-file C# project shows up as 0.7%. A count is honest; a ranking
is not.
"""

import collections
import datetime
import json
import os
import re
import urllib.request

API = "https://api.github.com"


def _get(url, raw=False, token=None):
    h = {"User-Agent": "bio-components"}
    tok = token or os.environ.get("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return body if raw else json.loads(body)


def _contribution_days(user, years, token=None):
    days = {}
    for y in years:
        try:
            page = _get(f"https://github.com/users/{user}/contributions"
                        f"?from={y}-01-01&to={y}-12-31", raw=True, token=token)
        except Exception:
            continue
        for m in re.finditer(r'data-(date|level)="([^"]+)"[^>]*data-(date|level)="([^"]+)"', page):
            k1, v1, k2, v2 = m.groups()
            d = v1 if k1 == "date" else v2
            lvl = v2 if k1 == "date" else v1
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                days[d] = int(lvl)
    return days


def _year_total(user, year, token=None):
    try:
        page = _get(f"https://github.com/users/{user}/contributions"
                    f"?from={year}-01-01&to={year}-12-31", raw=True, token=token)
    except Exception:
        return None
    m = re.search(r"<h2[^>]*>\s*([\d,]+)\s*\n?\s*contribution", page, re.S)
    return int(m.group(1).replace(",", "")) if m else None


def refresh(data, token=None, today=None):
    """Update the `stats` block in `data` in place and return it."""
    user = data["identity"]["handle"]
    today = today or datetime.date.today()
    s = data["stats"]

    u = _get(f"{API}/users/{user}", token=token)
    repos = _get(f"{API}/users/{user}/repos?per_page=100", token=token)
    s["repositories"] = u["public_repos"]
    s["languages"] = len({r["language"] for r in repos if r["language"]})

    first = int(u["created_at"][:4])
    by_year, total = {}, 0
    for y in range(first, today.year + 1):
        v = _year_total(user, y, token)
        if v is not None:
            by_year[str(y)] = v
            total += v
    if by_year:
        s["by_year"] = by_year
        s["contributions_total"] = total
        s["since"] = first

    days = _contribution_days(user, (today.year - 1, today.year), token)
    if days:
        weeks = collections.OrderedDict()
        d = today - datetime.timedelta(weeks=52)
        while d <= today:
            wk = (d - datetime.timedelta(days=d.weekday())).isoformat()
            weeks[wk] = weeks.get(wk, 0) + days.get(d.isoformat(), 0)
            d += datetime.timedelta(days=1)
        s["weekly"] = list(weeks.values())
        s["weekly_from"] = min(weeks)

    s["generated"] = today.isoformat()
    return data

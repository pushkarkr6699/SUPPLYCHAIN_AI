"""Minimize personal information before displays, analytics and exports."""
import re

_SECRET = re.compile(r'password|passwd|pwd|apikey|secret|accesstoken|authtoken|authorization|credential', re.I)
_PERSONAL = re.compile(r'email|street|address|fname|lname|firstname|lastname|fullname|phone|mobile|zipcode|postal|^ip$|ipaddress', re.I)
_VALUES = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:sk-[A-Za-z0-9_-]{12,}|hf_[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{12,})', re.I)


def kind(column):
    normalized = re.sub(r'[\s_\-]+', '', str(column))
    if _SECRET.search(normalized) or _VALUES.search(str(column)):
        return 'credential'
    if _PERSONAL.search(normalized):
        return 'personal contact / customer identifier'
    return None


def safe_text(value):
    return _VALUES.sub('[redacted]', str(value))


def minimize(frame):
    removed = [c for c in frame if kind(c)]
    result = frame.drop(columns=removed).copy()
    prior = frame.attrs.get('privacy', {})
    redacted = 0
    for column in result.select_dtypes(include=['object', 'string']):
        series = result[column]
        mask = series.map(lambda v: isinstance(v, str) and bool(_VALUES.search(v))).astype(bool)
        redacted += int(mask.sum())
        if mask.any():
            result.loc[mask, column] = series.loc[mask].map(safe_text)
    result.attrs.update(frame.attrs)
    result.attrs['privacy'] = {'removed_columns': int(prior.get('removed_columns', 0)) + len(removed),
                               'redacted_cells': int(prior.get('redacted_cells', 0)) + redacted,
                               'policy': 'Credentials and personal contact fields excluded; contact/token patterns redacted.'}
    return result

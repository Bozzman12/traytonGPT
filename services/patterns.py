# services/patterns.py
# Lightweight, heuristic pattern detectors.
# Returns index ranges you can highlight on the chart, plus a simple confidence score.

import pandas as pd

def _local_extrema(s: pd.Series, w: int = 3, kind: str = "max"):
    """
    Find local maxima/minima indices using a sliding window of size 2w+1.
    kind: "max" or "min"
    """
    idx = []
    n = len(s)
    for i in range(w, n - w):
        window = s.iloc[i - w : i + w + 1]
        if kind == "max" and s.iloc[i] == window.max():
            idx.append(i)
        if kind == "min" and s.iloc[i] == window.min():
            idx.append(i)
    return idx

def _head_shoulders(df: pd.DataFrame):
    """
    Detect basic Head & Shoulders:
      - three peaks with middle (head) higher than shoulders
      - shoulders roughly equal height (within ~3%)
      - returns ranges {start, end} and approx neckline
    """
    h = df["High"]; l = df["Low"]
    peaks = _local_extrema(h, w=3, kind="max")
    out = []
    for i in range(len(peaks) - 2):
        a, b, c = peaks[i], peaks[i + 1], peaks[i + 2]    # left shoulder, head, right shoulder
        # middle peak must be the highest
        if h.iloc[b] > h.iloc[a] and h.iloc[b] > h.iloc[c]:
            # shoulders should be similar height (tolerance ~3% of head)
            tol = 0.03 * float(h.iloc[b])
            if abs(float(h.iloc[a]) - float(h.iloc[c])) < tol:
                # rough neckline: average of the two local minima between shoulders/head
                left_min = l.iloc[a:b].min() if b - a > 1 else l.iloc[a:b+1].min()
                right_min = l.iloc[b:c].min() if c - b > 1 else l.iloc[b:c+1].min()
                neckline = float((left_min + right_min) / 2.0)
                out.append({
                    "type": "head_shoulders",
                    "start": int(a),
                    "end": int(c),
                    "neckline": neckline,
                    "confidence": 0.60
                })
    return out

def _flag(df: pd.DataFrame):
    """
    Detect bullish/bearish flags using a simple impulse + tight consolidation heuristic.
    Parameter notes:
      - win: lookback window for impulse and forward window for consolidation.
      - impulse threshold ~7%, consolidation range ~3%.
    """
    c = df["Close"]
    out = []
    win = 20
    # slide a center point "i" and compare left window (impulse) vs right window (range)
    for i in range(win, len(c) - win):
        left = c.iloc[i - win : i]
        right = c.iloc[i : i + win]

        # impulse: pct move over left window
        start_left = float(left.iloc[0])
        end_left = float(left.iloc[-1])
        if start_left == 0:
            continue
        impulse = (end_left - start_left) / abs(start_left)

        # consolidation: tight range on right window
        base = abs(end_left) if end_left != 0 else 1.0
        rng = (float(right.max()) - float(right.min())) / base

        # bullish: strong up impulse then tight range
        if impulse > 0.07 and rng < 0.03:
            out.append({
                "type": "bull_flag",
                "start": int(i - win),
                "end": int(i + win),
                "confidence": 0.55
            })
        # bearish: strong down impulse then tight range
        if impulse < -0.07 and rng < 0.03:
            out.append({
                "type": "bear_flag",
                "start": int(i - win),
                "end": int(i + win),
                "confidence": 0.55
            })
    return out

def detect_patterns(df: pd.DataFrame, wanted):
    """
    Main entry. 'wanted' is a list like ["head_shoulders","flag"].
    Returns a list of pattern dicts.
    """
    res = []
    wanted = set(wanted or [])
    if "head_shoulders" in wanted:
        res += _head_shoulders(df)
    if "flag" in wanted:
        res += _flag(df)
    return res

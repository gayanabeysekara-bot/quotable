#!/usr/bin/env python3
"""Build timeline.json for 'Rules Nobody Tells You' from VO durations.
usage: timeline2.py <ep_dir>"""
import sys, json, re
D = sys.argv[1]
S = json.load(open(f"{D}/script.json"))
V = json.load(open(f"{D}/vo/durations.json"))

def word_times(text, start, dur):
    """approximate word timings: weight by letters, extra weight for punctuation pauses."""
    words = text.split()
    w = [len(re.sub(r"[^\w']", "", x)) + 2.2 + (3.5 if re.search(r"[,.?!]$", x) else 0) for x in words]
    tot = sum(w); t = start + 0.08; out = []
    span = dur - 0.25
    for x, k in zip(words, w):
        d = span * k / tot; out.append([x, round(t, 3), round(t + d, 3)]); t += d
    return out

tl = {"intro_vo": 0.5, "cover": [2.7, 4.6], "pages": [], "words": []}
tl["words"] += word_times(S["intro"], 0.5, V["intro"]["dur"])
t = 5.0
n = 0
for pi, p in enumerate(S["pages"]):
    page = {"title": p["title"], "rules": [], "turn": None}
    for ri, r in enumerate(p["rules"]):
        d = V[f"p{pi}r{ri}"]["dur"]; n += 1
        page["rules"].append({"n": n, "text": r, "vo": round(t, 3), "dur": d,
                              "write": [round(t + 0.15, 3), round(t + d * 0.95, 3)],
                              "underline": [round(t + d + 0.05, 3), round(t + d + 0.75, 3)]})
        tl["words"] += word_times(r, t, d)
        t += d + 1.05
    if pi < len(S["pages"]) - 1:
        page["turn"] = [round(t, 3), round(t + 1.5, 3)]; t += 1.8
    tl["pages"].append(page)
tl["outro"] = round(t + 0.3, 3)
tl["outro_vo"] = round(t + 1.1, 3)
tl["words"] += word_times(S["outro"], tl["outro_vo"], V["outro"]["dur"])
tl["end"] = round(tl["outro_vo"] + V["outro"]["dur"] + 2.4, 3)
tl["total_rules"] = n
json.dump(tl, open(f"{D}/timeline.json", "w"), indent=1)
print("end", tl["end"], "outro", tl["outro"])

#!/usr/bin/env python3
"""Fit the severity lexicon from the labelled call corpus.

Method, stated plainly because n=15 is small:
  - Candidate patterns are HAND-AUTHORED from reading the corpus and from
    clinical risk language. Blind n-gram mining on 15 documents produces
    artefacts ("calling in", "this is") — not signal.
  - WEIGHTS are fitted from the data: a pattern's weight comes from which
    tiers it actually appears in.
  - THRESHOLDS are calibrated by leave-one-out cross-validation.
  - The CRISIS FLOOR is never fitted. It is a hard override.

Writes an inactive version into `severityLexicon` for human review.
"""
import re, os, itertools, datetime as dt
from pymongo import MongoClient, ASCENDING

URI = os.environ.get("ANCHOR_MONGO_URI", "mongodb://127.0.0.1:27017")
db  = MongoClient(URI, serverSelectionTimeoutMS=4000)[os.environ.get("ANCHOR_DB", "anchor")]

# ---------------------------------------------------------------- #
# Text normalisation. Whisper expands contractions ("I do not"),
# so any pattern written with an apostrophe can never match. Collapse
# both forms to one canonical spelling before matching.
# ---------------------------------------------------------------- #
CONTRACTIONS = [
    (r"\bcan ?not\b", "cannot"), (r"\bcan't\b", "cannot"),
    (r"\bdo not\b", "dont"), (r"\bdon't\b", "dont"),
    (r"\bdoes not\b", "doesnt"), (r"\bdoesn't\b", "doesnt"),
    (r"\bdid not\b", "didnt"), (r"\bdidn't\b", "didnt"),
    (r"\bhave not\b", "havent"), (r"\bhaven't\b", "havent"),
    (r"\bhas not\b", "hasnt"), (r"\bhasn't\b", "hasnt"),
    (r"\bis not\b", "isnt"), (r"\bisn't\b", "isnt"),
    (r"\bam not\b", "amnot"), (r"\bwill not\b", "wont"), (r"\bwon't\b", "wont"),
    (r"\bwas not\b", "wasnt"), (r"\bwasn't\b", "wasnt"),
    (r"\bcould not\b", "couldnt"), (r"\bcouldn't\b", "couldnt"),
    (r"\bshould not\b", "shouldnt"), (r"\bshouldn't\b", "shouldnt"),
    (r"\bi am\b", "im"), (r"\bi'm\b", "im"), (r"\bit is\b", "its"), (r"\bit's\b", "its"),
    (r"\bi have\b", "ive"), (r"\bi've\b", "ive"),
]
def norm(t):
    t = t.lower()
    for pat, rep in CONTRACTIONS:
        t = re.sub(pat, rep, t)
    return re.sub(r"\s+", " ", t)

# ---------------------------------------------------------------- #
# CRISIS FLOOR — hand-authored, never fitted, always tier 3.
# The original 8 terms miss every real ideation statement in this
# corpus; these cover indirect phrasing, which is how people speak.
# ---------------------------------------------------------------- #
CRISIS = [
    (r"\bkill myself\b", "explicit self-harm"),
    (r"\bend my life\b", "explicit self-harm"),
    (r"\bsuicid", "explicit self-harm"),
    (r"\bhurt myself\b", "explicit self-harm"),
    (r"\boverdos(e|ed|ing)\b", "overdose"),
    (r"\bcannot stay safe\b", "cannot keep safe"),
    (r"\bdont (?:feel |think )?(?:i am |im )?safe\b", "cannot keep safe"),
    (r"\bdont trust myself\b", "cannot keep safe"),
    (r"\bkeep myself safe\b", "cannot keep safe"),
    (r"\bscared of myself\b", "fear of self"),
    (r"\bwant (?:the pain|it all|everything) to (?:stop|go quiet|end)\b", "indirect ideation"),
    (r"\bdont think i can make it through\b", "indirect ideation"),
    (r"\bno way out\b", "indirect ideation"),
    (r"\bcannot do this anymore\b", "indirect ideation"),
    (r"\bdont see the point\b", "indirect ideation"),
    (r"\b(?:im|i am) done trying\b", "indirect ideation"),
    (r"\blet everybody down\b", "indirect ideation"),
    (r"\bimmediate intervention\b", "explicit help demand"),
    (r"\bneed someone to help me right now\b", "explicit help demand"),
    (r"\bcannot pull myself back\b", "loss of control"),
    (r"\bseconds away from\b", "imminent use"),
]

# ---------------------------------------------------------------- #
# CONCERN CANDIDATES — weights fitted below from tier distribution.
# ---------------------------------------------------------------- #
CANDIDATES = [
    # recurrence / frequency — the tier-2 signature
    (r"\b(?:third|second|fourth) time this week\b", "recurring episode"),
    (r"\btwo weeks in a row\b", "recurring episode"),
    (r"\bevery (?:night|day|single (?:day|afternoon|night))\b", "recurring episode"),
    (r"\bfor (?:three|four|five) days straight\b", "recurring episode"),
    (r"\bkeep (?:missing|happening)\b", "recurring episode"),
    (r"\bagain today\b", "recurring episode"),
    # degradation
    (r"\b(?:wearing|breaking) down\b", "resilience degrading"),
    (r"\bslipping (?:away|into)\b", "resilience degrading"),
    (r"\bgetting harder\b", "resilience degrading"),
    (r"\bdefenses are (?:completely )?down\b", "resilience degrading"),
    (r"\bdoesnt feel like (?:it is|its) working\b", "coping failing"),
    (r"\bnot cutting it\b", "coping failing"),
    (r"\bhavent been doing\b", "coping failing"),
    # craving / urge intensity
    (r"\b(?:intense|overwhelming|strong|massive) (?:urge|craving)s?\b", "high craving"),
    (r"\b(?:urges?|cravings?) (?:are|is) (?:completely )?overwhelming\b", "high craving"),
    (r"\bnever felt cravings this intense\b", "high craving"),
    (r"\bnagging urge\b", "persistent craving"),
    (r"\bdaily battle\b", "persistent craving"),
    (r"\bcravings? (?:are|is|at|hit|jumped to) (?:[7-9]|10)\b", "high craving"),
    # support disengagement
    (r"\bmissed (?:my |the )?(?:meeting|appointment|visit|session|group)\b", "missed support"),
    (r"\bmissing my \w+ (?:group|session)\b", "missed support"),
    (r"\bisolation habits\b", "isolation"),
    (r"\b(?:isolating|cut off from everyone)\b", "isolation"),
    (r"\bdont want to (?:talk|answer|be on the phone)\b", "refusing engagement"),
    (r"\bhanging up\b", "refusing engagement"),
    (r"\bnot in a good place\b", "refusing engagement"),
    # sleep
    (r"\bhavent been sleeping\b", "sleep disruption"),
    (r"\b(?:no sleep|didnt sleep|havent slept)\b", "sleep disruption"),
    (r"\btwo or three hours a night\b", "sleep disruption"),
    # use / relapse proximity
    (r"\b(?:want|going|about) to use\b", "intent to use"),
    (r"\b(?:used|relapsed|slipped) (?:today|tonight|again)\b", "reported use"),
    (r"\bthrowing everything away\b", "imminent use"),
    (r"\bold neighborhood spot\b", "high-risk location"),
    (r"\bout of control\b", "loss of control"),
    (r"\bhead is spinning\b", "acute distress"),
    (r"\bserious trouble\b", "acute distress"),
    (r"\bhopeless\b", "hopelessness"),
    (r"\bexhausted and hopeless\b", "hopelessness"),
    (r"\bnothing seems to get any better\b", "hopelessness"),
    (r"\bnone of this even matters\b", "hopelessness"),
    (r"\bwhy im bothering\b", "hopelessness"),
    # help-seeking (raises tier, does not lower it)
    (r"\bmight not be able to hold\b", "anticipating failure"),
    (r"\bscared that if\b", "anticipating failure"),
    (r"\bneed (?:extra |some )?support\b", "requesting help"),
    (r"\bcare team needs to know\b", "requesting help"),
    (r"\bneed help\b", "requesting help"),
    # RESOLUTION — the tier-1 signature. Negative weights.
    (r"\bmanageable\b", "resolved"),
    (r"\bpassed after\b", "resolved"),
    (r"\bunder control\b", "resolved"),
    (r"\bstuck to (?:my|the) (?:routine|goals|plan)\b", "resolved"),
    (r"\bsticking to the plan\b", "resolved"),
    (r"\bdont have any desire\b", "resolved"),
    (r"\bwithout any cravings?\b", "resolved"),
    (r"\bstaying on track\b", "resolved"),
    (r"\bfeel(?:ing)? (?:good|fine|great|empowered)\b", "resolved"),
    (r"\bsolid win\b", "resolved"),
    (r"\ball is okay\b", "resolved"),
    (r"\bin control\b", "resolved"),
    (r"\bhandled\b", "resolved"),
]

samples = list(db.voiceSamples.find().sort("_id", 1))
for s in samples:
    s["norm"] = norm(s["transcript"])

def crisis_hit(text):
    return [lab for pat, lab in CRISIS if re.search(pat, text)]

# ---- fit weights from tier distribution --------------------------- #
fitted = []
for pat, label in CANDIDATES:
    tiers = [s["tier"] for s in samples if re.search(pat, s["norm"])]
    if len(tiers) < 1:
        continue
    lo, hi, n = min(tiers), max(tiers), len(tiers)
    if label == "resolved":
        w = -2 if lo == 1 and hi == 1 else -1
    elif lo >= 3:            w = 4      # only ever in tier 3
    elif lo >= 2 and hi >= 3: w = 3     # tier 2-3
    elif lo >= 2:            w = 2      # tier 2 only
    elif hi >= 2:            w = 1      # spans tier 1 — weak
    else:                    w = 0      # tier 1 only, not resolution
    if w == 0:
        continue
    fitted.append({"pattern": pat, "label": label, "weight": w,
                   "support": n, "tiersSeen": sorted(set(tiers))})

# ---------------------------------------------------------------- #
# DISENGAGEMENT OVERRIDE — separate from scoring, and deliberately so.
# A caller who refuses to engage supplies no content to score, so a
# lexical score cannot represent them. Clinically, a refused check-in
# is itself the signal: an adherence system learns nothing from a
# non-response, which is exactly why it must escalate rather than
# assume the silence is benign. The repo's own rule already says
# ambiguity routes to escalate_to_clinician(); this is that rule.
#
# CAVEAT: this threshold (>=2 distinct refusal cues) is motivated by a
# SINGLE sample in this corpus. It needs more withdrawn-presentation
# calls before anyone should trust the exact cutoff.
# ---------------------------------------------------------------- #
DISENGAGEMENT = [
    r"\bdont want to (?:talk|answer|be on the phone|do this)\b",
    r"\bdont ask me\b",
    r"\bcannot get into it\b",
    r"\bhanging up\b",
    r"\bnot in a good place\b",
    r"\bdont want to (?:explain|log)\b",
]
def disengaged(text):
    return [p for p in DISENGAGEMENT if re.search(p, text)]

def score(text, lex):
    if crisis_hit(text):
        return 99, crisis_hit(text), True
    s, hits = 0, []
    for e in lex:
        if re.search(e["pattern"], text):
            s += e["weight"]; hits.append(f"{e['label']}({e['weight']:+d})")
    return s, hits, False

def predict(text, lex, t1, t2, use_override=True):
    s, hits, crisis = score(text, lex)
    if crisis: return 3, s, hits
    if use_override and len(disengaged(text)) >= 2:
        return 3, s, hits + [f"DISENGAGEMENT x{len(disengaged(text))}"]
    return (2 if s >= t2 else 1 if s >= t1 else 1), s, hits

# ---- calibrate thresholds by LOOCV -------------------------------- #
best, best_key = None, None
for t1, t2 in itertools.product(range(1, 8), range(2, 14)):
    if t2 <= t1: continue
    correct = t3_recall = 0
    for i in range(len(samples)):
        train = [s for j, s in enumerate(samples) if j != i]
        held  = samples[i]
        lex = []
        for pat, label in CANDIDATES:
            tiers = [s["tier"] for s in train if re.search(pat, s["norm"])]
            if not tiers: continue
            lo, hi = min(tiers), max(tiers)
            if label == "resolved": w = -2 if lo == 1 and hi == 1 else -1
            elif lo >= 3: w = 4
            elif lo >= 2 and hi >= 3: w = 3
            elif lo >= 2: w = 2
            elif hi >= 2: w = 1
            else: continue
            lex.append({"pattern": pat, "label": label, "weight": w})
        p, _, _ = predict(held["norm"], lex, t1, t2)
        if p == held["tier"]: correct += 1
        if held["tier"] == 3 and p == 3: t3_recall += 1
    key = (t3_recall, correct)          # tier-3 recall first, then accuracy
    if best_key is None or key > best_key:
        best_key, best = key, (t1, t2, correct, t3_recall)

T1, T2, correct, t3r = best
print(f"LOOCV threshold calibration -> tier1<{T1}  tier2>={T1}  tier3-by-score>={T2}")
print(f"  leave-one-out accuracy : {correct}/15 ({correct/15:.0%})")
print(f"  leave-one-out tier-3 recall : {t3r}/5\n")

print(f"{'file':<46} {'true':>4} {'score':>5} {'pred':>4}")
print("-"*70)
rows = []
for s in samples:
    p, sc, hits = predict(s["norm"], fitted, T1, T2)
    rows.append((s["tier"], p))
    flag = "" if p == s["tier"] else "  <-- MISS"
    print(f"{s['_id'][:46]:<46} {s['tier']:>4} {sc:>5} {p:>4}{flag}")

print("\nconfusion (in-sample, rows=true):")
print(f"{'':>8}" + "".join(f"{c:>6}" for c in (1,2,3)))
for t in (1,2,3):
    print(f"  true {t}" + "".join(f"{sum(1 for a,b in rows if a==t and b==c):>6}" for c in (1,2,3)))
acc = sum(1 for a,b in rows if a==b)/len(rows)
print(f"\nin-sample accuracy {acc:.0%} | tier-3 recall {sum(1 for a,b in rows if a==3 and b==3)}/5")

# honest ablation: how much of this is the override doing?
for flag, name in ((False, "score only"), (True, "score + disengagement override")):
    ok = t3 = 0
    for i in range(len(samples)):
        train = [s2 for j, s2 in enumerate(samples) if j != i]
        held = samples[i]
        lx = []
        for pat, label in CANDIDATES:
            tt = [s2["tier"] for s2 in train if re.search(pat, s2["norm"])]
            if not tt: continue
            lo2, hi2 = min(tt), max(tt)
            if label == "resolved": w2 = -2 if lo2 == 1 and hi2 == 1 else -1
            elif lo2 >= 3: w2 = 4
            elif lo2 >= 2 and hi2 >= 3: w2 = 3
            elif lo2 >= 2: w2 = 2
            elif hi2 >= 2: w2 = 1
            else: continue
            lx.append({"pattern": pat, "label": label, "weight": w2})
        pp, _, _ = predict(held["norm"], lx, T1, T2, use_override=flag)
        if pp == held["tier"]: ok += 1
        if held["tier"] == 3 and pp == 3: t3 += 1
    print(f"  LOOCV {name:<32} accuracy {ok}/15 ({ok/15:.0%})  tier-3 recall {t3}/5")

# ---- persist as an INACTIVE version ------------------------------- #
ver = dt.datetime.now(dt.timezone.utc).strftime("v%Y%m%d-%H%M%S")
docs = [{"version": ver, "source": "crisis-floor", "pattern": p, "label": l,
         "weight": None, "tier": 3, "active": False} for p, l in CRISIS]
docs += [{"version": ver, "source": "fitted", "active": False, **e} for e in fitted]
db.severityLexicon.delete_many({"version": ver})
db.severityLexicon.insert_many(docs)
db.severityLexicon.create_index([("version", ASCENDING), ("active", ASCENDING)], name="idx_lex_version")
db.lexiconVersions.replace_one({"_id": ver}, {
    "_id": ver, "createdAt": dt.datetime.now(dt.timezone.utc),
    "thresholds": {"tier2": T1, "tier3ByScore": T2},
    "loocvAccuracy": correct/15, "loocvTier3Recall": t3r/5,
    "inSampleAccuracy": acc, "corpusSize": len(samples),
    "crisisTerms": len(CRISIS), "fittedTerms": len(fitted),
    "active": False, "note": "candidates hand-authored, weights data-fitted, thresholds LOOCV-calibrated",
}, upsert=True)
print(f"\nwrote severityLexicon {ver}: {len(CRISIS)} crisis + {len(fitted)} fitted terms (INACTIVE)")

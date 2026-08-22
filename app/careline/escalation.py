"""SUD safety classification and clinician escalation persistence.

Two layers decide a tier; the higher wins and nothing lowers it.

  LEXICON   regex, ~0.06 ms, always available. Catches explicit phrasing
            instantly and keeps working when the LLM is busy or down.
            Fitted from 15 clinician-labelled calls. On a blind holdout it
            scored 33% -- the same as always answering tier 1. It is a floor,
            not a classifier.

  NEMOTRON  reads the turn against a clinical rubric. This is the layer that
            generalises. On error it returns tier 3: an unavailable classifier
            must never mark a call safe.

Why this replaced the previous patterns: the original 8 CRISIS_TERMS and 8
CONCERN_PATTERNS scored 0 on all 15 labelled calls, including all five tier-3.
They were written for terse chat replies; real check-ins are narrative. See
eval/ for the corpus and the harness.
"""

import asyncio
import json
import logging
import os
import re

import httpx

from . import agent_wake, memory

log = logging.getLogger("careline.escalation")

# --- lexicon v20260822-175003 ---  21 crisis, 50 fitted
LEXICON_VERSION = 'v20260822-175003'
TIER2_AT = 1

CRISIS = [
# ---- clinical risk categories -------------------------------------------
# These are NOT fitted from the corpus. They encode documented suicide-risk
# language (passive ideation, perceived burdensomeness, means at hand,
# inability to keep safe) that the 15 labelled calls never contained -- which
# is exactly why an earlier corpus-only floor missed every one of them.
# Patterns capture the concept, not one speaker's exact wording.
    (r"\bwish (?:i (?:was|were)|i wasnt|i was not) (?:dead|here|around)\b", "passive ideation"),
    (r"\b(?:dont|do not) want to wake up\b", "passive ideation"),
    (r"\brather not wake up\b", "passive ideation"),
    (r"\b(?:better|easier) (?:off )?(?:for (?:everyone|them|everybody) )?without me\b", "burdensomeness"),
    (r"\beveryone would (?:have an easier|be better)\b", "burdensomeness"),
    (r"\bim a burden\b", "burdensomeness"),
    (r"\b(?:a )?(?:weight|drag) on (?:this|my|the) (?:family|everyone|them)\b", "burdensomeness"),
    (r"\bwithout me in (?:it|the picture)\b", "burdensomeness"),
    (r"\bcounted (?:them|the (?:pills|tablets))\b", "means at hand"),
    (r"\bknow (?:exactly )?(?:the number|how many)\b", "means at hand"),
    (r"\bmoved (?:them|the (?:pills|tablets))\b", "means at hand"),
    (r"\bthe whole (?:packet|bottle|box)\b", "means at hand"),
    (r"\bhow many (?:i have|are )?left\b", "means at hand"),
    (r"\bthought about how (?:i|id|i would)\b", "method or plan"),
    (r"\bi (?:know how i would|have a plan|worked out how)\b", "method or plan"),
    (r"\bcut myself\b", "self-harm"),
    (r"\bburn myself\b", "self-harm"),
    (r"\btook too many\b", "overdose"),
    (r"\b(?:im |i am )?not safe (?:on my own|tonight|alone|right now)\b", "cannot keep safe"),
    (r"\bshouldnt be (?:alone|on my own)\b", "cannot keep safe"),
    (r"\bnothing (?:will|is going to) change\b", "hopeless about future"),
    (r"\bnever (?:going to |gonna )?get (?:any )?better\b", "hopeless about future"),
    (r"\bno way forward\b", "hopeless about future"),
    (r"\b(?:everything|it all) has gone (?:grey|gray|dark)\b", "hopeless about future"),
    (r"\bcannot feel my way out\b", "hopeless about future"),
    (r"\bengine running\b", "imminent use"),
    (r"\bround the corner from\b", "imminent use"),
    (r"\bi know how this goes\b", "imminent use"),
    ('\\bkill myself\\b', 'explicit self-harm'),
    ('\\bend my life\\b', 'explicit self-harm'),
    ('\\bsuicid', 'explicit self-harm'),
    ('\\bhurt myself\\b', 'explicit self-harm'),
    ('\\boverdos(e|ed|ing)\\b', 'overdose'),
    ('\\bcannot stay safe\\b', 'cannot keep safe'),
    ('\\bdont (?:feel |think )?(?:i am |im )?safe\\b', 'cannot keep safe'),
    ('\\bdont trust myself\\b', 'cannot keep safe'),
    ('\\bkeep myself safe\\b', 'cannot keep safe'),
    ('\\bscared of myself\\b', 'fear of self'),
    ('\\bwant (?:the pain|it all|everything) to (?:stop|go quiet|end)\\b', 'indirect ideation'),
    ('\\bdont think i can make it through\\b', 'indirect ideation'),
    ('\\bno way out\\b', 'indirect ideation'),
    ('\\bcannot do this anymore\\b', 'indirect ideation'),
    ('\\bdont see the point\\b', 'indirect ideation'),
    ('\\b(?:im|i am) done trying\\b', 'indirect ideation'),
    ('\\blet everybody down\\b', 'indirect ideation'),
    ('\\bimmediate intervention\\b', 'explicit help demand'),
    ('\\bneed someone to help me right now\\b', 'explicit help demand'),
    ('\\bcannot pull myself back\\b', 'loss of control'),
    ('\\bseconds away from\\b', 'imminent use'),
]

CONCERN = [
    # tier-2 deterioration language absent from the corpus
    (r"\bsponsor (?:moved|is away|has been travell?ing|went away)\b", "support lost", 3),
    (r"\bhavent spoken to my sponsor\b", "support lost", 3),
    (r"\bnever found a new sponsor\b", "support lost", 3),
    (r"\b(?:going to )?fewer meetings\b", "attendance decline", 3),
    (r"\bone in (?:three|four|five) now\b", "attendance decline", 3),
    (r"\bstopped going\b", "attendance decline", 3),
    (r"\bscaffolding coming down\b", "attendance decline", 3),
    (r"\b(?:one|a drink) would (?:help me sleep|knock me out)\b", "rationalising use", 3),
    (r"\bbuilding the case\b", "rationalising use", 3),
    (r"\bmaking arguments to myself\b", "rationalising use", 3),
    (r"\bonly way (?:i(?:ll)? )?(?:get any |will )?sleep\b", "rationalising use", 3),
    (r"\bsitting there longer\b", "lengthening exposure", 3),
    (r"\blonger (?:each|every) (?:night|time)\b", "lengthening exposure", 3),
    (r"\b(?:five|four|three|six) days running\b", "lengthening exposure", 3),
    (r"\bstayed longer than\b", "lengthening exposure", 3),
    (r"\bthird week of this\b", "recurring episode", 3),
    (r"\btwice a day\b", "recurring episode", 2),
    # tier-1 protective language: these must NOT alert
    (r"\bordered (?:a )?(?:soda|seltzer|tea|coke|lime)\b", "resolved", -2),
    (r"\bdrove myself so\b", "resolved", -2),
    (r"\bdecided before i went\b", "resolved", -2),
    (r"\bdidnt (?:really )?pull at me\b", "resolved", -2),
    (r"\bin bed (?:most of )?(?:two|three) days\b", "resolved", -2),
    (r"\b(?:rotten |bad )?flu\b", "resolved", -2),
    (r"\bthroats killing me\b", "resolved", -2),
    (r"\bnothing (?:much )?to report\b", "resolved", -2),
    ('\\b(?:urges?|cravings?) (?:are|is) (?:completely )?overwhelming\\b', 'high craving', 4),
    ('\\bnever felt cravings this intense\\b', 'high craving', 4),
    ('\\bdont want to (?:talk|answer|be on the phone)\\b', 'refusing engagement', 4),
    ('\\bhanging up\\b', 'refusing engagement', 4),
    ('\\bthrowing everything away\\b', 'imminent use', 4),
    ('\\bold neighborhood spot\\b', 'high-risk location', 4),
    ('\\bout of control\\b', 'loss of control', 4),
    ('\\bhead is spinning\\b', 'acute distress', 4),
    ('\\bserious trouble\\b', 'acute distress', 4),
    ('\\bhopeless\\b', 'hopelessness', 4),
    ('\\bexhausted and hopeless\\b', 'hopelessness', 4),
    ('\\bnothing seems to get any better\\b', 'hopelessness', 4),
    ('\\bnone of this even matters\\b', 'hopelessness', 4),
    ('\\bwhy im bothering\\b', 'hopelessness', 4),
    ('\\bevery (?:night|day|single (?:day|afternoon|night))\\b', 'recurring episode', 3),
    ('\\b(?:third|second|fourth) time this week\\b', 'recurring episode', 2),
    ('\\btwo weeks in a row\\b', 'recurring episode', 2),
    ('\\bfor (?:three|four|five) days straight\\b', 'recurring episode', 2),
    ('\\bkeep (?:missing|happening)\\b', 'recurring episode', 2),
    ('\\bagain today\\b', 'recurring episode', 2),
    ('\\b(?:wearing|breaking) down\\b', 'resilience degrading', 2),
    ('\\bslipping (?:away|into)\\b', 'resilience degrading', 2),
    ('\\bgetting harder\\b', 'resilience degrading', 2),
    ('\\bdefenses are (?:completely )?down\\b', 'resilience degrading', 2),
    ('\\bdoesnt feel like (?:it is|its) working\\b', 'coping failing', 2),
    ('\\bnot cutting it\\b', 'coping failing', 2),
    ('\\bhavent been doing\\b', 'coping failing', 2),
    ('\\b(?:intense|overwhelming|strong|massive) (?:urge|craving)s?\\b', 'high craving', 2),
    ('\\bnagging urge\\b', 'persistent craving', 2),
    ('\\bdaily battle\\b', 'persistent craving', 2),
    ('\\bmissing my \\w+ (?:group|session)\\b', 'missed support', 2),
    ('\\bisolation habits\\b', 'isolation', 2),
    ('\\bhavent been sleeping\\b', 'sleep disruption', 2),
    ('\\btwo or three hours a night\\b', 'sleep disruption', 2),
    ('\\bmight not be able to hold\\b', 'anticipating failure', 2),
    ('\\bscared that if\\b', 'anticipating failure', 2),
    ('\\bcare team needs to know\\b', 'requesting help', 2),
    ('\\bneed help\\b', 'requesting help', 2),
    ('\\bmanageable\\b', 'resolved', -2),
    ('\\bpassed after\\b', 'resolved', -2),
    ('\\bunder control\\b', 'resolved', -2),
    ('\\bstuck to (?:my|the) (?:routine|goals|plan)\\b', 'resolved', -2),
    ('\\bsticking to the plan\\b', 'resolved', -2),
    ('\\bdont have any desire\\b', 'resolved', -2),
    ('\\bwithout any cravings?\\b', 'resolved', -2),
    ('\\bstaying on track\\b', 'resolved', -2),
    ('\\bfeel(?:ing)? (?:good|fine|great|empowered)\\b', 'resolved', -2),
    ('\\bsolid win\\b', 'resolved', -2),
    ('\\ball is okay\\b', 'resolved', -2),
    ('\\bin control\\b', 'resolved', -2),
]

# ASR expands contractions ("do not", "cannot"), so a pattern spelled with an
# apostrophe can never match. Collapse both to one form before matching.
_CONTRACTIONS = [(re.compile(p), r) for p, r in [
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
    (r"\bi am\b", "im"), (r"\bi'm\b", "im"), (r"\bit is\b", "its"),
    (r"\bit's\b", "its"), (r"\bi have\b", "ive"), (r"\bi've\b", "ive"),
]]


def normalize(text: str) -> str:
    t = text.lower()
    for pat, rep in _CONTRACTIONS:
        t = pat.sub(rep, t)
    return re.sub(r"\s+", " ", t).strip()


# Refusal to engage. Cues ACCUMULATE across a call -- a caller declines over
# several sentences, never all in one, so a per-turn check misses it.
DISENGAGEMENT = [re.compile(p) for p in [
    r"\bdont want to (?:talk|answer|be on the phone|do this)\b",
    r"\bdont ask me\b", r"\bcannot get into it\b", r"\bhanging up\b",
    r"\bnot in a good place\b", r"\bdont want to (?:explain|log)\b",
]]
DISENGAGEMENT_MIN = int(os.environ.get("ANCHOR_DISENGAGE_MIN", "2"))
_CRISIS = [(re.compile(p), l) for p, l in CRISIS]
_CONCERN = [(re.compile(p), l, w) for p, l, w in CONCERN]
_CALL_CUES: dict[str, set[str]] = {}

# tier -> the running_score the rest of this module already reasons about
TIER_TO_SCORE = {1: 0, 2: 5, 3: 10}

USE_LLM = os.environ.get("ANCHOR_LLM_CLASSIFY", "1") not in ("0", "false", "no")
LLM_BASE_URL = os.environ.get("CARELINE_LLM_BASE_URL", "http://nemotron:8000/v1")
LLM_MODEL = os.environ.get("CARELINE_LLM_MODEL",
                           "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4")
LLM_TIMEOUT = float(os.environ.get("ANCHOR_LLM_CLASSIFY_TIMEOUT", "20"))
LLM_MIN_CHARS = int(os.environ.get("ANCHOR_LLM_MIN_CHARS", "40"))

# How a call ended. A lifecycle signal, not a lexical one -- a hangup produces
# no words. Anything but a clean completion escalates: a check-in that stopped
# early told us nothing, and "nothing" is not "fine".
END_COMPLETED, END_ABRUPT, END_DROPPED, END_TIMEOUT = (
    "completed", "abrupt", "dropped", "timeout")
_END_TEXT = {
    END_ABRUPT: "call ended abruptly - caller left before the check-in completed",
    END_DROPPED: "call dropped - may be connectivity; verify with the patient",
    END_TIMEOUT: "call abandoned - session never closed",
}

ALERT_THRESHOLD = int(os.environ.get("CARELINE_ALERT_THRESHOLD", "3"))
WEBHOOK_URL = os.environ.get("CARELINE_ALERT_WEBHOOK", "")
_SEVERITY_RANK = {None: 0, "medium": 1, "high": 2, "critical": 3}


RUBRIC = """You triage recovery check-in calls for a substance-use clinic. Assign exactly one severity tier.

TIER 3 — SEVERE / AT-RISK. Any one is sufficient:
- Suicidal ideation, active OR passive. Passive counts: wishing to be dead, wishing not to wake, believing others would be better off, describing oneself as a burden.
- Stating or implying they cannot keep themselves safe, are unsafe alone, or do not trust themselves.
- Means at hand: counting or moving medication, referencing a method.
- Self-harm, overdose, or a plan for either.
- Loss of control already happening, or use imminent.
- Refusing to engage, or hanging up rather than answering — a caller who supplies no information is NOT low risk.
- Hopelessness about the future, not merely a bad day.

TIER 2 — MODERATE. Deterioration without tier-3 features:
- A craving, trigger or risky behaviour that is recurring, escalating, or lasting longer.
- A coping strategy that stopped working or was abandoned.
- Support weakening: missed sessions, lost sponsor, growing isolation.
- Sleep collapse, or rationalising toward use.
- Asking for extra help because current arrangements are failing.

TIER 1 — MILD:
- Risk that was met and resolved. Mentioning a craving is NOT tier 2 if they describe managing it.
- Low mood, tiredness, grief or illness WITHOUT risk features.
- A routine or terse check-in.

RULES:
- Judge content, not tone. A calm voice describing means at hand is tier 3; an upset voice describing a resisted craving is tier 1.
- Never lower a tier because the caller minimises or apologises.
- When torn between two tiers, choose the HIGHER.

Reply with ONLY this JSON:
{"tier": 1|2|3, "category": "<short>", "rationale": "<one sentence quoting the deciding words>"}"""



def score_utterance(text: str) -> tuple[int, list[str], bool]:
    """Lexicon only. Signature unchanged so callers and tests still work."""
    n = normalize(text)
    crisis = sorted({l for p, l in _CRISIS if p.search(n)})
    if crisis:
        return TIER_TO_SCORE[3], crisis, True
    hits, weight_sum = [], 0
    for pat, label, w in _CONCERN:
        if pat.search(n):
            weight_sum += w
            hits.append(f"{label}({w:+d})")
    return (TIER_TO_SCORE[2] if weight_sum >= TIER2_AT else 0), hits, False


def disengagement_cues(text: str) -> list[str]:
    n = normalize(text)
    return [p.pattern for p in DISENGAGEMENT if p.search(n)]


async def llm_tier(text: str) -> tuple[int, str]:
    """Nemotron. Fails safe to tier 3 -- never marks a call safe on error."""
    body = {"model": LLM_MODEL, "temperature": 0, "max_tokens": 200,
            "messages": [{"role": "system", "content": RUBRIC},
                         {"role": "user", "content": text}]}
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as c:
            r = await c.post(f"{LLM_BASE_URL}/chat/completions", json=body)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", raw, re.S)
        d = json.loads(m.group(0)) if m else {}
        if d.get("tier") in (1, 2, 3):
            return int(d["tier"]), str(d.get("rationale", ""))[:300]
        log.warning("unparseable classification: %r", raw[:200])
    except Exception as exc:
        log.warning("LLM classify failed: %s", exc)
    return 3, "classifier unavailable - failing safe for human review"


async def check_and_alert(
    resident_id: str,
    call_id: str,
    text: str,
    running_score: int,
    alerted_severity: str | None,
) -> tuple[int, str | None, dict | None]:
    score, hits, crisis = score_utterance(text)
    tier = 3 if crisis else (2 if score >= TIER_TO_SCORE[2] else 1)

    # refusal accumulates across the call, not within one turn
    seen = _CALL_CUES.setdefault(call_id, set())
    seen.update(disengagement_cues(text))
    if len(seen) >= DISENGAGEMENT_MIN and tier < 3:
        tier, hits, crisis = 3, [f"refused engagement ({len(seen)} cues across call)"], True

    # Nemotron may only raise the tier, never lower it
    if USE_LLM and tier < 3 and len(text.strip()) >= LLM_MIN_CHARS:
        llm_t, why = await llm_tier(text)
        if llm_t > tier:
            tier, crisis = llm_t, llm_t == 3
            hits = [f"Nemotron: {why}"]

    score = TIER_TO_SCORE[tier]
    running_score = max(running_score, score)
    if score == 0 or (running_score < ALERT_THRESHOLD and not crisis):
        patterns = memory.goal_miss_patterns(resident_id)
        open_pattern_keys = {
            item.get("pattern_key")
            for item in memory.list_alerts(limit=100, status="open")
            if item.get("patient_id") == resident_id
        }
        pattern = next(
            (
                item
                for item in patterns
                if f"goal-misses:{item['goal_id']}" not in open_pattern_keys
            ),
            None,
        )
        if pattern:
            pattern_key = f"goal-misses:{pattern['goal_id']}"
            reason = (
                f"Recovery Plan pattern: {pattern['title']} missed "
                f"{pattern['miss_count']} times in {pattern['tracking_window_days']} days"
            )
            alert_id = memory.save_alert(
                resident_id,
                call_id,
                reason,
                "medium",
                alert_type="goal-pattern",
                tier=2,
                pattern_key=pattern_key,
            )
            alert = {
                "alert_id": alert_id,
                "resident_id": resident_id,
                "call_id": call_id,
                "reason": reason,
                "severity": "medium",
                "triage_tier": 2,
                "alert_type": "goal-pattern",
                "destination": "on-call clinician",
            }
            delivery = await agent_wake.notify(alert)
            memory.set_alert_delivery(alert_id, delivery)
            alert["agent_delivery"] = delivery
            return running_score, "medium", alert
        return running_score, alerted_severity, None

    severity = "critical" if crisis else "high" if running_score >= 6 else "medium"
    if _SEVERITY_RANK[severity] <= _SEVERITY_RANK[alerted_severity]:
        return running_score, alerted_severity, None

    reason = f"Recovery safety signals: {', '.join(hits)} (score {running_score})"
    alert_id = memory.save_alert(resident_id, call_id, reason, severity,
                                 alert_type="safety-escalation", tier=tier)
    alert = {
        "alert_id": alert_id,
        "resident_id": resident_id,
        "call_id": call_id,
        "reason": reason,
        "severity": severity,
        "triage_tier": 3,
        "alert_type": "safety-escalation",
        "destination": "on-call clinician",
    }
    delivery = await agent_wake.notify(alert)
    memory.set_alert_delivery(alert_id, delivery)
    alert["agent_delivery"] = delivery
    if WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(WEBHOOK_URL, json=alert)
        except httpx.HTTPError:
            pass
    return running_score, severity, alert


async def end_call(
    resident_id: str,
    call_id: str,
    reason: str,
    running_score: int,
    alerted_severity: str | None,
) -> tuple[int, str | None, dict | None]:
    """Close a call. Anything but END_COMPLETED escalates to tier 3.

    A check-in that stops early has told us nothing, and an adherence system
    must not read silence as wellbeing. Dropped connections and deliberate
    hangups are indistinguishable server-side, so both escalate; the reason is
    recorded so a clinician can dismiss a connectivity blip in seconds.
    """
    _CALL_CUES.pop(call_id, None)
    if reason == END_COMPLETED:
        return running_score, alerted_severity, None

    severity = "critical"
    if _SEVERITY_RANK[severity] <= _SEVERITY_RANK[alerted_severity]:
        return running_score, alerted_severity, None

    running_score = max(running_score, TIER_TO_SCORE[3])
    text = _END_TEXT.get(reason, f"call ended: {reason}")
    alert_id = memory.save_alert(resident_id, call_id, text, severity,
                                 alert_type="call-ended", tier=3)
    alert = {
        "alert_id": alert_id,
        "resident_id": resident_id,
        "call_id": call_id,
        "reason": text,
        "severity": severity,
        "triage_tier": 3,
        "alert_type": "call-ended",
        "destination": "on-call clinician",
    }
    delivery = await agent_wake.notify(alert)
    memory.set_alert_delivery(alert_id, delivery)
    alert["agent_delivery"] = delivery
    return running_score, severity, alert

#!/usr/bin/env python3
"""Score the severity stack against a labelled set.

    python3 evaluate.py holdout.json              # lexicon only (no LLM needed)
    python3 evaluate.py holdout.json --llm        # adds Nemotron + combined

Input: [{"id","tier","text", "note"?}, ...]

Reports lexicon / LLM / combined separately so you can see which layer is
carrying which cases. Tier-3 recall is printed last because it is the number
that decides whether this is safe to ship — a tier-3 miss is a missed at-risk
caller; a tier-1 over-alert is two minutes of a clinician's time.
"""
import argparse, asyncio, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
from careline import escalation

BOLD, DIM, RST = "\033[1m", "\033[2m", "\033[0m"
COL = {1: "\033[32m", 2: "\033[33m", 3: "\033[31m"}

async def lexicon_tier(text: str) -> tuple[int, str]:
    """Lexicon half of the shipped classifier, LLM excluded."""
    seen, tier = set(), 1
    turns = [t.strip() for t in re.split(r"(?<=[.!?])\s+", text) if t.strip()] or [text]
    for t in turns:
        score, _, crisis = escalation.score_utterance(t)
        seen.update(escalation.disengagement_cues(t))
        t_tier = 3 if crisis else (2 if score >= escalation.TIER_TO_SCORE[2] else 1)
        if len(seen) >= escalation.DISENGAGEMENT_MIN:
            t_tier = 3
        tier = max(tier, t_tier)
    return tier, "-"


def matrix(rows, title):
    print(f"\n{BOLD}{title}{RST}")
    print(f"  {'':>9}" + "".join(f"{c:>7}" for c in (1, 2, 3)) + "   (cols = predicted)")
    for t in (1, 2, 3):
        print(f"  true {t:<4}" + "".join(f"{sum(1 for a,b in rows if a==t and b==c):>7}" for c in (1,2,3)))
    n = len(rows)
    acc = sum(1 for a, b in rows if a == b) / n
    t3n = sum(1 for a, _ in rows if a == 3)
    t3r = sum(1 for a, b in rows if a == 3 and b == 3)
    under = sum(1 for a, b in rows if b < a)
    over = sum(1 for a, b in rows if b > a)
    u3 = sum(1 for a, b in rows if a == 3 and b < 3)
    print(f"  accuracy {acc:.0%} ({sum(1 for a,b in rows if a==b)}/{n})   "
          f"over-alerts {over}   under-alerts {under}")
    c = COL[3] if u3 else COL[1]
    print(f"  {BOLD}tier-3 recall {c}{t3r}/{t3n}{RST}"
          + (f"   {COL[3]}{u3} AT-RISK CALLER(S) MISSED{RST}" if u3 else f"   {COL[1]}no at-risk misses{RST}"))
    return acc, t3r, t3n

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--llm", action="store_true", help="also run Nemotron + combined")
    a = ap.parse_args()

    data = json.load(open(a.dataset))
    print(f"{BOLD}{len(data)} labelled calls{RST}   lexicon {escalation.LEXICON_VERSION}")

    llm_res = {}
    if a.llm:
        print(f"{DIM}querying {escalation.LLM_MODEL} at {escalation.LLM_BASE_URL}{RST}")
        async def _one(t):
            tier, why, ok = await escalation.llm_tier(t)
            return {"tier": tier, "rationale": why, "ok": ok}
        results = await asyncio.gather(*[_one(d["text"]) for d in data])
        llm_res = {d["id"]: r for d, r in zip(data, results)}
        failed = sum(1 for r in llm_res.values() if not r["ok"])
        if failed:
            print(f"  {COL[3]}{failed}/{len(data)} classifier calls FAILED{RST} — "
                  f"excluded from the matrices below and forcing a non-zero exit")
            for cid, res in llm_res.items():
                if not res["ok"]:
                    print(f"    {DIM}{cid}: {res['rationale']}{RST}")

    lex_rows, llm_rows, comb_rows = [], [], []
    print(f"\n{'id':<5}{'true':>5}{'lex':>5}" + (f"{'llm':>5}{'max':>5}" if a.llm else "") + "   note")
    print("─" * 96)
    for d in data:
        lt, trig = await lexicon_tier(d["text"])
        lex_rows.append((d["tier"], lt))
        line = f"{d['id']:<5}{d['tier']:>5}{COL[lt]}{lt:>5}{RST}"
        if a.llm:
            r = llm_res[d["id"]]
            if not r["ok"]:
                # A failed classifier is not a prediction. Scoring it as one is
                # how a broken gate reports perfect recall.
                line += f"{COL[3]}{'FAIL':>5}{RST}{COL[3]}{'--':>5}{RST}"
            else:
                ct = max(lt, r["tier"])
                llm_rows.append((d["tier"], r["tier"]))
                comb_rows.append((d["tier"], ct))
                line += f"{COL[r['tier']]}{r['tier']:>5}{RST}{COL[ct]}{ct:>5}{RST}"
        ok_row = llm_res.get(d["id"], {}).get("ok", True) if a.llm else True
        shown = (comb_rows[-1][1] if (a.llm and ok_row and comb_rows) else lt)
        miss = "  " + COL[3] + "MISS" + RST if (ok_row and shown != d["tier"]) else ""
        print(line + f"   {DIM}{d.get('note','')[:52]}{RST}{miss}")

    matrix(lex_rows, "LEXICON ONLY")
    if a.llm:
        if not llm_rows:
            print(f"\n{COL[3]}{BOLD}EVERY classifier call failed. No Nemotron or combined "
                  f"score can be computed.{RST}")
            print(f"{DIM}Fix the endpoint or the response parser and re-run.{RST}")
            return 2
        matrix(llm_rows, f"NEMOTRON ONLY  ({len(llm_rows)}/{len(data)} calls succeeded)")
        acc, t3r, t3n = matrix(comb_rows,
                               f"COMBINED  max(lexicon, llm) — escalate-only  "
                               f"({len(comb_rows)}/{len(data)} calls succeeded)")
        print()
        blocking = []
        if failed:
            blocking.append(f"{failed}/{len(data)} classifier calls failed")
        if t3r < t3n:
            blocking.append(f"{t3n - t3r} at-risk caller(s) missed")
        if blocking:
            print(f"{COL[3]}{BOLD}BLOCKING: {'; '.join(blocking)}{RST}")
            print(f"{DIM}A gate that passes while the classifier is failing is worse than "
                  f"no gate. Both conditions must be clean to exit 0.{RST}")
            return 1
        print(f"{COL[1]}{BOLD}PASS{RST} — all {len(data)} calls classified, no at-risk misses")
        return 0
    print(f"\n{DIM}Run with --llm once vLLM is reachable to score the full stack.{RST}")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

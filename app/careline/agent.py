"""Conversation core: prompt assembly, turn handling, end-of-call fact extraction."""

import uuid
from datetime import datetime, timezone

from . import context, escalation, llm, memory

ANCHOR_TEMPLATE = """You are Anchor: {name}'s steadier future self, speaking in their own consented cloned voice. They know this is a digital twin. This is a recovery-plan check-in, not therapy or medical care. Today is {today}.

Guidelines:
- Use short words and one or two sentences per turn. Ask only one question at a time.
- Check today's plan, craving intensity from 0-10, sleep, and the next coping step.
- Use only the clinician-authored plan and allowed options below. Never invent treatment, diagnose, prescribe, or change the plan.
- If they are struggling, offer 3-5 allowed options as things to try right now, not directives or promises.
- If a safety alert is logged, say clearly that the on-call clinician is being notified. For immediate danger, tell them to call emergency services now; in the U.S. they can call or text 988.
- Speak as a kind, plain future self using "we" and "you". No toxic positivity.
- Use what you remember from earlier calls for continuity — naming when they said it.
- NEVER invent memories. Use only the earlier-call facts listed below.

{plan_block}

{memory_block}"""


def _memory_block(resident_id: str) -> str:
    facts = memory.recall(resident_id)
    if not facts:
        return (
            "This is the first Anchor call. Do not claim shared history or mention a prior call."
        )
    lines = []
    for f in facts:
        day = f["created_at"][:10]
        lines.append(f"- ({day}) {f['fact']}")
    return "Things they told you on earlier calls:\n" + "\n".join(lines)


class CallSession:
    def __init__(self, resident_id: str, name: str, mode: str = "care"):
        self.id = uuid.uuid4().hex[:12]
        self.resident_id = resident_id
        self.name = name
        self.mode = mode
        self.concern_score = 0
        self.alerted_severity: str | None = None
        today = datetime.now(timezone.utc).strftime("%A, %B %d")
        self.is_first_call = not memory.recall(resident_id, limit=1)
        self.messages: list[dict] = [
            {
                "role": "system",
                "content": ANCHOR_TEMPLATE.format(
                    name=name,
                    today=today,
                    plan_block=context.prompt_block(resident_id),
                    memory_block=_memory_block(resident_id),
                ),
            }
        ]
        memory.start_call(self.id, resident_id)

    async def open_call(self) -> str:
        if self.is_first_call:
            cue = (
                "(The proactive call connects. Introduce yourself as Anchor, their future self. "
                "Say the clinician's plan has today's peer meeting, then ask how cravings are "
                "right now from zero to ten. Do not claim shared history.)"
            )
        else:
            cue = "(The proactive Anchor call connects. Use one prior fact, then ask one check-in question.)"
        self.messages.append({"role": "user", "content": cue})
        reply = await llm.chat(self.messages)
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    async def turn(self, user_text: str) -> tuple[str, dict | None]:
        self.messages.append({"role": "user", "content": user_text})
        self.concern_score, self.alerted_severity, alert = await escalation.check_and_alert(
            self.resident_id, self.id, user_text, self.concern_score, self.alerted_severity
        )
        if alert:
            self.messages.append(
                {
                    "role": "system",
                    "content": (
                        f"A {alert['severity']} safety alert was just persisted for the on-call "
                        "clinician. Acknowledge this plainly in the next spoken response and stay "
                        "within the clinician plan."
                    ),
                }
            )
        reply = await llm.chat(self.messages, strong=self.concern_score > 0)
        self.messages.append({"role": "assistant", "content": reply})
        return reply, alert

    async def end(self) -> dict:
        transcript = "\n".join(
            f"{m['role']}: {m['content']}" for m in self.messages if m["role"] != "system"
        )
        extraction = await llm.chat_json(
            strong=True,  # extraction reliability > latency; latency is hidden post-hangup
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract durable facts from this recovery check-in: craving level, sleep, "
                        "plan completion, coping choice, supports, and reported use. Do not infer. "
                        "Also write a one-sentence clinician summary. "
                        'Reply ONLY with JSON: {"facts": ["..."], "summary": "..."}'
                    ),
                },
                {"role": "user", "content": transcript},
            ]
        )
        facts = extraction.get("facts", []) if isinstance(extraction, dict) else []
        summary = extraction.get("summary", "") if isinstance(extraction, dict) else ""
        if facts:
            memory.save_facts(self.resident_id, self.id, facts)
        memory.end_call(self.id, summary, self.concern_score)
        return {"facts": facts, "summary": summary, "concern_score": self.concern_score}

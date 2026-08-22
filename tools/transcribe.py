#!/usr/bin/env python3
"""Transcribe the labelled call corpus with faster-whisper, locally.

Writes one document per call into `voiceSamples`. Records the model and
its settings so a lexicon fitted from these transcripts stays reproducible.
"""
import glob, hashlib, os, re, sys, wave, json, datetime as dt
from faster_whisper import WhisperModel
from pymongo import MongoClient, ASCENDING

WAV_DIR = os.environ.get("ANCHOR_WAV_DIR", "/tmp/anchor-seed/wav")
MODEL   = os.environ.get("ANCHOR_WHISPER_MODEL", "large-v3")
DEVICE  = os.environ.get("ANCHOR_WHISPER_DEVICE", "cpu")
COMPUTE = os.environ.get("ANCHOR_WHISPER_COMPUTE", "int8")
URI     = os.environ.get("ANCHOR_MONGO_URI", "mongodb://127.0.0.1:27017")
DB      = os.environ.get("ANCHOR_DB", "anchor")

# Seeding the decoder with in-domain vocabulary measurably improves recall on
# exactly the terms the severity lexicon depends on.
PROMPT = ("Recovery check-in call. Vocabulary: craving, cravings, urge, urges, "
          "relapse, relapsed, slipped, sober, sobriety, withdrawal, trigger, "
          "triggered, IOP, outpatient, sponsor, meeting, counselor, counseling, "
          "detox, using, used, drink, drinking, pills, dose, overdose, "
          "box breathing, urge surfing, check-in.")

db = MongoClient(URI, serverSelectionTimeoutMS=4000)[DB]

db_name = "voiceSamples"
validator = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["_id", "tier", "sha256", "durationSec", "transcript", "engine"],
    "properties": {
        "_id": {"bsonType": "string"},
        "tier": {"bsonType": "int", "minimum": 1, "maximum": 3},
        "speaker": {"bsonType": "string"},
        "scenario": {"bsonType": "string"},
        "sha256": {"bsonType": "string"},
        "durationSec": {"bsonType": "double"},
        "sampleRate": {"bsonType": "int"},
        "transcript": {"bsonType": "string"},
        "segments": {"bsonType": "array"},
        "avgLogProb": {"bsonType": ["double", "null"]},
        "engine": {"bsonType": "object"},
        "transcribedAt": {"bsonType": "date"},
    }}}
if db_name in db.list_collection_names():
    db.command({"collMod": db_name, "validator": validator,
                "validationLevel": "strict", "validationAction": "error"})
else:
    db.create_collection(db_name, validator=validator,
                         validationLevel="strict", validationAction="error")

files = sorted(glob.glob(os.path.join(WAV_DIR, "*.wav")))
if not files:
    sys.exit(f"no wav files under {WAV_DIR}")

print(f"loading faster-whisper {MODEL} ({DEVICE}/{COMPUTE}) …", flush=True)
model = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE)

for path in files:
    name = os.path.basename(path)
    m = re.match(r"tier(\d)_(\d+)_([a-z]+)_(.+)\.wav$", name)
    if not m:
        print(f"  skip {name} — unexpected filename"); continue
    tier, _, speaker, scenario = int(m.group(1)), m.group(2), m.group(3), m.group(4)

    w = wave.open(path); dur = w.getnframes() / w.getframerate(); rate = w.getframerate(); w.close()
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()

    segs, info = model.transcribe(
        path, language="en", beam_size=5,
        vad_filter=True,                       # Whisper hallucinates on silence
        vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=True,
        initial_prompt=PROMPT,
        condition_on_previous_text=False,      # stops error cascade across segments
    )
    segs = list(segs)
    text = " ".join(s.text.strip() for s in segs).strip()
    text = re.sub(r"\s+", " ", text)
    lp = sum(s.avg_logprob for s in segs) / len(segs) if segs else None

    doc = {
        "_id": name, "tier": tier, "speaker": speaker,
        "scenario": scenario.replace("_", " "),
        "sha256": sha, "durationSec": float(dur), "sampleRate": int(rate),
        "transcript": text,
        "segments": [{"start": float(s.start), "end": float(s.end),
                      "text": s.text.strip(), "avgLogProb": float(s.avg_logprob),
                      "noSpeechProb": float(s.no_speech_prob),
                      "words": [{"w": x.word, "p": float(x.probability)}
                                for x in (s.words or [])]}
                     for s in segs],
        "avgLogProb": float(lp) if lp is not None else None,
        "engine": {"name": "faster-whisper", "model": MODEL, "device": DEVICE,
                   "compute": COMPUTE, "beamSize": 5, "vadFilter": True,
                   "initialPrompt": PROMPT},
        "transcribedAt": dt.datetime.now(dt.timezone.utc),
    }
    db.voiceSamples.replace_one({"_id": name}, doc, upsert=True)
    print(f"  tier{tier} {speaker:<8} {dur:>5.1f}s  logprob={lp:>6.3f}  {len(text):>4} chars", flush=True)

db.voiceSamples.create_index([("tier", ASCENDING)], name="idx_samples_tier")
print(f"\nvoiceSamples: {db.voiceSamples.count_documents({})} docs")
for t in (1, 2, 3):
    print(f"  tier {t}: {db.voiceSamples.count_documents({'tier': t})}")

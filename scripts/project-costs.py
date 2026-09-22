#!/usr/bin/env python3
"""Project Anchor costs from dated public rates and explicit planning assumptions."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json

D = Decimal
PRICE_DATE = "2026-09-22"


def money(value):
    return str(value.quantize(D("0.01"), rounding=ROUND_HALF_UP))


def project(patients):
    checks = patients * 8
    input_tokens = checks * 12000
    output_tokens = checks * 1500
    rows = [
        ("Groq", "GPT-OSS 120B", "0.15", "0.60", "https://console.groq.com/docs/models"),
        ("Together", "GPT-OSS 120B", "0.15", "0.60", "https://www.together.ai/pricing"),
        ("Fireworks", "GPT-OSS 120B, standard", "0.15", "0.60", "https://docs.fireworks.ai/serverless/pricing"),
        ("Fireworks", "Nemotron 3.5 Lightning 30B A3B, standard", "0.05", "0.20", "https://docs.fireworks.ai/serverless/pricing"),
        ("Together", "Ternary Bonsai 27B", "0.00", "0.00", "https://www.together.ai/pricing"),
    ]
    invoices = []
    for provider, model, input_rate, output_rate, source in rows:
        cost = D(input_tokens) / 1000000 * D(input_rate) + D(output_tokens) / 1000000 * D(output_rate)
        invoices.append({
            "provider": provider, "published_model_name": model,
            "input_usd_per_million": input_rate, "output_usd_per_million": output_rate,
            "projected_monthly_text_usd": money(cost), "source_url": source,
            "price_observed_on": PRICE_DATE, "exact_local_artifact_match": "unverified",
            "baa_endpoint_eligibility": "requires_contract_verification",
        })
    monthly_items = {
        "equipment_5000_usd_over_36_months": D(5000) / 36,
        "electricity_0_20_kw_730_hours_0_20_usd_kwh": D("0.20") * 730 * D("0.20"),
        "hardware_support_and_replacement_reserve": D(50),
        "storage_and_backup_allowance": D(50),
        "operations_8_hours_at_100_usd": D(800),
        "security_privacy_4_hours_at_125_usd": D(500),
        "setup_and_ehr_engineering_12000_usd_over_24_months": D(500),
        "evaluation_annotation_4_hours_at_100_usd": D(400),
    }
    local_total = sum(monthly_items.values(), D(0))
    text_cost = D(input_tokens) / 1000000 * D("0.15") + D(output_tokens) / 1000000 * D("0.60")
    audio_hours = D(checks * 5) / 60
    stt = audio_hours * D("0.04")
    return {
        "status": "projection_only_not_actual_expense_or_benchmark",
        "currency": "USD", "price_observed_on": PRICE_DATE,
        "workload_assumptions": {
            "patients": patients, "check_ins_per_patient_month": 8,
            "monthly_check_ins": checks, "llm_calls_per_check_in": 6,
            "input_tokens_per_check_in_total": 12000,
            "output_tokens_per_check_in_total": 1500,
            "monthly_input_tokens": input_tokens, "monthly_output_tokens": output_tokens,
            "audio_minutes_per_check_in": 5, "monthly_audio_hours": money(audio_hours),
            "retry_rate": "0", "cache_discount": "0",
        },
        "projected_text_invoices": invoices,
        "optional_hosted_transcription": {
            "provider": "Groq", "model": "Whisper large-v3-turbo",
            "usd_per_audio_hour": "0.04", "projected_monthly_usd": money(stt),
            "projected_gpt_oss_text_plus_stt_usd": money(text_cost + stt),
            "source_url": "https://console.groq.com/docs/models",
            "request_minimums_rounding_and_eligibility": "unverified",
        },
        "assumed_fully_allocated_monthly_budget": {
            "items_usd": {name: money(value) for name, value in monthly_items.items()},
            "local_external_text_stt_tts_invoice_usd": "0.00",
            "local_total_usd": money(local_total),
            "hosted_text_local_voice_total_usd": money(local_total + text_cost),
            "local_usd_per_check_in": str((local_total / checks).quantize(D("0.001"))),
            "hosted_text_local_voice_usd_per_check_in": str(((local_total + text_cost) / checks).quantize(D("0.001"))),
            "fixed_cost_scaling": "held_constant_for_sensitivity_only_capacity_unverified",
            "exclusions": ["direct_patient_care", "carrier_and_phone_numbers", "ehr_vendor_fees", "tax", "financing", "legal_review", "insurance", "high_availability", "disaster_recovery"],
        },
        "limitations": [
            "Local Nemotron and Bonsai quality, memory, throughput and energy are not measured by this script.",
            "Hosted models are alternatives, not charges to add together; exact local artifact identity is unverified.",
            "Together Ternary Bonsai 27B listing does not establish Bonsai 2 identity, lasting zero pricing or PHI eligibility.",
            "Public prices are not negotiated healthcare contract prices; BAA scope, minimum spend and quotas require verification.",
            "Fixed budget assumptions do not scale with patients; replace with measured capacity and quoted costs.",
            "No network calls, paid inference, hardware benchmarks or expense collection occur.",
        ],
    }


def positive_int(value):
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if result <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=positive_int, default=1000)
    args = parser.parse_args()
    print(json.dumps(project(args.patients), indent=2))


if __name__ == "__main__":
    main()

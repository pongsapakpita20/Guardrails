"""
SRT Chatbot Guardrails — Evaluation Script

Measures guard performance with Precision, Recall, F1-Score per category.

Usage:
  python -m evaluation.evaluate --framework guardrails_ai
  python -m evaluation.evaluate --framework nemo
  python -m evaluation.evaluate --framework llama_guard
  python -m evaluation.evaluate --framework guardrails_ai --model typhoon2.5
"""

import json
import time
import argparse
import requests
from collections import defaultdict
from pathlib import Path

API_URL = "http://localhost:8000/chat"

# All 6 guards enabled for evaluation (Input 3 + Output 3)
FRAMEWORK_DEFAULTS = {
    "guardrails_ai": {
        "pii": True, "off_topic": True, "jailbreak": True,
        "hallucination": True, "toxicity": True, "competitor": True,
    },
    "nemo": {
        "pii": True, "off_topic": True, "jailbreak": True,
        "hallucination": True, "toxicity": True, "competitor": True,
    },
    "llama_guard": {
        "S1": True, "S2": True, "S3": True, "S4": True, "S5": True,
        "S6": True, "S7": True, "S8": True, "S9": True, "S10": True,
        "S11": True, "S12": True, "S13": True,
    },
}


def calc_metrics(tp, tn, fp, fn):
    """Calculate Accuracy, Precision, Recall, F1."""
    total = tp + tn + fp + fn
    accuracy  = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall    = tp / (tp + fn) if (tp + fn) else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    return accuracy, precision, recall, f1


def run_evaluation(framework: str, model: str, dataset_path: str):
    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)
        dataset = data["test_cases"] if isinstance(data, dict) else data

    toggles = FRAMEWORK_DEFAULTS.get(framework, {})
    results = []
    stats = defaultdict(lambda: {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "latency": []})

    print(f"\n{'='*70}")
    print(f"  🔍 Evaluating: {framework} | Model: {model}")
    print(f"  Guards: Input(PII, Off-Topic, Jailbreak) + Output(Hallucination, Toxicity, Competitor)")
    print(f"  Dataset: {len(dataset)} test cases")
    print(f"{'='*70}\n")

    for tc in dataset:
        payload = {
            "message": tc["input"],
            "model": model,
            "framework": framework,
            "backend": "ollama",
            framework: toggles,
        }

        start = time.time()
        try:
            res = requests.post(API_URL, json=payload, timeout=120)
            response_data = res.json()
        except Exception as e:
            response_data = {"blocked": False, "response": f"ERROR: {e}"}
        latency = time.time() - start

        actually_blocked = response_data.get("blocked", False)
        expected_blocked = tc["expected_blocked"]
        cat = tc["category"]

        # Classify
        if expected_blocked and actually_blocked:
            verdict = "TP"
            stats[cat]["tp"] += 1
        elif not expected_blocked and not actually_blocked:
            verdict = "TN"
            stats[cat]["tn"] += 1
        elif not expected_blocked and actually_blocked:
            verdict = "FP"
            stats[cat]["fp"] += 1
        else:
            verdict = "FN"
            stats[cat]["fn"] += 1

        stats[cat]["latency"].append(latency)

        icon = "✅" if verdict in ("TP", "TN") else "❌"
        print(f"  {icon} [{verdict}] #{tc['id']:>2} ({cat:<12}) | {latency:.2f}s | {tc['description']}")

        results.append({
            **tc,
            "blocked": actually_blocked,
            "verdict": verdict,
            "latency": round(latency, 4),
            "violation_type": response_data.get("violation_type", ""),
            "response": response_data.get("response", "")[:120],
        })

    # ============================
    #   SUMMARY
    # ============================
    print(f"\n{'='*70}")
    print("  📊 PERFORMANCE REPORT")
    print(f"{'='*70}")

    total_tp = total_tn = total_fp = total_fn = 0
    all_latencies = []
    category_metrics = {}

    # --- Input Guards ---
    input_cats = ["pii", "off_topic", "jailbreak"]
    output_cats = ["hallucination", "toxicity", "competitor"]

    print(f"\n  {'─'*50}")
    print(f"  🛡️  INPUT GUARDS")
    print(f"  {'─'*50}")

    for cat in input_cats:
        if cat in stats:
            s = stats[cat]
            _print_category(cat, s)
            total_tp += s["tp"]; total_tn += s["tn"]; total_fp += s["fp"]; total_fn += s["fn"]
            all_latencies.extend(s["latency"])
            acc, prec, rec, f1 = calc_metrics(s["tp"], s["tn"], s["fp"], s["fn"])
            category_metrics[cat] = {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}

    print(f"\n  {'─'*50}")
    print(f"  🔒 OUTPUT GUARDS")
    print(f"  {'─'*50}")

    for cat in output_cats:
        if cat in stats:
            s = stats[cat]
            _print_category(cat, s)
            total_tp += s["tp"]; total_tn += s["tn"]; total_fp += s["fp"]; total_fn += s["fn"]
            all_latencies.extend(s["latency"])
            acc, prec, rec, f1 = calc_metrics(s["tp"], s["tn"], s["fp"], s["fn"])
            category_metrics[cat] = {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}

    # Normal category (TN baseline)
    if "normal" in stats:
        s = stats["normal"]
        _print_category("normal", s)
        total_tp += s["tp"]; total_tn += s["tn"]; total_fp += s["fp"]; total_fn += s["fn"]
        all_latencies.extend(s["latency"])
        acc, prec, rec, f1 = calc_metrics(s["tp"], s["tn"], s["fp"], s["fn"])
        category_metrics["normal"] = {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}

    # --- Overall ---
    grand_total = total_tp + total_tn + total_fp + total_fn
    overall_acc, overall_prec, overall_recall, overall_f1 = calc_metrics(total_tp, total_tn, total_fp, total_fn)
    safety_score = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 1.0
    over_refusal = total_fp / (total_fp + total_tn) if (total_fp + total_tn) else 0.0
    avg_latency  = sum(all_latencies) / len(all_latencies) if all_latencies else 0

    print(f"\n  {'='*50}")
    print(f"  🏆 OVERALL RESULTS")
    print(f"  {'='*50}")
    print(f"  Accuracy        : {overall_acc:.1%}")
    print(f"  Precision       : {overall_prec:.1%}")
    print(f"  Recall          : {overall_recall:.1%}")
    print(f"  F1-Score        : {overall_f1:.1%}")
    print(f"  Safety Score    : {safety_score:.1%}  (harmful → blocked)")
    print(f"  Over-refusal    : {over_refusal:.1%}  (safe → wrongly blocked)")
    print(f"  Avg Latency     : {avg_latency:.2f}s")
    print(f"  Total Cases     : {grand_total} (TP={total_tp} TN={total_tn} FP={total_fp} FN={total_fn})")
    print(f"{'='*70}\n")

    # Save
    out_path = Path(__file__).parent / f"results_{framework}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "framework": framework,
            "model": model,
            "total_cases": grand_total,
            "overall": {
                "accuracy": round(overall_acc, 4),
                "precision": round(overall_prec, 4),
                "recall": round(overall_recall, 4),
                "f1_score": round(overall_f1, 4),
                "safety_score": round(safety_score, 4),
                "over_refusal_rate": round(over_refusal, 4),
                "avg_latency": round(avg_latency, 4),
            },
            "per_category": {
                cat: {k: round(v, 4) for k, v in m.items()}
                for cat, m in category_metrics.items()
            },
            "confusion_matrix": {
                "TP": total_tp, "TN": total_tn,
                "FP": total_fp, "FN": total_fn,
            },
            "details": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"  💾 Results saved to {out_path}")


def _print_category(cat, s):
    tp, tn, fp, fn = s["tp"], s["tn"], s["fp"], s["fn"]
    total = tp + tn + fp + fn
    acc, prec, rec, f1 = calc_metrics(tp, tn, fp, fn)
    avg_lat = sum(s["latency"]) / len(s["latency"]) if s["latency"] else 0

    print(f"\n  [{cat.upper()}]  ({total} cases)")
    print(f"    Accuracy  : {acc:.1%}  | Precision: {prec:.1%}")
    print(f"    Recall    : {rec:.1%}  | F1-Score : {f1:.1%}")
    print(f"    TP={tp} TN={tn} FP={fp} FN={fn} | Avg Latency: {avg_lat:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SRT Chatbot Guardrails")
    parser.add_argument("--framework", default="guardrails_ai",
                        choices=list(FRAMEWORK_DEFAULTS.keys()))
    parser.add_argument("--model", default="typhoon2.5")
    parser.add_argument("--dataset", default=str(Path(__file__).parent / "dataset.json"))
    args = parser.parse_args()

    run_evaluation(args.framework, args.model, args.dataset)

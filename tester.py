import json

def run_test(reference_file="dataset_reference.json", results_file="analysis_results.json"):
    try:
        with open(reference_file, "r", encoding="utf-8") as f:
            ref_data = {item["id"]: item["reference_data"] for item in json.load(f)}
        with open(results_file, "r", encoding="utf-8") as f:
            res_data = {item["id"]: item["analysis"] for item in json.load(f)}
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    total = len(res_data)
    correct_satisfaction = 0
    mismatches = []

    for idx, analysis in res_data.items():
        if idx not in ref_data:
            continue
        
        true_val = ref_data[idx]["true_satisfaction"]
        pred_val = analysis.get("satisfaction")

        if true_val == pred_val:
            correct_satisfaction += 1
        else:
            mismatches.append({
                "id": idx,
                "true": true_val,
                "pred": pred_val,
                "scenario": ref_data[idx]["true_scenario"]
            })

    accuracy = (correct_satisfaction / total) * 100 if total > 0 else 0

    print("-" * 30)
    print(f"FINAL ACCURACY: {accuracy:.2f}%")
    print(f"Correct: {correct_satisfaction} / Total: {total}")
    print("-" * 30)

    if mismatches:
        print("\nTOP 5 MISMATCHES (Sample):")
        for m in mismatches:
            print(f"ID {m['id']} | Scenario: {m['scenario']} | Expected: {m['true']} | Got: {m['pred']}")

if __name__ == "__main__":
    run_test()
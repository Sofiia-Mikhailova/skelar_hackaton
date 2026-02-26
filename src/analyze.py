import json
import time
import re
from llm_client import LLMClient

def extract_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except:
        return None

def analyze_support_performance(input_file="dataset_clean.json", output_file="analysis_results.json"):
    client = LLMClient() 
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except:
        return

    results = []
    total = len(dataset)

    for index, item in enumerate(dataset, 1):
        print(f"Progress: {index}/{total} | {item.get('customer_name')}", end="\r")

        history = ""
        for m in item.get("messages", []):
            history += f"[{m.get('timestamp', '')}] {m.get('role', '').upper()}: {m.get('text', '')}\n"

        prompt = f"""
        Role: Senior Support Auditor. Analyze the dialogue.
        Logic:
        1. If problem NOT solved but customer says 'thanks/ok', satisfaction is 'unsatisfied'.
        2. Handle fragmented messages (messenger style) as one thought.
        3. Be deterministic. Ignore politeness if task failed.

        DIALOGUE:
        {history}

        RETURN ONLY JSON:
        {{
            "intent": "billing/tech_error/account_access/pricing/shipping/promo_code/other",
            "satisfaction": "satisfied/neutral/unsatisfied",
            "quality_score": 1-5,
            "agent_mistakes": ["ignored_question", "incorrect_info", "rude_tone", "no_resolution", "unnecessary_escalation", "slow_response", "none"],
            "resolution_speed": "fast/average/slow"
        }}
        """

        while True:
            try:
                # Виклик саме моделі 70B
                response = client.get_json_response(prompt, model="llama-3.3-70b-versatile", temperature=0.0)
                
                data = response if isinstance(response, dict) else extract_json(str(response))
                
                if data:
                    results.append({
                        "id": item.get("id"),
                        "customer_name": item.get("customer_name"),
                        "analysis": data
                    })
                    break
            except Exception as e:
                if "429" in str(e):
                    time.sleep(70)
                else:
                    break

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\nDone.")

if __name__ == "__main__":
    analyze_support_performance()
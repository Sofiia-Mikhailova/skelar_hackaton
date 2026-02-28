import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm_client import LLMClient


def extract_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except:
        return None


def chunked(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


def analyze_single(item, client):
    chat_id = item.get("id")
    customer_name = item.get("customer_name", "Unknown")

    history = ""
    for m in item.get("messages", []):
        history += f"[{m.get('timestamp', '')}] {m.get('role', '').upper()}: {m.get('text', '')}\n"

    valid_scenarios = [
        "success", "refund_success", "hidden_dissatisfaction", "agent_error",
        "rude_agent", "ignored_issue", "unnecessary_escalation", "customer_silent",
        "conflict_escalation", "aggressive_customer", "policy_clash"
    ]

    prompt = f"""
        Analyze the following customer support chat and return a structured evaluation.

        The correct customer name is: {customer_name}
        If the agent addressed the customer by ANY other name, that is a wrong_customer_name mistake.

        INTENT:
        - Determine the topic from exactly one of: payment_issue, tech_error, account_access, pricing_plan, refund_request, other.

        SCENARIO:
        - Identify the scenario type. Must be exactly one of: {valid_scenarios}
        - Look carefully for 'hidden_dissatisfaction' — customer uses closing phrases like "ok", "thanks", "fine"
          but the core issue was never actually resolved. This is the hardest case to detect.

        SATISFACTION — use exactly one of: satisfied, neutral, hidden_dissatisfaction, unsatisfied

        The most important rule: customer tone is NOT satisfaction.
        A customer can say "thanks" and still be unsatisfied if their problem wasn't solved.
        A customer can be aggressive and still end up satisfied if the issue was fully resolved.

        Issue resolved and customer is calm or happy → satisfied
        Issue resolved but customer was aggressive → still satisfied, tone doesn't override outcome
        Issue not resolved but customer said "ok/thanks/fine" → hidden_dissatisfaction
        Issue not resolved and customer is visibly frustrated → unsatisfied
        Customer stopped responding after 1-2 messages → neutral
        Agent escalated without trying to solve first → neutral

        SPECIAL CASES:
        - policy_clash: agent correctly refused per company policy. satisfaction = unsatisfied, agent_mistakes = []
        - conflict_escalation: agent stayed calm and followed protocol. satisfaction = unsatisfied, agent_mistakes = []

        QUALITY SCORE (1-5):
        1 = rude agent OR security violation (asked for password), or zero help provided
        2 = major mistake: wrong info, ignored question, unnecessary escalation, wrong customer name (expected: {customer_name})
        3 = issue not resolved but agent was helpful / robotic tone / missed side question
        4 = issue resolved, good service, but maybe missed a tiny detail.
        5 = perfect: fast, polite, all questions answered, used name {customer_name} correctly

        AGENT MISTAKES — list any that apply (empty list if none):
        - ignored_question: agent ignored one of the customer's questions
        - incorrect_info: agent provided wrong data or wrong policy
        - rude_tone: agent was rude, passive-aggressive, or dismissive
        - no_resolution: issue was not resolved (do NOT use for policy_clash or conflict_escalation)
        - unnecessary_escalation: agent escalated to supervisor without real need
        - security_violation: agent asked for password or sensitive credentials
        - wrong_customer_name: agent addressed customer by a name other than {customer_name}

        CHAT HISTORY:
        {history}

        RETURN ONLY JSON:
        {{
            "id": {chat_id},
            "intent": "...",
            "scenario": "...",
            "satisfaction": "...",
            "quality_score": ...,
            "agent_mistakes": [...]
        }}
        """

    while True:
        try:
            response = client.get_json_response(
                prompt,
                model="llama-3.3-70b-versatile",
                temperature=0
            )

            data = response if isinstance(response, dict) else extract_json(str(response))

            if data:
                return {
                    "id": chat_id,
                    "customer_name": customer_name,
                    "analysis": data
                }

        except Exception as e:
            if "429" in str(e):
                time.sleep(5)
            else:
                return None


def analyze_support_performance(input_file="dataset_clean.json", output_file="analysis_results.json"):
    client = LLMClient()

    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    batches = list(chunked(dataset, 5))

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for batch in batches:
            for item in batch:
                futures.append(executor.submit(analyze_single, item, client))

        total = len(futures)
        done = 0

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
                done += 1
                print(f"Processed: {done}/{total}", end="\r")

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)

    results.sort(key=lambda x: x["id"])

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    analyze_support_performance()

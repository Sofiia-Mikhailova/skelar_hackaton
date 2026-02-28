import json
import time
import random
from faker import Faker
from llm_client import LLMClient

fake = Faker()

def generate_skelar_dataset(count=150):
    client = LLMClient()
    dataset_clean = []
    dataset_reference = []
    
    topics = ["payment_issue", "tech_error", "account_access", "pricing_plan", "refund_request", "other"]
    scenarios = [
        {"type": "success", "label": "satisfied", "mistake": "none"},
        {"type": "refund_success", "label": "satisfied", "mistake": "none"},
        {"type": "hidden_dissatisfaction", "label": "hidden_dissatisfaction", "mistake": "no_resolution"},  # ← changed
        {"type": "agent_error", "label": "unsatisfied", "mistake": "incorrect_info"},
        {"type": "rude_agent", "label": "unsatisfied", "mistake": "rude_tone"},
        {"type": "ignored_issue", "label": "unsatisfied", "mistake": "ignored_question"},
        {"type": "unnecessary_escalation", "label": "neutral", "mistake": "unnecessary_escalation"},  # ← changed
        {"type": "customer_silent", "label": "neutral", "mistake": "none"},
        {"type": "conflict_escalation", "label": "unsatisfied", "mistake": "none"},
        {"type": "aggressive_customer", "label": "satisfied", "mistake": "none"},
        {"type": "policy_clash", "label": "unsatisfied", "mistake": "none"}
    ]


    half = count // 2
    satisfied_pool = [s for s in scenarios if s["label"] == "satisfied"]
    problematic_pool = [s for s in scenarios if s["label"] != "satisfied"]
    
    task_scenarios = (
        [random.choice(satisfied_pool) for _ in range(half)] +
        [random.choice(problematic_pool) for _ in range(count - half)]
    )
    random.shuffle(task_scenarios)

    generated_count = 0
    while generated_count < count:
        scenario = task_scenarios[generated_count]
        topic = random.choice(topics)
        customer_name = fake.name()
        is_messenger = random.choice([True, False])
        should_split = random.choice([True, False]) if is_messenger else False

        prompt = f"""
        Generate a unique customer support chat.
        Topic: {topic}. Scenario: {scenario['type']}. Target Satisfaction: {scenario['label']}. Agent mistake: {scenario['mistake']}.
        
        TOPIC LOGIC:
        - If the topic is not one of payment_issue, tech_error, account_access, pricing_plan, refund_request, set topic = 'other'.

        MISTAKE & SATISFACTION LOGIC:

        MISTAKE RULES:
        - If 'hidden_dissatisfaction': Customer says "thanks" or "ok", but issue NOT solved.
        - If 'rude_tone': Agent must be rude, passive-aggressive or dismissive.
        - If 'incorrect_info': Agent provides wrong data/policy.
        - If 'ignored_question': Agent ignores one of the customer's questions.
        - If 'unnecessary_escalation': Agent escalates to supervisor/support tier without real need, even though issue could be solved directly.

        SATISFACTION LABELS — use exactly one of: satisfied, neutral, hidden_dissatisfaction, unsatisfied

        - satisfied: issue fully resolved, customer happy (even if they were aggressive initially).
        - neutral: customer went silent OR agent escalated unnecessarily without resolving.
        - hidden_dissatisfaction: customer says "ok", "thanks", "fine" BUT issue was NOT actually resolved. Surface tone looks positive, real outcome is negative.
        - unsatisfied: issue unresolved AND customer is clearly frustrated/angry, OR agent made a major mistake (rude_tone, incorrect_info, ignored_question).

        CRITICAL RULES:
        - Customer tone alone does NOT determine satisfaction. Final satisfaction depends on whether the issue was actually resolved.
        - hidden_dissatisfaction ≠ unsatisfied. Do NOT use unsatisfied when customer is politely accepting an unresolved issue.
        - If problem NOT solved = at minimum hidden_dissatisfaction, or unsatisfied if customer is visibly frustrated.
        - Aggressive customer tone alone does NOT mean unsatisfied — if issue resolved → satisfied.
        - policy_clash and conflict_escalation → unsatisfied (situation-driven, not agent error).
        
        CONFLICT & PROBLEM LOGIC:
        - If 'conflict_escalation': Customer is extremely frustrated, uses CAPS, and demands to speak with a supervisor/manager. Agent must stay calm and follow protocol.
        - If 'aggressive_customer': Customer MUST be truly aggressive (threats to leave, legal action, insults, "I'll go to social media"). IMPORTANT: Aggressive tone alone does NOT mean unsatisfied. If the issue is fully resolved, final satisfaction can still be 'satisfied'.
        - If 'policy_clash': Customer wants a refund or feature that is explicitly against company policy. The conflict arises from the agent saying "No" professionally.
        
        CUSTOMER RULES:
        1. BE HUMAN: Use slang, casual language, emotional punctuation (!!!, ?). 
        2. NO REPETITION: Do NOT use "I appreciate it" or "I guess". Use: "cool", "fine", "noted", "thx", "ok then", "finally".
        3. SPLIT MESSAGES: {"ACTIVATE SPLIT: The customer MUST send greeting and the problem as 2-3 separate messages (e.g. 'hi' then 'i have a problem')." if should_split else "Keep messages as single blocks."}
        4. STYLE: {"Messenger (typos, no caps, short)" if is_messenger else "Informal but clear"}.
        5. TIMESTAMPS: Year is 2026. Use YYYY-MM-DD HH:MM:SS. If messages are split, interval is 2-5 seconds.

        AGENT RULES:
        1. PROFESSIONAL TONE: Always polite, formal, and helpful (UNLESS 'rude_tone' is specified).
        2. GRAMMAR: Agent ALWAYS uses proper capitalization (starts sentences with Upper Case). NO SLANG.
        3. SECURITY: Agent NEVER asks for passwords or sensitive credentials.
        4. IDENTITY: Agent MUST address the customer only as {customer_name}.
        5. ESCALATION: If agent transfers to supervisor without trying to solve the issue first, the label is 'neutral' and quality_score is 2.
        6. NO "(pause)". If agent needs time, they write: "Please wait a moment while I check this for you." and then provide the actual answer in a NEW separate message.
        7. INACTIVITY LOGIC: If scenario is 'customer_silent':
           - The customer MUST send exactly 1-2 messages and then STOP responding.
           - Agent asks if user is there, warns about closing, then closes.
        8. MULTI-QUESTION: If the customer asks a side question, agent must answer it sequentially.

        STRICT JSON RULES:
        - Message objects MUST only contain "role", "text", and "timestamp".

        Return ONLY JSON:
        {{
            "id": {generated_count + 1},
            "customer_name": "{customer_name}",
            "quality_score": 1-5,
            "messages": [
                {{"role": "customer", "text": "...", "timestamp": "2026-..."}},
                {{"role": "agent", "text": "...", "timestamp": "2026-..."}}
            ]
        }}
        """

        try:
            chat_data = client.get_json_response(
                prompt,
                model="llama-3.1-8b-instant",
                temperature=0.8
            )
            
            if isinstance(chat_data, dict) and chat_data.get("messages"):
                valid_messages = []
                for m in chat_data["messages"]:
                    if isinstance(m, dict) and "text" in m:
                        valid_messages.append({
                            "role": m.get("role"),
                            "text": m.get("text"),
                            "timestamp": m.get("timestamp")
                        })
                
                if not valid_messages:
                    continue

                item = {
                    "id": generated_count + 1,
                    "customer_name": customer_name,
                    "messages": valid_messages
                }
                
                ref_item = item.copy()
                ref_item["reference_data"] = {
                    "topic": topic,
                    "behavior": "messenger" if is_messenger else "structured",
                    "scenario": scenario["type"],
                    "label": scenario["label"],
                    "mistake": scenario["mistake"],
                    "quality_score": chat_data.get("quality_score", 3)
                }
                
                dataset_clean.append(item)
                dataset_reference.append(ref_item)
                generated_count += 1
                print(f"Chat #{generated_count} generated (2026)")

        except Exception as e:
            if "429" in str(e):
                time.sleep(60)
            continue

    with open("dataset_clean.json", "w", encoding="utf-8") as f:
        json.dump(dataset_clean, f, ensure_ascii=False, indent=4)
    with open("dataset_reference.json", "w", encoding="utf-8") as f:
        json.dump(dataset_reference, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    generate_skelar_dataset(150)
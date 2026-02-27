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
        {"type": "hidden_dissatisfaction", "label": "unsatisfied", "mistake": "no_resolution"},
        {"type": "agent_error", "label": "unsatisfied", "mistake": "incorrect_info"},
        {"type": "rude_agent", "label": "unsatisfied", "mistake": "rude_tone"},
        {"type": "ignored_issue", "label": "unsatisfied", "mistake": "ignored_question"},
        {"type": "unnecessary_escalation", "label": "unsatisfied", "mistake": "unnecessary_escalation"},
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

        prompt = f"""
        Generate a unique customer support chat.
        Topic: {topic}. Scenario: {scenario['type']}. Target Satisfaction: {scenario['label']}. Agent mistake: {scenario['mistake']}.
        
        TOPIC LOGIC:
        - If the topic is not one of payment_issue, tech_error, account_access, pricing_plan, refund_request, set topic = 'other'.

        MISTAKE & SATISFACTION LOGIC:
        - If 'hidden_dissatisfaction': Customer says "thanks" or "ok", but issue NOT solved.
        - If 'rude_tone': Agent must be rude, passive-aggressive or dismissive.
        - If 'incorrect_info': Agent provides wrong data/policy.
        - If 'ignored_question': Agent ignores one of the customer's questions.
        - If 'unnecessary_escalation': Agent escalates to supervisor/support tier without real need, even though issue could be solved directly.
        - If problem NOT solved = 'unsatisfied' regardless of customer tone.
        - Customer tone alone does NOT determine satisfaction. Final satisfaction depends on whether the issue was actually resolved.

        QUALITY SCORE (1-5) CALCULATION:
        1 - Rude agent, or zero help provided.
        2 - Major mistakes (wrong info, ignored 50% of questions, unnecessary escalation) or very slow.
        3 - Issue solved but agent was robotic, slow, or ignored a side question.
        4 - Good service, solved the main issue quickly, but maybe missed a tiny detail.
        5 - Perfect! Fast responses, all questions (even side ones) answered, polite.
        
        CONFLICT & PROBLEM LOGIC:
        - If 'conflict_escalation': Customer is extremely frustrated, uses CAPS, and demands to speak with a supervisor/manager. Agent must stay calm and follow protocol.
        - If 'aggressive_customer': Customer uses passive-aggressive comments, threats (social media, legal, or leaving for a competitor).  IMPORTANT: Aggressive tone alone does NOT mean unsatisfied. If the issue is fully resolved, final satisfaction can still be 'satisfied'.
        - If 'policy_clash': Customer wants a refund or feature that is explicitly against company policy. The conflict arises from the agent saying "No" professionally.
        
        CUSTOMER RULES:
        1. BE HUMAN: Use slang, casual language, emotional punctuation (!!!, ?). 
        2. NO REPETITION: Do NOT use "I appreciate it" or "I guess". Use: "cool", "fine", "noted", "thx", "ok then", "finally".
        3. SPLIT MESSAGES: Frequently send 2-3 short messages instead of one long block. If Messenger style, always start with "hi" and the issue separately.
        4. STYLE: {"Messenger (typos, no caps, short)" if is_messenger else "Informal but clear"}.

        AGENT RULES:
        1. PROFESSIONAL TONE: Always polite, formal, and helpful (UNLESS 'rude_tone' is specified). No slang/abbreviations.
        2. NO "(pause)". If agent needs time, they write: "Please wait a moment while I check this for you." and then provide the actual answer in a NEW separate message.
        3. INACTIVITY LOGIC: If scenario is 'customer_silent':
           - Agent asks if user is there.
           - If no reply, agent warns: "I haven't heard from you. I will close this chat in 2 minutes if there's no interaction."
           - If still no reply, agent professionally closes the chat.
        4. MULTI-QUESTION: If the customer asks a side question, agent must answer it sequentially.

        Return ONLY JSON:
        {{
            "id": {generated_count + 1},
            "customer_name": "{customer_name}",
            "quality_score": 1-5,
            "messages": [
                {{"role": "customer", "text": "...", "timestamp": "..."}},
                {{"role": "agent", "text": "...", "timestamp": "..."}}
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
                valid_messages = [m for m in chat_data["messages"] if isinstance(m, dict) and "text" in m]
                
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
                print(f"Chat #{generated_count} generated")

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
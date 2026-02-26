import json
import time
import random
from datetime import datetime, timedelta
from faker import Faker
from llm_client import LLMClient

fake = Faker()

def generate_skelar_dataset(count=150):
    client = LLMClient()
    dataset_clean = []
    dataset_reference = []
    
    topics = ["billing", "tech_error", "account_access", "pricing", "shipping", "promo_code"]
    
    scenarios = [
        {"type": "success", "label": "satisfied", "mistake": "none"},
        {"type": "refund_success", "label": "satisfied", "mistake": "none"},
        {"type": "hidden_dissatisfaction", "label": "unsatisfied", "mistake": "no_resolution"},
        {"type": "agent_error", "label": "unsatisfied", "mistake": "incorrect_info"},
        {"type": "rude_agent", "label": "unsatisfied", "mistake": "rude_tone"},
        {"type": "ignored_issue", "label": "neutral", "mistake": "ignored_question"},
        {"type": "bad_escalation", "label": "unsatisfied", "mistake": "unnecessary_escalation"}
    ]

    generated_count = 0
    while generated_count < count:
        topic = random.choice(topics)
        scenario = random.choice(scenarios) if generated_count % 2 != 0 else random.choice([s for s in scenarios if s["label"] == "satisfied"])
            
        customer_name = fake.name()
        is_structured = random.choice([True, False])
        customer_style = "Structured, polite" if is_structured else "Messenger style (short messages, typos, slang, no caps)"

        prompt = f"""
        Generate a realistic customer support chat.
        Topic: {topic}. Scenario: {scenario['type']}. 
        Target Satisfaction: {scenario['label']}. Agent mistake: {scenario['mistake']}.
        
        CUSTOMER: {customer_name}, Style: {customer_style}

        STRICT AGENT RULES:
        1. Professional, polite, proper grammar/capitalization.
        2. NO slang, NO typos.
        3. If mistake required ({scenario['mistake']}), stay professional in tone.

        SATISFACTION LOGIC:
        - If 'hidden_dissatisfaction': Customer says "thanks" or "ok", but issue NOT solved. Label: 'unsatisfied'.
        - If problem NOT solved = 'unsatisfied' regardless of customer tone.

        Return ONLY JSON:
        {{
            "id": {generated_count + 1},
            "customer_name": "{customer_name}",
            "messages": [
                {{"role": "customer", "text": "...", "timestamp": "..."}},
                {{"role": "agent", "text": "...", "timestamp": "..."}}
            ]
        }}
        """
        chat_data = client.get_json_response(prompt)
        
        if chat_data and isinstance(chat_data.get("messages"), list) and len(chat_data["messages"]) > 0:
            messages = chat_data["messages"]
            
            clean_item = {
                "id": generated_count + 1,
                "customer_name": customer_name,
                "messages": messages
            }
            
            agent_msgs = [m.get("text", "") for m in messages if isinstance(m, dict) and m.get("role") == "agent"]
            avg_agent_len = sum(len(str(m).split()) for m in agent_msgs) / len(agent_msgs) if agent_msgs else 0
            total_words = sum(len(str(m.get("text", "")).split()) for m in messages if isinstance(m, dict))
            
            ref_item = clean_item.copy()
            ref_item["topic"] = topic
            ref_item["reference_data"] = {
                "customer_behavior": "structured" if is_structured else "messenger",
                "true_scenario": scenario["type"],
                "true_satisfaction": scenario["label"],
                "true_mistake": scenario["mistake"],
                "is_resolved": "no" if scenario["mistake"] in ["no_resolution", "ignored_question"] or scenario["label"] == "unsatisfied" else "yes",
                "metrics": {
                    "message_count": len(messages),
                    "total_word_count": total_words,
                    "avg_agent_response_length": round(avg_agent_len, 2)
                }
            }
            
            dataset_clean.append(clean_item)
            dataset_reference.append(ref_item)
            generated_count += 1
        
        time.sleep(0.1)

    with open("dataset_clean.json", "w", encoding="utf-8") as f:
        json.dump(dataset_clean, f, ensure_ascii=False, indent=4)
    with open("dataset_reference.json", "w", encoding="utf-8") as f:
        json.dump(dataset_reference, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    generate_skelar_dataset(150)
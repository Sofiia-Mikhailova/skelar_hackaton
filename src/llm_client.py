import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            self.client = None
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            self.default_model = "llama-3.1-8b-instant"
        except:
            self.client = None

    def get_json_response(self, prompt, model=None, temperature=0.0):
        if not self.client:
            return None
        
        target_model = model if model else self.default_model
        
        completion = self.client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": "You are a professional assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

if __name__ == "__main__":
    client = LLMClient()
    result = client.get_json_response("Say 'Ready' in JSON", model="llama-3.3-70b-versatile")
    print(result)
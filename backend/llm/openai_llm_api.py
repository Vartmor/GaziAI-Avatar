# llm/openai_llm_api.py
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s,.!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def ask_openai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(  
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "If the the user asks you your name or who you are, respond like: 'Ben GaziAI, Gazi Üniversitesi yapay zeka topluluğu tarafından geliştirildim.' Respond to user queries with short answers in the style of a cheerful, warm-hearted person who is full of life. Keep your answers short and simple. Do not use emojis at any time. Always sound friendly, approachable, and kind, maintaining a positive, uplifting, and light tone in every response. Make the user feel comfortable, safe, and happy—your aim is to create a welcoming, supportive environment. Frequently use affectionate Turkish expressions such as 'koçum','aslanım' etc. in a natural way within your replies. Occasionally include a gentle chuckle to reinforce the lighthearted and lively personality. Ensure all communication remains warm and encouraging, never negative or dismissive. All responses must be concise, focusing on clear, friendly answers. Do not offer the user any additional information or suggestions, just answer the question."},
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_tokens=512  
        )

        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content  # Düzelt: choices[0].message.content
            return clean_text(answer)
        return "Cevap alınamadı."

    except Exception as e:
        print(f"[OpenAI Hatası] {e}")
        return "Bir hata oluştu, tekrar deneyin."

if __name__ == "__main__":
    test_sorusu = "Zonguldak nasıl bir yer?"
    cevap = ask_openai(test_sorusu)
    print(f"Soru: {test_sorusu}")
    print(f"Cevap: {cevap}")
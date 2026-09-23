import os
import json
import base64
import random
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()

if not GEMINI_API_KEY:
    print("❌ ایرر: GEMINI_API_KEY گٹ ہب سیکریٹس میں نہیں ملی یا خالی ہے!")
    exit(1)

if not GH_TOKEN:
    print("❌ ایرر: GH_TOKEN گٹ ہب سیکریٹس میں نہیں ملا یا خالی ہے!")
    exit(1)

headers_gh = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_ai_app():
    categories = [
        "Financial calculator", "Crypto profit utility", "OSINT phone formatter tool",
        "Interactive productivity timer", "2D retro canvas game", "Smart notes markdown editor",
        "Color palette generator for designers", "Workout fitness tracker"
    ]
    chosen_cat = random.choice(categories)
    
    prompt = f"""
    Create a unique, highly polished, beautiful single-page web app in the category: '{chosen_cat}'.
    The app must be completely functional using HTML5, modern CSS, and vanilla JavaScript.
    
    You must respond ONLY with a strict JSON object with this exact structure:
    {{
      "repo_name": "short-clean-kebab-case-name",
      "description": "One line catchy description of the app",
      "html_code": "<!DOCTYPE html>...full working code...",
      "readme": "# App Name\\n\\nDetailed description and how to use it."
    }}
    Do not add markdown codeblocks around the json. Output pure valid JSON only.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"}
    }
    
    res = requests.post(url, json=payload)
    data = res.json()
    
    if "error" in data:
        print(f"❌ جیمینائی ایرر: {data['error'].get('message', 'نامعلوم خرابی')}")
        exit(1)
        
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw_text)

def push_file(owner, repo, path, content, message):
    b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    requests.put(url, headers=headers_gh, json={"message": message, "content": b64_content})

def main():
    user_res = requests.get("https://api.github.com/user", headers=headers_gh)
    if user_res.status_code != 200:
        print("❌ گٹ ہب ٹوکن ایرر: GH_TOKEN درست نہیں ہے یا ایکسپائر ہو گیا ہے!")
        exit(1)
        
    username = user_res.json()["login"]
    
    print("1. جیمینائی سے نیا ایپ آئیڈیا اور کوڈ لیا جا رہا ہے...")
    app_data = get_ai_app()
    repo_name = f"{app_data['repo_name']}-{random.randint(100, 999)}"
    print(f"✅ ایپ تیار ہوئی: {repo_name}")
    
    print("2. نیا گٹ ہب ریپو بنایا جا رہا ہے...")
    create_repo_url = "https://api.github.com/user/repos"
    repo_payload = {
        "name": repo_name,
        "description": app_data.get("description", "Built by 24/7 AI Factory"),
        "auto_init": True
    }
    r = requests.post(create_repo_url, headers=headers_gh, json=repo_payload)
    if r.status_code not in [200, 201]:
        print("❌ ریپو بنانے میں مسئلہ:", r.text)
        return
        
    print("3. کوڈ فائلیں اپ لوڈ کی جا رہی ہیں...")
    push_file(username, repo_name, "index.html", app_data["html_code"], "Add functional web application")
    push_file(username, repo_name, "README.md", app_data["readme"], "Add documentation")
    
    # 4. لائیو ویب سائٹ آن کریں (GitHub Pages)
    pages_url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    requests.post(pages_url, headers=headers_gh, json={"source": {"branch": "main", "path": "/"}})
    
    print(f"🎉 مبارک ہو! نئی ایپ لائیو اپ لوڈ ہو چکی ہے: https://{username}.github.io/{repo_name}/")

if __name__ == "__main__":
    main()

import os
import json
import base64
import random
import requests
import time
import re

# Priority set karna: Sabse pehle GEMINI_API_KEY_2, phir GEMINI_API_KEY aur baqi
keys_list = []
priority_env_names = ["GEMINI_API_KEY_2", "GEMINI_API_KEY", "GEMINI_API_KEY_3"]

for env_name in priority_env_names:
    val = os.environ.get(env_name, "").strip()
    if val and val not in keys_list:
        keys_list.append(val)

# Agar koi combined ya comma wali key ho toh usay bhi add kar lo
raw_combined = os.environ.get("GEMINI_API_KEYS", "")
for k in raw_combined.split(","):
    cleaned = k.strip()
    if cleaned and cleaned not in keys_list:
        keys_list.append(cleaned)

GEMINI_API_KEYS = keys_list
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()

if not GEMINI_API_KEYS or not GH_TOKEN:
    print("❌ Error: Kam az kam aik API key aur GH_TOKEN lazmi hai!")
    exit(1)

print(f"🔑 Total {len(GEMINI_API_KEYS)} API Key(s) detect ho gayi hain. (By default pehle GEMINI_API_KEY_2 use hogi)")

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
    
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash"
    ]
    
    exhausted_keys = set()
    attempt_round = 1

    while True:
        print(f"\n🔄 --- Koshish Round {attempt_round} shuru ho rahi hai ---")
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
        
        if len(exhausted_keys) >= len(GEMINI_API_KEYS):
            print("⏳ Tamam API keys ki limit filhal khatam ho chuki hai. 20 seconds wait karke dobara koshish karte hain...")
            time.sleep(20)
            exhausted_keys.clear()
            attempt_round += 1
            continue

        for key_index, api_key in enumerate(GEMINI_API_KEYS):
            if key_index in exhausted_keys:
                continue
                
            # Pehli key yahan GEMINI_API_KEY_2 hogi (kyunki humne priority upar rakh di hai)
            key_label = "GEMINI_API_KEY_2" if key_index == 0 else f"API Key #{key_index + 1}"
            print(f"\n🔑 {key_label} test ki ja rahi hai...")
            
            for model_name in models_to_try:
                print(f"🎯 Model: {model_name}...")
                url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"}
                }
                
                try:
                    res = requests.post(url, json=payload, timeout=30)
                    data = res.json()
                    
                    if "error" not in data and "candidates" in data:
                        print(f"✅ Kamyabi! Model '{model_name}' ne {key_label} ke sath response de diya!")
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        try:
                            return json.loads(raw_text, strict=False)
                        except json.JSONDecodeError:
                            cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', raw_text)
                            return json.loads(cleaned_text, strict=False)
                    else:
                        err_obj = data.get("error", {})
                        err_msg = err_obj.get("message", "Error")
                        print(f"⚠️ {model_name} par response: {err_msg}")
                        
                        if "quota" in err_msg.lower() or "limit" in err_msg.lower() or "exceeded" in err_msg.lower():
                            print(f"⚡ {key_label} ki limit khatam ho chuki hai! Foran agli key par shift ho rahe hain...")
                            exhausted_keys.add(key_index)
                            break
                except Exception as e:
                    print(f"⚠️ Connection error: {e}")
                
                time.sleep(1)
        
        attempt_round += 1

def push_file(owner, repo, path, content, message):
    b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    requests.put(url, headers=headers_gh, json={"message": message, "content": b64_content})

def main():
    user_res = requests.get("https://api.github.com/user", headers=headers_gh)
    if user_res.status_code != 200:
        print("❌ GitHub Token Error: GH_TOKEN durust nahi hai!")
        exit(1)
        
    username = user_res.json()["login"]
    
    print("1. Gemini se naya app idea aur code liya ja raha hai...")
    app_data = get_ai_app()
    repo_name = f"{app_data['repo_name']}-{random.randint(100, 999)}"
    print(f"✅ App tayar hui: {repo_name}")
    
    print("2. Naya GitHub repo banaya ja raha hai...")
    create_repo_url = "https://api.github.com/user/repos"
    repo_payload = {
        "name": repo_name,
        "description": app_data.get("description", "Built by 24/7 AI Factory"),
        "auto_init": True
    }
    r = requests.post(create_repo_url, headers=headers_gh, json=repo_payload)
    if r.status_code not in [200, 201]:
        print("❌ Repo banane mein masla:", r.text)
        return
        
    print("3. Code files upload ki ja rahi hain...")
    push_file(username, repo_name, "index.html", app_data["html_code"], "Add functional web application")
    push_file(username, repo_name, "README.md", app_data["readme"], "Add documentation")
    
    pages_url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    requests.post(pages_url, headers=headers_gh, json={"source": {"branch": "main", "path": "/"}})
    
    print(f"🎉 Mubarak ho! Nayi app live upload ho chuki hai: https://{username}.github.io/{repo_name}/")

if __name__ == "__main__":
    main()

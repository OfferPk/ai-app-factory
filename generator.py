import os
import json
import base64
import random
import requests
import time
import re

# Multiple API keys support (agar comma se separate karke dein)
raw_keys = os.environ.get("GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEY", ""))
GEMINI_API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()

if not GEMINI_API_KEYS or not GH_TOKEN:
    print("❌ Error: GEMINI_API_KEY ya GH_TOKEN khali hai!")
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
    
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash"
    ]
    
    # Infinite/Smart retry loop jab tak success na ho jaye
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
        
        # Har key ko check karein
        for key_index, api_key in enumerate(GEMINI_API_KEYS):
            print(🔑 API Key #{key_index + 1} istemal ki ja rahi hai...)
            
            for model_name in models_to_try:
                print(f"🎯 Test kiya ja raha hai model: {model_name}...")
                url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"}
                }
                
                try:
                    res = requests.post(url, json=payload, timeout=30)
                    data = res.json()
                    
                    if "error" not in data and "candidates" in data:
                        print(f"✅ Gemini model '{model_name}' kamyabi se connect ho gaya!")
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        try:
                            return json.loads(raw_text, strict=False)
                        except json.JSONDecodeError:
                            cleaned_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', raw_text)
                            return json.loads(cleaned_text, strict=False)
                    else:
                        err_msg = data.get("error", {}).get("message", "Error")
                        print(f"⚠️ {model_name} par response: {err_msg}")
                except Exception as e:
                    print(f"⚠️ {model_name} fail hua: {e}")
                
                # Model ke darmiyan chota waqfa
                time.sleep(2)
        
        print("⏳ Sabhi models aur keys par filhal high demand hai. 10 seconds baad dobara try karte hain...")
        time.sleep(10)
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
    
    # 4. Live website on karein (GitHub Pages)
    pages_url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    requests.post(pages_url, headers=headers_gh, json={"source": {"branch": "main", "path": "/"}})
    
    print(f"🎉 Mubarak ho! Nayi app live upload ho chuki hai: https://{username}.github.io/{repo_name}/")

if __name__ == "__main__":
    main()

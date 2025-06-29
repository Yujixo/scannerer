import requests, time, json, os

GIST_TOKEN = os.getenv("GH_GIST_TOKEN")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
HEADERS = {"Authorization": f"token {GIST_TOKEN}"}
PROCESSED_FILE = "processed.json"

def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(json.load(f))

def save_processed(ids):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(ids), f)

def fetch_recent_scripts():
    res = requests.get("https://scriptblox.com/api/script/recent")
    return res.json().get("result", [])

def download_script(script_url):
    try:
        script_id = script_url.strip().split("/")[-1]
        api_url = f"https://rawscripts.net/raw/{script_id}"
        res = requests.get(api_url)
        try:
            if res.headers.get("Content-Type", "").startswith("application/json"):
                error = res.json().get("message")
                print(f"Error for {script_id}: {error}")
                return None
        except Exception:
            pass
        return res.text if res.status_code == 200 else None
    except Exception as e:
        print(f"Failed to fetch script: {e}")
        return None

def upload_to_gist(title, content):
    data = {
        "description": title,
        "public": True,
        "files": {
            f"{title}.lua": {"content": content}
        }
    }
    res = requests.post("https://api.github.com/gists", headers=HEADERS, json=data)
    return res.json().get("html_url")

def send_discord_notification(game, title, slug, gist_url):
    roblox_url = f"https://www.roblox.com/games/{game['gameId']}"
    scriptblox_url = f"https://scriptblox.com/script/{slug}"
    message = {
        "content": f"✅ **New Script Uploaded!**\n\n🎮 Game: [{game['name']}]({roblox_url})\n📜 Title: [{title}]({scriptblox_url})\n🔗 Gist: {gist_url}"
    }
    requests.post(DISCORD_WEBHOOK, json=message)

def main():
    processed_ids = load_processed()
    new_processed = set()

    for script in fetch_recent_scripts():
        script_id = script["_id"]
        if script_id in processed_ids:
            continue

        raw_url = script.get("script")
        content = download_script(raw_url)
        if not content:
            continue

        gist_url = upload_to_gist(script["title"], content)
        if gist_url:
            send_discord_notification(script["game"], script["title"], script["slug"], gist_url)
            print(f"Processed: {script['title']}")
            new_processed.add(script_id)

    save_processed(processed_ids.union(new_processed))

if __name__ == "__main__":
    main()

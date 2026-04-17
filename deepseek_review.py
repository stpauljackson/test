import os
import requests
import subprocess

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_REF = os.getenv("BASE_REF", "main")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set")

def get_git_diff():
    try:
        base = f"origin/{BASE_REF}"

        # ensure base exists
        subprocess.run(["git", "fetch", "origin", BASE_REF], check=True)

        diff = subprocess.check_output(
            ["git", "diff", f"{base}...HEAD"],
            text=True
        )
        return diff[:12000]

    except Exception as e:
        return f"Error getting diff: {e}"

def call_llm(diff):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a ruthless senior engineer. Find bugs, security issues, bad design."
            },
            {
                "role": "user",
                "content": f"Review this git diff:\n\n{diff}"
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"API Error: {response.text}")

    return response.json()["choices"][0]["message"]["content"]

def post_comment(review):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    body = {
        "body": f"## 🤖 LLM Code Review\n\n{review[:5000]}"
    }

    print("POSTING TO:", url)

    res = requests.post(url, headers=headers, json=body)

    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)

    if res.status_code not in [200, 201]:
        raise Exception(f"GitHub API error: {res.text}")

def main():
    diff = get_git_diff()

    if not diff.strip():
        print("No diff found.")
        return

    review = call_llm(diff)

    print("\n===== LLM REVIEW =====\n")
    print(review)
    post_comment(review)
    
if __name__ == "__main__":
    main()
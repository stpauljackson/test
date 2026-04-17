import os
import requests
import subprocess

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_REF = os.getenv("BASE_REF", "main")

# 🔥 YOU MISSED THESE
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("PR_NUMBER")
REPO = os.getenv("REPO")

# ---- VALIDATION ----
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not set")

if not PR_NUMBER or not REPO:
    raise ValueError(f"Missing PR context → PR_NUMBER={PR_NUMBER}, REPO={REPO}")

PR_NUMBER = str(PR_NUMBER).strip()
REPO = str(REPO).strip()

print("DEBUG → REPO:", REPO)
print("DEBUG → PR_NUMBER:", PR_NUMBER)

# ---- GIT DIFF ----
def get_git_diff():
    try:
        base = f"origin/{BASE_REF}"

        subprocess.run(["git", "fetch", "origin", BASE_REF], check=True)

        diff = subprocess.check_output(
            ["git", "diff", f"{base}...HEAD"],
            text=True
        )

        return diff[:12000]

    except Exception as e:
        raise Exception(f"Git diff failed: {e}")

# ---- LLM CALL ----
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
                "content": "You are a strict senior reviewer. Be concise. Give actionable issues."
            },
            {
                "role": "user",
                "content": f"Review this git diff:\n\n{diff}"
            }
        ]
    }

    res = requests.post(url, headers=headers, json=payload)

    if res.status_code != 200:
        raise Exception(f"LLM API Error: {res.text}")

    return res.json()["choices"][0]["message"]["content"]

# ---- POST COMMENT ----
def post_comment(review):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    body = {
        "body": f"## 🤖 LLM Code Review\n\n{review[:5000]}"
    }

    print("POST URL:", url)

    res = requests.post(url, headers=headers, json=body)

    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)

    if res.status_code not in [200, 201]:
        raise Exception(f"GitHub API error: {res.text}")

# ---- MAIN ----
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
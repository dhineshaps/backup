import requests
import subprocess
import sys

# -------------------------
# CONFIGURATION
# -------------------------

WORKSPACE = "YOUR_WORKSPACE"
REPO = "YOUR_REPO"
USERNAME = "YOUR_USERNAME"
APP_PASSWORD = "YOUR_APP_PASSWORD"

MAX_LINES_PER_FILE = 200


# -------------------------
# FETCH PR DIFF
# -------------------------

def get_pr_diff(pr_id):

    url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO}/pullrequests/{pr_id}/diff"

    print("Fetching PR diff from Bitbucket...")

    response = requests.get(url, auth=(USERNAME, APP_PASSWORD))

    if response.status_code != 200:
        print("Failed to fetch diff:", response.status_code)
        sys.exit(1)

    return response.text


# -------------------------
# CLEAN AND OPTIMIZE DIFF
# -------------------------

def extract_changes(diff_text):

    clean_changes = []
    current_file = None
    line_count = 0

    for line in diff_text.splitlines():

        if line.startswith("diff --git"):
            parts = line.split(" ")
            current_file = parts[2].replace("a/", "")
            clean_changes.append(f"\nFILE: {current_file}")
            line_count = 0
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+") or line.startswith("-"):

            if line_count < MAX_LINES_PER_FILE:
                clean_changes.append(line)
                line_count += 1

    return "\n".join(clean_changes)


# -------------------------
# RUN COPILOT REVIEW
# -------------------------

def run_copilot_review(change_summary):

    prompt = """
You are a senior software engineer reviewing a pull request.

Review the following code changes and report ONLY serious issues:

- logic bugs
- null pointer risks
- security issues
- memory leaks
- performance problems
- missing error handling

Ignore formatting or style issues.

Return short bullet points.
"""

    print("Running Copilot review...")

    process = subprocess.run(
        ["copilot", "-p", prompt],
        input=change_summary,
        text=True,
        capture_output=True
    )

    return process.stdout


# -------------------------
# MAIN
# -------------------------

def main():

    if len(sys.argv) < 2:
        print("Usage: python ai_pr_review.py <PR_ID>")
        sys.exit(1)

    pr_id = sys.argv[1]

    diff_text = get_pr_diff(pr_id)

    change_summary = extract_changes(diff_text)

    if not change_summary.strip():
        print("No code changes detected.")
        sys.exit(0)

    review = run_copilot_review(change_summary)

    print("\n==========================")
    print("AI PR REVIEW RESULT")
    print("==========================\n")

    print(review)


if __name__ == "__main__":
    main()

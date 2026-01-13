import requests

POLARIS_URL = "https://<your-polaris-domain>"
API_TOKEN = "<your-api-token>"
PROJECT_ID = "<project-uuid>"

url = f"{POLARIS_URL}/api/findings/issues"

params = {
    "projectId": PROJECT_ID,
    "query": "occurrence:severity=in=('medium','low')",
    "_includeOccurrenceProperties": "true",
    "_includeType": "true",
}

headers = {
    "Accept": "application/vnd.polaris.findings.issues-1+json",
    "Api-token": API_TOKEN,
}

response = requests.get(url, headers=headers, params=params)
response.raise_for_status()

data = response.json()

for issue in data.get("items", []):
    occurrence = issue.get("occurrence", {})
    print(
        "Severity:", occurrence.get("severity"),
        "| File:", occurrence.get("filePath"),
        "| Line:", occurrence.get("lineNumber"),
        "| Checker:", issue.get("type", {}).get("checkerName")
    )

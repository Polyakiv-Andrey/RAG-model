import requests
import json




def read_doc():
    """Reads a Confluence page by ID and returns its content."""
    url = f"{CONFLUENCE_URL}/rest/api/content/{PAGE_ID}?expand=body.storage"

    auth = (USERNAME, API_TOKEN)
    headers = {"Accept": "application/json"}

    response = requests.get(url, auth=auth, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        print(response.text)
        return None

    page_data = response.json()
    content = page_data.get("body", {}).get("storage", {}).get("value", "")
    return content


def update_doc(content):
    """Updates a Confluence page by ID with new content."""
    # Fetch the current page data to get the latest version
    url = f"{CONFLUENCE_URL}/rest/api/content/{PAGE_ID}?expand=version"
    auth = (USERNAME, API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, auth=auth, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page version. Status code: {response.status_code}")
        print(response.text)
        return None

    page_data = response.json()
    current_version = page_data.get("version", {}).get("number", 1)

    # Increment version for the update
    new_version = current_version + 1

    # Prepare the update payload
    payload = {
        "version": {
            "number": new_version
        },
        "title": page_data.get("title", "Updated Page"),
        "type": "page",
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }

    # Send the update request
    update_url = f"{CONFLUENCE_URL}/rest/api/content/{PAGE_ID}"
    response = requests.put(update_url, auth=auth, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        print(f"Failed to update page. Status code: {response.status_code}")
        print(response.text)
        return None

    print("Page updated successfully.")
    return response.json()
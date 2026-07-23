"""
post_to_instagram.py

Publishes an already-hosted image to Instagram via the Graph API, two-step:
  1. Create a media container (image URL + caption).
  2. Publish that container.

Requires environment variables:
  IG_USER_ID      -- your Instagram Business/Creator account's numeric ID
  IG_ACCESS_TOKEN -- a long-lived Page access token with
                     instagram_content_publish permission

These are read from the environment (set as GitHub Actions secrets), never
hardcoded.
"""
import os
import sys
import time

import requests

GRAPH_API_VERSION = "v25.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def create_container(ig_user_id: str, access_token: str, image_url: str, caption: str) -> str:
    url = f"{GRAPH_BASE}/{ig_user_id}/media"
    resp = requests.post(url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    })
    resp.raise_for_status()
    return resp.json()["id"]


def publish_container(ig_user_id: str, access_token: str, container_id: str) -> str:
    url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    resp = requests.post(url, data={
        "creation_id": container_id,
        "access_token": access_token,
    })
    resp.raise_for_status()
    return resp.json()["id"]


def wait_until_container_ready(container_id: str, access_token: str, timeout=120, interval=5):
    """Poll the container's status_code until it's FINISHED (Instagram needs
    a moment to fetch/process the image before it can be published)."""
    url = f"{GRAPH_BASE}/{container_id}"
    waited = 0
    while waited < timeout:
        resp = requests.get(url, params={"fields": "status_code", "access_token": access_token})
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"Container {container_id} failed processing.")
        time.sleep(interval)
        waited += interval
    raise TimeoutError(f"Container {container_id} not ready after {timeout}s.")


def post_image(image_url: str, caption: str) -> str:
    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    print(f"Creating media container for {image_url}")
    container_id = create_container(ig_user_id, access_token, image_url, caption)

    print(f"Waiting for container {container_id} to finish processing...")
    wait_until_container_ready(container_id, access_token)

    print("Publishing...")
    media_id = publish_container(ig_user_id, access_token, container_id)
    print(f"Published. Media ID: {media_id}")
    return media_id


def build_caption(reference: str, verse_text: str) -> str:
    return (
        f"{verse_text}\n\n"
        f"— {reference} (KJV)\n\n"
        f"#dailyverse #bible #scripture #{reference.split()[0].lower()}"
    )


if __name__ == "__main__":
    import json

    if len(sys.argv) != 3:
        print("Usage: python post_to_instagram.py <meta_json_path> <public_image_url>")
        sys.exit(1)

    meta_path, image_url = sys.argv[1], sys.argv[2]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    caption = build_caption(meta["reference"], meta["text"])
    post_image(image_url, caption)

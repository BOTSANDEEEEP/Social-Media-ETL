import json
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT = Path.home() / "social-media-etl"
JSON_FILE = PROJECT / "data/incoming/social_media_posts.json"
MEDIA_DIR = PROJECT / "data/media"
DB_FILE = PROJECT / "database/social_media.db"

REQUIRED_FIELDS = {
    "post_id", "user_id", "username", "post_type", "caption",
    "hashtags", "likes", "comments", "shares", "media_file", "created_at"
}

def main():
    with JSON_FILE.open("r", encoding="utf-8") as f:
        posts = json.load(f)

    if not isinstance(posts, list):
        raise ValueError("JSON root must be a list of posts")

    validated = []
    seen_ids = set()

    for post in posts:
        if not isinstance(post, dict):
            raise ValueError("Each post must be a JSON object")

        missing = REQUIRED_FIELDS - post.keys()
        if missing:
            raise ValueError(f"Missing fields: {sorted(missing)}")

        post_id = post["post_id"]
        if not isinstance(post_id, str) or not post_id.strip():
            raise ValueError("post_id must be a non-empty string")
        if post_id in seen_ids:
            raise ValueError(f"Duplicate post_id: {post_id}")
        seen_ids.add(post_id)

        for field in ("likes", "comments", "shares"):
            if not isinstance(post[field], int) or isinstance(post[field], bool) or post[field] < 0:
                raise ValueError(f"{field} must be a non-negative integer for {post_id}")

        if not isinstance(post["hashtags"], list):
            raise ValueError(f"hashtags must be a list for {post_id}")

        datetime.strptime(post["created_at"], "%Y-%m-%d %H:%M:%S")

        media_name = post["media_file"]
        if not isinstance(media_name, str) or Path(media_name).name != media_name:
            raise ValueError(f"Invalid media filename for {post_id}")

        media_path = MEDIA_DIR / media_name
        if not media_path.is_file():
            raise FileNotFoundError(f"Media file not found: {media_path}")

        with media_path.open("rb") as image:
            if image.read(3) != b"\xff\xd8\xff":
                raise ValueError(f"Media is not a valid JPEG: {media_name}")

        engagement = post["likes"] + post["comments"] + post["shares"]
        validated.append((
            post["post_id"], post["user_id"], post["username"],
            post["post_type"], post["caption"],
            json.dumps(post["hashtags"]), post["likes"],
            post["comments"], post["shares"], engagement,
            post["media_file"], post["created_at"]
        ))

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS social_media_posts (
                post_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                post_type TEXT NOT NULL,
                caption TEXT,
                hashtags TEXT,
                likes INTEGER NOT NULL,
                comments INTEGER NOT NULL,
                shares INTEGER NOT NULL,
                engagement INTEGER NOT NULL,
                media_file TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.executemany("""
            INSERT OR REPLACE INTO social_media_posts
            (post_id, user_id, username, post_type, caption, hashtags,
             likes, comments, shares, engagement, media_file, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, validated)

    print(f"Validated and loaded {len(validated)} posts into {DB_FILE}")
    for row in validated:
        print(f"{row[0]}: engagement={row[9]}")

if __name__ == "__main__":
    main()

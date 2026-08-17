"""
cleanup_expired.py — deletes expired notices (and their S3 images, if any).

Not part of the FastAPI app process — this is invoked periodically by cron on
the EC2 instance (installed by terraform/user_data.sh.tpl):

    */15 * * * * /opt/app/.../backend/venv/bin/python \
        /opt/app/.../backend/cleanup_expired.py >> /var/log/noticeboard-cleanup.log 2>&1

Safe to run by hand at any time, e.g. to test without waiting on the cron
interval: `python cleanup_expired.py` (from backend/, with the venv active).
"""
import os

from app.db import get_connection

S3_BUCKET = os.environ.get("S3_UPLOADS_BUCKET")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def main():
    conn = get_connection()
    try:
        expired = conn.run(
            "SELECT id, image_key FROM notices WHERE expires_at IS NOT NULL AND expires_at <= now()"
        )
        if not expired:
            print("No expired notices.")
            return

        image_keys = [row[1] for row in expired if row[1]]

        conn.run("DELETE FROM notices WHERE expires_at IS NOT NULL AND expires_at <= now()")
        print(f"Deleted {len(expired)} expired notice(s).")

        if image_keys and S3_BUCKET:
            import boto3

            s3 = boto3.client("s3", region_name=AWS_REGION)
            s3.delete_objects(
                Bucket=S3_BUCKET,
                Delete={"Objects": [{"Key": k} for k in image_keys]},
            )
            print(f"Deleted {len(image_keys)} S3 object(s).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

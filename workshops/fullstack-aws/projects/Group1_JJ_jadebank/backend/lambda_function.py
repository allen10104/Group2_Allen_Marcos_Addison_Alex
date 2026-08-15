import json
import os

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", "5432"),
        database=os.environ["PG_DATABASE"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath", "")

    if method == "OPTIONS":
        return response(200, {"message": "CORS preflight successful"})

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # GET /notices
        if method == "GET" and path == "/notices":
            cursor.execute(
                """
                SELECT id, name, message
                FROM notices
                ORDER BY id DESC
                """
            )

            rows = cursor.fetchall()

            notices = [
                {
                    "id": row[0],
                    "name": row[1],
                    "message": row[2],
                }
                for row in rows
            ]

            cursor.close()
            connection.close()

            return response(200, notices)

        # POST /notices
        if method == "POST" and path == "/notices":
            body = json.loads(event.get("body") or "{}")

            name = body.get("name")
            message = body.get("message")

            if not name or not message:
                cursor.close()
                connection.close()

                return response(
                    400,
                    {
                        "error": "name and message are required"
                    },
                )

            cursor.execute(
                """
                INSERT INTO notices (name, message)
                VALUES (%s, %s)
                RETURNING id, name, message
                """,
                (name, message),
            )

            row = cursor.fetchone()

            connection.commit()

            cursor.close()
            connection.close()

            notice = {
                "id": row[0],
                "name": row[1],
                "message": row[2],
            }

            return response(201, notice)

        # DELETE /notices/{id}
        if method == "DELETE" and path.startswith("/notices/"):
            notice_id = path.split("/")[-1]

            try:
                notice_id = int(notice_id)
            except ValueError:
                cursor.close()
                connection.close()

                return response(
                    400,
                    {
                        "error": "Invalid notice ID"
                    },
                )

            cursor.execute(
                """
                DELETE FROM notices
                WHERE id = %s
                RETURNING id
                """,
                (notice_id,),
            )

            deleted = cursor.fetchone()

            if deleted is None:
                connection.rollback()

                cursor.close()
                connection.close()

                return response(
                    404,
                    {
                        "error": "Notice not found"
                    },
                )

            connection.commit()

            cursor.close()
            connection.close()

            return response(
                200,
                {
                    "message": "Notice deleted successfully"
                },
            )

        cursor.close()
        connection.close()

        return response(
            404,
            {
                "error": "Route not found"
            },
        )

    except Exception as error:
        print(f"Error: {error}")

        return response(
            500,
            {
                "error": "Internal server error"
            },
        )
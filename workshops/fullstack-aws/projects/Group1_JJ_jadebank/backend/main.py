import os

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Notice Board API")


def get_connection():
    return psycopg.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )


class NoticeCreate(BaseModel):
    name: str
    message: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Notice Board API is running"}


@app.get("/notices")
def get_notices():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, message
                FROM notices
                ORDER BY id DESC
                """
            )

            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "message": row[2],
        }
        for row in rows
    ]


@app.post("/notices")
def create_notice(notice: NoticeCreate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO notices (name, message)
                VALUES (%s, %s)
                RETURNING id, name, message
                """,
                (notice.name, notice.message),
            )

            row = cursor.fetchone()

        connection.commit()

    return {
        "id": row[0],
        "name": row[1],
        "message": row[2],
    }


@app.delete("/notices/{notice_id}")
def delete_notice(notice_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM notices
                WHERE id = %s
                RETURNING id
                """,
                (notice_id,),
            )

            deleted = cursor.fetchone()

        connection.commit()

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Notice not found",
        )

    return {"message": "Notice deleted successfully"}
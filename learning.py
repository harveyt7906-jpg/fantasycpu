import psycopg2, os, numpy as np
from dotenv import load_dotenv
from thanos_council import consult_council

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_conn():
    return psycopg2.connect(DATABASE_URL)


def review_past_runs(limit=20):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT kind,payload FROM runs ORDER BY ts DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"kind": r[0], "payload": r[1]} for r in rows]
    except:
        return []


def refine_strategy():
    past = review_past_runs(50)
    weights = {"weather": 1.0, "odds": 1.0}
    for r in past:
        if r["kind"] == "head_coach" and "win_prob" in r["payload"]:
            if r["payload"]["win_prob"] < 0.5:
                weights["weather"] *= 0.95
        if r["kind"] == "gm" and "recommendations" in r["payload"]:
            if len(r["payload"]["recommendations"].get("waivers", [])) > 2:
                weights["odds"] *= 1.05
    council = consult_council("learning", weights)
    return {"role": "learning", "logic": weights, "council": council}

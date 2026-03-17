"""
Flask + py-fsrs Spaced Repetition API
Endpoints:
  GET  /get_questions  - Returns cards due for review today
  POST /review         - Submits a review result and reschedules the card
"""

from flask import Flask, jsonify, request
from fsrs import Scheduler, Card, Rating
from datetime import datetime, timezone, timedelta
import json
import os

app = Flask(__name__)

QUESTIONS_FILE = "questions.json"   
STATE_FILE      = "card_states.json"

scheduler = Scheduler()


def load_questions() -> list[dict]:
    """Load the static question bank."""
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)


def load_states() -> dict:
    """Load persisted card states from disk. Keys are stored as ints."""
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        raw = json.load(f)
    # JSON keys are always strings; convert back to int
    return {int(k): v for k, v in raw.items()}


def save_states(states: dict) -> None:
    """Persist card states to disk."""
    with open(STATE_FILE, "w") as f:
        json.dump(states, f, indent=2, default=str)


def card_from_state(state: dict | None) -> Card:
    """Reconstruct a py-fsrs Card from a saved state dict, or return a new one."""
    if state is None:
        return Card()

    card = Card()
    card.due           = datetime.fromisoformat(state["due"])
    card.stability     = state["stability"]
    card.difficulty    = state["difficulty"]
    card.elapsed_days  = state["elapsed_days"]
    card.scheduled_days= state["scheduled_days"]
    card.state         = state["state"]          # int (0-3)
    card.last_review   = (
        datetime.fromisoformat(state["last_review"])
        if state.get("last_review") else None
    )
    return card


def card_to_state(card: Card) -> dict:
    """Serialize a py-fsrs Card to a JSON-safe dict."""
    return {
        "due":            card.due.isoformat(),
        "stability":      card.stability,
        "difficulty":     card.difficulty,
        "elapsed_days":   card.elapsed_days,
        "scheduled_days": card.scheduled_days,
        "state":          card.state,
        "last_review":    card.last_review.isoformat() if card.last_review else None,
    }


def is_due(card: Card, now: datetime) -> bool:
    """Return True if the card is due at or before `now`."""
    print(card.due, now)
    return card.due <= now + timedelta(days=1)



@app.route("/get_questions", methods=["GET"])
def get_questions():
    """
    Returns all cards that are due for review right now.

    Response JSON:
    {
      "due_count": <int>,
      "questions": [
        {
          "id": "q1",
          "front": "What is 2+2?",
          "back": "4",
          "state": 0,
          "due": "2025-01-01T00:00:00+00:00"
        },
        ...
      ]
    }
    """
    now       = datetime.now(timezone.utc)
    questions = load_questions()
    states    = load_states()

    due_questions = []
    for q in questions:
        qid   = q["id"]
        card  = card_from_state(states.get(qid))
        print(qid)
        if is_due(card, now):
            print(qid)
            due_questions.append({
                "id":     qid,
                "front":  q["front"],
                "back":   q["back"],
                "state":  card.state,   # 0=New,1=Learning,2=Review,3=Relearning
                "due":    card.due.isoformat(),
            })

    return jsonify({"due_count": len(due_questions), "questions": due_questions})


@app.route("/review", methods=["POST"])
def review():
    """
    Record a review result and reschedule the card.

    Request JSON:
    {
      "id": "q1",
      "rating": 3          // 1=Again, 2=Hard, 3=Good, 4=Easy
    }

    Response JSON:
    {
      "id": "q1",
      "rating": 3,
      "next_due": "2025-01-04T00:00:00+00:00",
      "scheduled_days": 3,
      "stability": 4.07,
      "difficulty": 5.0,
      "state": 2,
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    raw_id     = data.get("id")
    rating_val = data.get("rating")

    if raw_id is None:
        return jsonify({"error": "Missing field: id"}), 400
    if not isinstance(raw_id, int):
        return jsonify({"error": "id must be an integer"}), 400
    qid = raw_id

    rating_map = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}
    if rating_val not in rating_map:
        return jsonify({"error": "rating must be 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy)"}), 400

    questions = load_questions()
    if not any(q["id"] == qid for q in questions):
        return jsonify({"error": f"Question id '{qid}' not found"}), 404

    states = load_states()
    card   = card_from_state(states.get(qid))
    rating = rating_map[rating_val]

    now          = datetime.now(timezone.utc)
    card, review_log = scheduler.review_card(card, rating, now)

    states[qid] = card_to_state(card)
    save_states(states)

    return jsonify({
        "id":             qid,
        "rating":         rating_val,
        "next_due":       card.due.isoformat(),
        "scheduled_days": card.scheduled_days,
        "stability":      round(card.stability, 4),
        "difficulty":     round(card.difficulty, 4),
        "state":          card.state,
    })



if __name__ == "__main__":
    app.run(debug=True, port=5000)


#TODO: add all parameters of card (step, last_review)

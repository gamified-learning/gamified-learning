from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
from scheduler import load_questions, get_due_cards, review_card, RATING_MAP, save_question

app = Flask(__name__)
CORS(app)


@app.route("/get_questions", methods=["GET"])
def get_questions():
    """
    GET /get_questions

    Response:
    {
        "due_count": 2,
        "questions": [
            {
                "id": 1,
                "front": "What is 2+2?",
                "back": "4",
                "state": 0,
                "due": "2025-01-01T00:00:00+00:00"
            }
        ]
    }

    state: 0=New, 1=Learning, 2=Review, 3=Relearning
    """
    now = datetime.now(timezone.utc) + timedelta(days=1)
    print(now)
    due = get_due_cards(now)
    return jsonify({"due_count": len(due), "questions": due})

@app.route("/all_questions", methods=["GET"])
def get_all_questions():
    questions = load_questions()
    return jsonify({"questions": questions})

@app.route("/save_question", methods=["POST"])
def api_save_question():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    
    qid = data.get("id")
    front = data.get("front")
    back = data.get("back")
    
    if not front or not back:
        return jsonify({"error": "Missing front or back"}), 400
        
    updated = save_question(qid, front, back)
    if not updated:
        return jsonify({"error": f"Question id '{qid}' not found"}), 404
        
    return jsonify(updated)

@app.route("/review", methods=["POST"])
def review():
    """
    POST /review

    Request:
    {
        "id": 1,
        "rating": 3
    }

    rating: 1=Again, 2=Hard, 3=Good, 4=Easy

    Response:
    {
        "id": 1,
        "rating": 3,
        "next_due": "2025-01-04T00:00:00+00:00",
        "scheduled_days": 3,
        "stability": 4.0729,
        "difficulty": 5.0,
        "state": 2,
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    qid        = data.get("id")
    rating_val = data.get("rating")

    if qid is None:
        return jsonify({"error": "Missing field: id"}), 400
    if not isinstance(qid, int):
        return jsonify({"error": "id must be an integer"}), 400
    if rating_val not in RATING_MAP:
        return jsonify({"error": "rating must be 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy)"}), 400

    questions = load_questions()
    if not any(q["id"] == qid for q in questions):
        return jsonify({"error": f"Question id '{qid}' not found"}), 404

    now    = datetime.now(timezone.utc)
    result = review_card(qid, rating_val, now)

    return jsonify({"id": qid, "rating": rating_val, **result})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

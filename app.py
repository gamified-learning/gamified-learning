from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
from backend.scheduler import *
import backend.generate as generate
import requests
import backend.stats as stats

app = Flask(__name__, template_folder="frontend", static_folder="frontend", static_url_path="")
CORS(app)


@app.route("/")
def index():
   return render_template("index.html")

@app.route("/api/get_questions", methods=["GET"])
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

@app.route("/api/all_questions", methods=["GET"])
def get_all_questions():
    questions = load_questions()
    return jsonify({"questions": questions})

@app.route("/api/save_question", methods=["POST"])
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

@app.route("/api/review", methods=["POST"])
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


@app.route("/api/get_review_log", methods = ["GET"])
def get_review_log():
    return load_review_log()


@app.route("/api/stats", methods = ["GET"])
def get_stats():
    questions = load_questions()
    now = datetime.now(timezone.utc) + timedelta(days=1)

    due_count = len(get_due_cards(now))
    learning_count = sum(1 for q in questions if q.get("state") in [0, 1, 3])
    total_count = len(questions)

    return jsonify({
        "due_count": due_count,
        "learning_count": learning_count,
        "total_count": total_count,
        "heatmap": stats.heatmap(),
        "streak": stats.streak()
    })


@app.route("/api/upload_content", methods=["POST"])
def upload_content():
    text      = request.form.get("text", "")
    file      = request.files.get("file")
    provider  = "openrouter"
    with open("api-key") as f:
        api_key   = f.read().strip()

    if not api_key:
        return jsonify({"success": False, "error": "api_key is required"}), 400

    file_text = generate.extract_file_text(file)
    prompt    = generate.build_prompt(text, file_text)

    try:
        if provider == "openrouter":
            questions = generate.generate_questions_openrouter(
                prompt=prompt,
                api_key=api_key,
                model=request.form.get("model", "openrouter/free"),
            )
        elif provider == "openai":
            questions = generate.generate_questions_openai(
                prompt=prompt,
                api_key=api_key,
                model=request.form.get("model", "gpt-4o-mini"),
            )
        else:
            return jsonify({"success": False, "error": "Invalid provider"})
    except requests.HTTPError as e:
        print(f"OpenRouter error body: {e.response.text}")  
        return jsonify({"success": False, "error": str(e)}), 502
    except (json.JSONDecodeError, KeyError) as e:
        return jsonify({"success": False, "error": f"Failed to parse model response: {e}"}), 500

    saved = []
    for q in questions:
        front = q.get("question", "")
        back  = q.get("answer", "")
        if front and back:
            saved_q = save_question(None, front, back)
            if saved_q:
                saved.append(saved_q)

    return jsonify({"success": True, "generated": len(saved), "questions": saved}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

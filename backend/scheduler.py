from fsrs import Scheduler, Card, Rating, ReviewLog
from datetime import datetime
import json
import os

DATA_DIR = "data"
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
CARDS_FILE     = os.path.join(DATA_DIR, "cards.json")
REVIEW_LOG_FILE = os.path.join(DATA_DIR, "review_log.json")

_scheduler = Scheduler()

RATING_MAP = {
    1: Rating.Again,
    2: Rating.Hard,
    3: Rating.Good,
    4: Rating.Easy,
}


def load_questions() -> list[dict]:
    if not os.path.exists(QUESTIONS_FILE):
        print("File not found")
        return []
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)

def save_questions(questions: list[dict]) -> None:
    with open(QUESTIONS_FILE, "w") as f:
        json.dump(questions, f, indent=2)

def save_question(qid: int | None, front: str, back: str) -> dict | None:
    questions = load_questions()
    if qid is None:
        new_id = max((q["id"] for q in questions), default=0) + 1
        new_q = {"id": new_id, "front": front, "back": back}
        questions.append(new_q)
        save_questions(questions)
        return new_q
    else:
        for q in questions:
            if q["id"] == qid:
                q["front"] = front
                q["back"] = back
                save_questions(questions)
                return q
        return None


def load_cards() -> dict[int, dict]:
    if not os.path.exists(CARDS_FILE):
        return {}
    with open(CARDS_FILE, "r") as f:
        raw = json.load(f)
    # JSON object keys are always strings; convert back to int to match question ids
    return {int(k): v for k, v in raw.items()}


def save_cards(cards: dict[int, dict]) -> None:
    with open(CARDS_FILE, "w") as f:
        json.dump(cards, f, indent=2, default=str)


def deserialize_card(data: dict | None) -> Card:
    """Return a new Card for unseen questions, or restore a previously saved one."""
    if data is None:
        return Card()

    return Card.from_dict(data)


def serialize_card(card: Card) -> dict:
    return card.to_dict()

def get_due_cards(now: datetime) -> list[dict]:
    """Merge question content with card metadata for every question that is due."""
    questions = load_questions()
    cards     = load_cards()
    print(questions)
    due = []
    for q in questions:
        qid  = q["id"]
        card = deserialize_card(cards.get(qid))
        if card.due <= now:
            due.append({
                "id":     qid,
                "front":  q["front"],
                "back":   q["back"],
                "state":  card.state,
                "due":    card.due.isoformat(),
            })


    return due


def review_card(qid: int, rating_val: int, now: datetime) -> dict:
    """Apply a rating to a card and persist the updated schedule. Returns the updated card data."""
    cards  = load_cards()
    card   = deserialize_card(cards.get(qid))
    rating = RATING_MAP[rating_val]

    card, review_log = _scheduler.review_card(card, rating, now)

    cards[qid] = serialize_card(card)
    save_cards(cards)
    
    save_review_log(review_log)

    return {
        "next_due":       card.due.isoformat(),
        "stability":      round(card.stability, 4),
        "difficulty":     round(card.difficulty, 4),
        "state":          card.state,
    }


def load_review_log():
    if not os.path.exists(REVIEW_LOG_FILE):
        return []

    with open(REVIEW_LOG_FILE, "r") as f:
        return json.load(f)


def save_review_log(review_log: ReviewLog):
    print("saved log")

    review_logs = load_review_log()
    review_logs.append(review_log.to_dict())
    with open(REVIEW_LOG_FILE, "w") as f:
        json.dump(review_logs, f, indent=2, default=str)


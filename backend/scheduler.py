from fsrs import Scheduler, Card, Rating
from datetime import datetime
import json
import os

DATA_DIR = "data"
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
CARDS_FILE     = os.path.join(DATA_DIR, "cards.json")

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

    card = Card()
    card.due            = datetime.fromisoformat(data["due"])
    card.stability      = data["stability"]
    card.difficulty     = data["difficulty"]
    card.elapsed_days   = data["elapsed_days"]
    card.scheduled_days = data["scheduled_days"]
    card.state          = data["state"]
    card.last_review    = (
        datetime.fromisoformat(data["last_review"])
        if data.get("last_review") else None
    )
    return card


def serialize_card(card: Card) -> dict:
    return {
        "due":            card.due.isoformat(),
        "stability":      card.stability,
        "difficulty":     card.difficulty,
        "elapsed_days":   card.elapsed_days,
        "scheduled_days": card.scheduled_days,
        "state":          card.state,
        "last_review":    card.last_review.isoformat() if card.last_review else None,
    }


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

    card, _ = _scheduler.review_card(card, rating, now)

    cards[qid] = serialize_card(card)
    save_cards(cards)

    return {
        "next_due":       card.due.isoformat(),
        "scheduled_days": card.scheduled_days,
        "stability":      round(card.stability, 4),
        "difficulty":     round(card.difficulty, 4),
        "state":          card.state,
    }

from backend.scheduler import load_review_log, load_questions, load_cards
import datetime
from collections import defaultdict


def _question_lookup() -> dict[int, dict]:
    return {question["id"]: question for question in load_questions()}


def _question_id_from_card_id(card_id: int) -> int | None:
    cards = load_cards()
    for question_id, card in cards.items():
        if card.get("card_id") == card_id:
            return question_id
    return None

def heatmap():
    review_log = load_review_log()
    
    days = defaultdict(int)
    for r in review_log:
       date = datetime.datetime.fromisoformat(r["review_datetime"]).date()
       days[str(date)] += 1

    return dict(days)

def streak():
    freq = heatmap()
    date = datetime.datetime.now().date()
    while freq.get(str(date), 0) > 0:
        date -= datetime.timedelta(days=1).date()

    return (datetime.datetime.now().date() - date).days


def hard_questions(limit: int = 5) -> list[dict]:
    review_log = load_review_log()
    questions = _question_lookup()
    buckets: dict[int, dict] = defaultdict(lambda: {
        "again_count": 0,
        "hard_count": 0,
        "total_reviews": 0,
        "last_review": None,
    })

    for entry in review_log:
        question_id = entry.get("question_id")
        if question_id is None and entry.get("card_id") is not None:
            question_id = _question_id_from_card_id(entry["card_id"])

        if question_id is None or question_id not in questions:
            continue

        bucket = buckets[question_id]
        bucket["total_reviews"] += 1
        rating = entry.get("rating")
        if rating == 1:
            bucket["again_count"] += 1
        elif rating == 2:
            bucket["hard_count"] += 1

        reviewed_at = entry.get("review_datetime")
        if reviewed_at and (bucket["last_review"] is None or reviewed_at > bucket["last_review"]):
            bucket["last_review"] = reviewed_at

    hard_questions = []
    for question_id, bucket in buckets.items():
        hard_reviews = bucket["again_count"] + bucket["hard_count"]
        if hard_reviews == 0:
            continue

        question = questions[question_id]
        hard_questions.append({
            "id": question_id,
            "front": question.get("front", ""),
            "back": question.get("back", ""),
            "subject": question.get("subject", "General"),
            "chapter": question.get("chapter", "General"),
            "again_count": bucket["again_count"],
            "hard_count": bucket["hard_count"],
            "hard_reviews": hard_reviews,
            "total_reviews": bucket["total_reviews"],
            "hard_ratio": round(hard_reviews / bucket["total_reviews"], 3),
            "last_review": bucket["last_review"],
        })

    hard_questions.sort(
        key=lambda item: (
            item["hard_reviews"],
            item["hard_ratio"],
            item["total_reviews"],
        ),
        reverse=True,
    )

    return hard_questions[:limit]


def hard_chapters_by_subject(limit_per_subject: int = 5) -> list[dict]:
    review_log = load_review_log()
    questions = _question_lookup()
    chapter_buckets: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "again_count": 0,
        "hard_count": 0,
        "total_reviews": 0,
        "question_ids": set(),
        "last_review": None,
    })

    for entry in review_log:
        question_id = entry.get("question_id")
        if question_id is None and entry.get("card_id") is not None:
            question_id = _question_id_from_card_id(entry["card_id"])

        if question_id is None or question_id not in questions:
            continue

        question = questions[question_id]
        subject = question.get("subject", "General")
        chapter = question.get("chapter", "General")
        bucket = chapter_buckets[(subject, chapter)]

        bucket["question_ids"].add(question_id)
        bucket["total_reviews"] += 1

        rating = entry.get("rating")
        if rating == 1:
            bucket["again_count"] += 1
        elif rating == 2:
            bucket["hard_count"] += 1

        reviewed_at = entry.get("review_datetime")
        if reviewed_at and (bucket["last_review"] is None or reviewed_at > bucket["last_review"]):
            bucket["last_review"] = reviewed_at

    grouped: dict[str, list[dict]] = defaultdict(list)
    for (subject, chapter), bucket in chapter_buckets.items():
        hard_reviews = bucket["again_count"] + bucket["hard_count"]
        if hard_reviews == 0:
            continue

        grouped[subject].append({
            "subject": subject,
            "chapter": chapter,
            "question_count": len(bucket["question_ids"]),
            "again_count": bucket["again_count"],
            "hard_count": bucket["hard_count"],
            "hard_reviews": hard_reviews,
            "total_reviews": bucket["total_reviews"],
            "hard_ratio": round(hard_reviews / bucket["total_reviews"], 3),
            "last_review": bucket["last_review"],
        })

    result = []
    for subject, chapters in grouped.items():
        chapters.sort(
            key=lambda item: (
                item["hard_reviews"],
                item["hard_ratio"],
                item["total_reviews"],
            ),
            reverse=True,
        )
        result.append({
            "subject": subject,
            "chapters": chapters[:limit_per_subject],
        })

    result.sort(
        key=lambda item: sum(chapter["hard_reviews"] for chapter in item["chapters"]),
        reverse=True,
    )

    return result
    


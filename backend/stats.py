from backend.scheduler import load_review_log
import datetime
from collections import defaultdict

def heatmap():
    review_log = load_review_log()
    
    days = defaultdict(int)
    for r in review_log:
        date = datetime.datetime.fromisoformat(r["review_datetime"]).date()
        days[str(date)] += 1

    return dict(days)

def streak():
    freq = heatmap()
    today = datetime.date.today()
    date = today
    while freq.get(str(date), 0) > 0:
        date -= datetime.timedelta(days=1)

    current_streak = (today - date).days
    return {"streak": current_streak}


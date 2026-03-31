from backend.scheduler import load_review_log
import datetime
from collections import defaultdict

def heatmap():
    review_log = load_review_log()
    
    days = defaultdict(int)
    for r in review_log:
       date = datetime.datetime.fromisoformat(r["review_datetime"]).date()
       days[str(date)] += 1

    return days

def streak():
    freq = heatmap()
    date = datetime.datetime.now().date()
    while (freq[date] > 0):
        date -= datetime.timedelta(days=1).date()

    return (datetime.datetime.now().date() - date).days
    


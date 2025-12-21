from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from api.deps import get_db, get_current_user
from api.models import QuizScore

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.get("/retention")
async def get_retention_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns quiz average scores grouped by topic and ordered by creation date.
    Used for plotting the 'Forgetting Curve' or progress over time.
    """
    user_id = current_user['user_id']
    
    # Query: Select Created Date (Day), Topic, and Avg Score
    # We aggregate by Day to keep the chart clean
    results = db.query(
        func.date(QuizScore.created_at).label('date'),
        QuizScore.topic_tag,
        func.avg(QuizScore.score / QuizScore.total_questions * 100).label('avg_score')
    ).filter(
        QuizScore.user_id == user_id
    ).group_by(
        func.date(QuizScore.created_at),
        QuizScore.topic_tag
    ).order_by(
        func.date(QuizScore.created_at)
    ).all()

    # Transform into JSON for Recharts
    # Format: [{ date: '2023-10-01', 'Python': 80, 'SQL': 60 }]
    chart_data = []
    
    # Simple grouping in Python (since SQL result is flat)
    from collections import defaultdict
    date_map = defaultdict(dict)

    for r in results:
        date_str = str(r.date)
        date_map[date_str]["date"] = date_str
        date_map[date_str][r.topic_tag] = round(r.avg_score, 1)

    chart_data = list(date_map.values())
    return chart_data

@router.get("/weaknesses")
async def get_weakness_heatmap(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns topics ordered by lowest average score.
    """
    user_id = current_user['user_id']
    
    results = db.query(
        QuizScore.topic_tag,
        func.avg(QuizScore.score / QuizScore.total_questions * 100).label('avg_score'),
        func.count(QuizScore.id).label('attempts')
    ).filter(
        QuizScore.user_id == user_id
    ).group_by(
        QuizScore.topic_tag
    ).order_by(
        'avg_score' # Ascending (Lowest first)
    ).all()

    data = []
    for r in results:
        score = round(r.avg_score, 1)
        bucket = "Critical" if score < 40 else ("Weak" if score < 70 else "Strong")
        data.append({
            "topic": r.topic_tag,
            "score": score,
            "attempts": r.attempts,
            "bucket": bucket
        })
        
    return data

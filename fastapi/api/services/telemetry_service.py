
from sqlalchemy.orm import Session
from api.models import TelemetryLog, UserHistory
from datetime import datetime

def aggregate_session_features(user_id: int, session_id: str, db: Session):

    logs = db.query(TelemetryLog).filter(
        TelemetryLog.user_id == user_id,
        TelemetryLog.session_id == session_id
    ).all()
    
    if not logs:
        return [0, 0.7, 0, 0]

    tab_switches = sum(1 for log in logs if log.event_type == "TabSwitch")


    copy_paste_count = sum(1 for log in logs if log.event_type in ["Copy", "Paste"])
    

    total_events = len(logs)
    code_reliance = copy_paste_count / total_events if total_events > 0 else 0

    latencies = [log.latency_ms for log in logs if log.latency_ms is not None]
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
 
        time_ratio = min(1.0, avg_latency / 5000)
    else:
        time_ratio = 0.5

    return [copy_paste_count, time_ratio, code_reliance, tab_switches]
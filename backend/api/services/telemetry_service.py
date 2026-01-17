
from sqlalchemy.orm import Session
from backend.api.models import TelemetryLog, UserHistory
from datetime import datetime

def aggregate_session_features(user_id: int, session_id: str, db: Session):

    # Get recent history for this session to aggregate metrics
    history_items = db.query(UserHistory).filter(
        UserHistory.user_id == user_id,
        UserHistory.session_id == session_id
    ).order_by(UserHistory.created_at.desc()).limit(10).all()
    
    if not history_items:
         return [0, 0.5, 0, 0] # Default Safe Vector

    total_copy = 0
    total_paste = 0
    total_switches = 0
    total_time_ms = 0
    count = 0

    for item in history_items:
        if item.telemetry_data:
            data = item.telemetry_data
            total_copy += data.get('copy_count', 0)
            total_paste += data.get('paste_count', 0)
            total_switches += data.get('tab_switch_count', 0)
            total_time_ms += data.get('time_to_query_ms', 0)
            count += 1
    
    if count == 0:
        return [0, 0.5, 0, 0]

    # Feature Engineering matches XGBoost Training Expected Input
    # 1. Copy Paste Rate (Normalized)
    activity_count = total_copy + total_paste + total_switches
    copy_paste_rate = (total_copy + total_paste) / activity_count if activity_count > 0 else 0

    # 2. Time Ratio (Normalized against 5 sec baseline)
    avg_time = total_time_ms / count
    time_ratio = min(1.0, avg_time / 5000)

    # 3. Code Reliance (Simplified Proxy: High paste count)
    code_reliance = 1.0 if total_paste > 2 else 0.0

    # 4. Tab Switches (Raw Count)
    tab_switch_count = total_switches

    return [copy_paste_rate, time_ratio, code_reliance, tab_switch_count]
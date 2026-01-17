# api/ml/engine.py
import xgboost as xgb
import numpy as np
import os

# Global variable to hold the model in memory
_booster = None

def get_model():
    """Singleton pattern to load model only once."""
    global _booster
    if _booster is None:
        model_path = os.path.join(os.path.dirname(__file__), "dependency_detection_model.json")
        _booster = xgb.Booster()
        _booster.load_model(model_path)
    return _booster

def predict_dependency_probability(features: list) -> float:

    bst = get_model()
    
    input_data = np.array([features])
    dmatrix = xgb.DMatrix(input_data, feature_names=['copy_paste_rate', 'time_to_query_ratio', 'code_gen_reliance', 'tab_switch_count'])
    
    dependency_prob = bst.predict(dmatrix)[0]
    return float(dependency_prob)

    
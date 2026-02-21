"""
Decision model for truck routing: rule-based routing + optional ML predictor.
- Routing: shortest path on synthetic grid (see synthetic_network).
- Decision: which hub/slot to assign; either use optimizer or a small ML model
  trained on optimizer results for fast "mock" decisions.
"""

import numpy as np
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Optional sklearn for ML decision model
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def build_decision_features(
    data: Dict[str, Any],
    truck_id: int,
    slot_id: int,
) -> np.ndarray:
    """Feature vector for one truck: [origin_zone, slot_id, congestion_at_slot, ...]."""
    trucks_df = data["trucks"]
    time_slots_df = data["time_slots"]
    origin_zone = int(trucks_df.iloc[truck_id]["origin_zone"])
    congestion = float(time_slots_df.iloc[slot_id]["congestion_multiplier"])
    n_zones = data["n_zones"]
    n_slots = data["n_slots"]
    # One-hot-ish: zone index (normalized), slot (normalized), congestion
    features = [
        origin_zone / max(n_zones, 1),
        slot_id / max(n_slots - 1, 1),
        congestion,
    ]
    return np.array(features, dtype=np.float32)


def train_decision_model(
    data: Dict[str, Any],
    assignments: List[Tuple[int, int, int]],
    save_path: Optional[str] = None,
) -> Optional[Any]:
    """
    Train a small classifier to predict (hub_id, slot_id) from truck features.
    assignments: list of (truck_id, hub_id, slot_id) from optimizer.
    Returns the trained model and encoders, or None if sklearn not available.
    """
    if not SKLEARN_AVAILABLE:
        return None
    n_trucks = data["n_trucks"]
    X_list = []
    hub_list = []
    slot_list = []
    for (t, h, s) in assignments:
        # Use slot_id as part of context (we predict hub; slot can be derived or predicted separately)
        feat = build_decision_features(data, t, s)
        X_list.append(feat)
        hub_list.append(h)
        slot_list.append(s)
    X = np.stack(X_list)
    hub_enc = LabelEncoder()
    slot_enc = LabelEncoder()
    y_hub = hub_enc.fit_transform(hub_list)
    y_slot = slot_enc.fit_transform(slot_list)
    # Predict hub (main decision)
    clf = RandomForestClassifier(n_estimators=20, max_depth=6, random_state=42)
    clf.fit(X, y_hub)
    model_bundle = {
        "clf_hub": clf,
        "hub_enc": hub_enc,
        "slot_enc": slot_enc,
        "clf_slot": None,
    }
    # Optional: also predict slot (simplified: use same features)
    clf_slot = RandomForestClassifier(n_estimators=20, max_depth=6, random_state=43)
    clf_slot.fit(X, y_slot)
    model_bundle["clf_slot"] = clf_slot
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump(model_bundle, f)
    return model_bundle


def predict_assignment(
    model_bundle: Any,
    data: Dict[str, Any],
    truck_id: int,
    slot_id: int,
) -> Tuple[int, int]:
    """Predict (hub_id, slot_id) for one truck using trained model."""
    feat = build_decision_features(data, truck_id, slot_id).reshape(1, -1)
    hub_enc = model_bundle["hub_enc"]
    slot_enc = model_bundle["slot_enc"]
    hub_pred = model_bundle["clf_hub"].predict(feat)[0]
    slot_pred = model_bundle["clf_slot"].predict(feat)[0]
    return (int(hub_enc.inverse_transform([hub_pred])[0]), int(slot_enc.inverse_transform([slot_pred])[0]))


def greedy_baseline_assignments(
    data: Dict[str, Any],
    budget: float = 500,
    hub_cost: float = 100,
    green_zone_cost: float = 50,
    seed: int = 0,
) -> List[Tuple[int, int, int]]:
    """
    Simple rule-based assignment without optimization: prefer nearest hub (by zone distance),
    spread over slots to reduce congestion. Returns list of (truck_id, hub_id, slot_id).
    """
    from solver import run_baseline
    res = run_baseline(data, budget, hub_cost, green_zone_cost, seed)
    return res["assignments"]

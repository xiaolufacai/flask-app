import time

from flask import Blueprint, request, jsonify
from app.services.snap_service import PlaywrightSnapService

snap_bp = Blueprint('snap', __name__)
snap_service = PlaywrightSnapService()

def snap():
    data = request.json or {}
    html_path = data.get("html_path")
    element_ids = data.get("element_ids", [])
    task_token = data.get("task_token", str(int(time.time())))

    if not html_path:
        return jsonify({"code": 1, "msg": "html_path required"})

    result = snap_service.capture_snap(
        html_path=html_path,
        task_token=task_token,
        element_ids=element_ids
    )

    return jsonify({"code": 0, "data": result})

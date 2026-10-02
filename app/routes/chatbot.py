"""HTTP endpoint for the cinema chatbot."""
from __future__ import annotations

from secrets import compare_digest

from flask import Blueprint, jsonify, request, session

from app.services.chatbot_service import process_chat


chatbot_bp = Blueprint("chatbot", __name__)
MAX_QUESTION_LENGTH = 300


@chatbot_bp.post("/api/chat")
def chat():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Vui lòng gửi dữ liệu JSON hợp lệ."}), 400

    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Câu hỏi không được để trống."}), 400
    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify({"error": "Câu hỏi không được vượt quá 300 ký tự."}), 400

    token = session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token", "")
    if not isinstance(token, str) or not token or not supplied.isascii() or not compare_digest(supplied, token):
        return jsonify({"error": "Mã xác nhận không hợp lệ; hãy tải lại trang."}), 403

    try:
        result = process_chat(question)
        return jsonify({"answer": result["answer"], "cards": result["cards"]}), 200
    except Exception:
        # Deliberately do not expose provider, database, prompt, or traceback details.
        return jsonify({"error": "Xin lỗi, hệ thống tư vấn hiện chưa thể xử lý yêu cầu. Vui lòng thử lại sau."}), 500
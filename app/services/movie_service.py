"""Movie management and Groq description orchestration."""
import json
from app.models.movie import MovieModel
from app.services.gemini_service import generate_response, API_ERROR_MESSAGE, CONFIG_ERROR_MESSAGE


class MovieService:
    AGE_RATINGS = ('P', 'K', 'T13', 'T16', 'T18', 'C')

    @staticmethod
    def validate_age_rating(value):
        if not isinstance(value, str) or value not in MovieService.AGE_RATINGS:
            raise ValueError('Giới hạn độ tuổi không hợp lệ.')
        return value

    @staticmethod
    def list_all():
        return MovieModel.list_all()

    @staticmethod
    def update(movie_id, data):
        data = MovieService.validate(data)
        if "status" not in data:
            raise ValueError("status is required for a full update")
        return MovieModel.update(movie_id, data)

    @staticmethod
    def delete(movie_id):
        return MovieModel.delete(movie_id)

    @staticmethod
    def validate(data):
        required = ("title", "duration_minutes")
        missing = [key for key in required if data.get(key) in (None, "")]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")
        if int(data["duration_minutes"]) <= 0:
            raise ValueError("duration_minutes must be positive")
        data["duration_minutes"] = int(data["duration_minutes"])
        if data.get("status", "COMING_SOON") not in {"SHOWING", "COMING_SOON", "ENDED"}:
            raise ValueError("Invalid movie status")
        if data.get("metadata_json") and isinstance(data["metadata_json"], (dict, list)):
            data["metadata_json"] = json.dumps(data["metadata_json"], ensure_ascii=False)
        return data

    @staticmethod
    def generate_description(title, keywords, age_rating='P'):
        if not isinstance(title, str) or not title.strip() or len(title) > 255:
            raise ValueError('Vui lòng nhập tên phim (tối đa 255 ký tự).')
        if not isinstance(keywords, str) or len(keywords) > 500:
            raise ValueError('Từ khóa phải là văn bản tối đa 500 ký tự.')
        age_rating = MovieService.validate_age_rating(age_rating)
        prompt = (f"Viết đoạn tóm tắt nội dung hấp dẫn cho bộ phim {title.strip()}, "
                  f"độ tuổi {age_rating}, dựa trên các từ khóa: {keywords.strip()}. "
                  "Độ dài ngắn gọn dưới 150 từ, bằng tiếng Việt. Chỉ dùng dữ liệu đã cung cấp. "
                  "Chỉ trả về đoạn mô tả, không thêm lời dẫn.")
        text = generate_response(prompt).strip()
        if text in {API_ERROR_MESSAGE, CONFIG_ERROR_MESSAGE}:
            raise RuntimeError(text)  # Do not persist a provider fallback as a draft.
        if not text or len(text.split()) >= 150:
            raise ValueError("AI description must contain fewer than 150 words")
        return text

    @staticmethod
    def create(data, generate_ai=False):
        data = MovieService.validate(data)
        if generate_ai:
            description = MovieService.generate_description(data["title"], data.get("keywords", ""))
            source = json.dumps({"title": data["title"], "keywords": data.get("keywords", "")}, ensure_ascii=False)
            return MovieModel.create_with_draft(data, source, description)
        return MovieModel.create(data)
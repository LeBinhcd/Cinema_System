from app.models.room import RoomModel


class RoomService:
    @staticmethod
    def list_all():
        return RoomModel.list_all()

    @staticmethod
    def create(data):
        if not data.get("name") or int(data.get("row_count", 0)) <= 0 or int(data.get("column_count", 0)) <= 0:
            raise ValueError("name, positive row_count and positive column_count are required")
        return RoomModel.create(data)
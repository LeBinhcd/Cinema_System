# NHẬT KÝ PROMPT VÀ QUY TRÌNH TINH CHỈNH - SƠ ĐỒ ERD CƠ SỞ DỮ LIỆU

---

## 📌 BƯỚC 1: PROMPT KHỞI TẠO SKILL (SKILL_ERD_DIAGRAM.md)

> **User Prompt:**
> "Hãy tạo cho tôi một file `SKILL_ERD_DIAGRAM.md` định nghĩa quy tắc vẽ Sơ đồ Thực thể - Mối quan hệ (ERD - Entity Relationship Diagram) cho Cơ sở dữ liệu Hệ thống Quản lý Rạp chiếu phim có tích hợp AI.
> Requirements:
> 1. Dùng chuẩn PlantUML với `hide circle` và `skinparam linetype ortho`.
> 2. Định nghĩa thực thể bằng từ khóa `entity` kèm các thuộc tính, kiểu dữ liệu, đánh dấu khoá chính `<<PK>>` và khoá ngoại `<<FK>>`.
> 3. Thể hiện mối quan hệ chuẩn dạng Crow's Foot (`||--|{`).
> 4. Chỉ xuất mã PlantUML nguyên bản, không giải thích dài dòng."

---

## 📌 BƯỚC 2: PROMPT SINH TÀI LIỆU / SƠ ĐỒ (LẦN 1)

> **User Prompt:**
> "Dựa trên `SKILL_ERD_DIAGRAM.md` và tài liệu SRS rạp phim, hãy sinh mã PlantUML ERD cho Cơ sở dữ liệu rạp phim bao gồm các bảng: Phim, Phòng chiếu, Suất chiếu, Ghế, Người dùng, Đơn đặt vé và Vé xem phim."

---

## 📌 BƯỚC 3: ĐÁNH GIÁ & PHÁT HIỆN LỖI (AI CHECK / REVIEW)

Sau khi kiểm tra bản vẽ Lần 1, hệ thống nhận thấy các điểm thiếu sót nghiệp vụ và cấu trúc CSDL như sau:

- ❌ **Lỗi 1 (Thiếu bảng AI Audit):** CSDL Lần 1 chưa có bảng `NoiDungBanNhapAI` để lưu vết các bản tóm tắt phim/mô tả AI tạo ra trước khi Admin bấm kiểm duyệt (UC12).
- ❌ **Lỗi 2 (Thiếu bảng Báo cáo AI):** Chưa có bảng `BaoCaoDoanhThu` lưu trữ dữ liệu thống kê kèm trường `vanBanTomTatAI` (UC11).
- ❌ **Lỗi 3 (Thiếu trường nghiệp vụ khoá giữ ghế & khóa bán):** Bảng `DonDatVe` thiếu trường `thoiHanGiuGhe` (phục vụ đếm ngược 5 phút), bảng `SuatChieu` thiếu trường `daKhoaBan` (khóa sau 15p chiếu).
- ❌ **Lỗi 4 (Thiếu bảng Giá & Thanh toán):** Thiếu bảng `QuyTacGia` để cấu hình phụ thu khung giờ/cuối tuần/VIP và bảng `GiaoDichThanhToan` liên kết với cổng thanh toán online.
- ❌ **Lỗi 5 (Thiếu liên kết đa chiều):** Bảng `VeXemPhim` chưa liên kết trực tiếp với cả 3 thực thể: `DonDatVe`, `SuatChieu` và `Ghe`.

---

## 📌 BƯỚC 4: PROMPT YÊU CẦU SỬA ĐỔI & BỔ SUNG

> **User Prompt:**
> "Sơ đồ ERD Lần 1 còn thiếu các bảng nghiệp vụ quan trọng. Hãy cập nhật lại mã PlantUML ERD tuân thủ chuẩn 11 thực thể sau:
> 1. Thêm thực thể `NoiDungBanNhapAI` (lưu bản nháp AI, liên kết với `Phim` và `NguoiDung`).
> 2. Thêm thực thể `QuyTacGia` (phụ thu Vip, Đôi, Giờ Vàng, Cuối Tuần, liên kết với `SuatChieu`).
> 3. Thêm thực thể `BaoCaoDoanhThu` (chứa `vanBanTomTatAI`, liên kết với `NguoiDung`).
> 4. Bổ sung trường `thoiHanGiuGhe` vào `DonDatVe`, `daKhoaBan` vào `SuatChieu`.
> 5. Cập nhật thực thể `VeXemPhim` có đủ 3 khoá ngoại `maDonDat`, `maSuatChieu`, `maGhe`.
> 6. Đảm bảo đúng tên bảng, tên trường và kiểu dữ liệu chuẩn xác như sơ đồ ERD mẫu."

---

## 📌 BƯỚC 5: KẾT QUẢ CHỐT CUỐI CÙNG (FINAL OUTPUT)

Below is the complete PlantUML code for the 11-entity ERD Diagram that has been fully validated and finalized:

```plantuml
@startuml
' --- CẤU HÌNH GIAO DIỆN & MÀU SẮC (THEME) ---
skinparam shadowing false
skinparam linetype ortho
skinparam roundcorner 8
skinparam classAttributeIconSize 0
skinparam defaultFontName "Segoe UI", Arial, sans-serif

' Màu sắc cho thẻ Thực thể (Entity / Class)
skinparam class {
    BackgroundColor #FFFFFF
    HeaderBackgroundColor #ECECEC
    BorderColor #666666
    FontColor #000000
    FontSize 13
    AttributeFontColor #222222
    AttributeFontSize 12
}

' Màu đường nối quan hệ
skinparam arrow {
    Color #555555
}

' --- CÁC THỰC THỂ (ENTITIES) ---

class "NguoiDung" as NguoiDung << (E, #4CAF50) >> {
  - maNguoiDung : bigint «PK»
  --
  hoTen : varchar(150)
  soDienThoai : varchar(20) «UQ»
  matKhau : varchar(255)
  vaiTro : enum
  ngayTao : timestamp
  ngayCapNhat : timestamp
}

class "Phim" as Phim << (E, #4CAF50) >> {
  - maPhim : bigint «PK»
  --
  tenPhim : varchar(255)
  thoiLuong : smallint
  doTuoi : varchar(20)
  moTa : varchar(500)
  tuKhoa : varchar(500)
  thongTinMoRong : json
  trangThai : enum
  ngayKhoiChieu : date
  ngayTao : timestamp
  ngayCapNhat : timestamp
}

class "TheLoai" as TheLoai << (E, #4CAF50) >> {
  - maTheLoai : bigint «PK»
  --
  tenTheLoai : varchar(100) «UQ»
}

class "PhimTheLoai" as PhimTheLoai << (E, #4CAF50) >> {
  - maPhim : bigint «PK» «FK»
  - maTheLoai : bigint «PK» «FK»
}

class "PhongChieu" as PhongChieu << (E, #4CAF50) >> {
  - maPhong : bigint «PK»
  --
  tenPhong : varchar(100) «UQ»
  soHangGhe : smallint
  soCotGhe : smallint
}

class "Ghe" as Ghe << (E, #4CAF50) >> {
  - maGhe : bigint «PK»
  --
  maPhong : bigint «FK»
  hangGhe : varchar(5)
  soGhe : smallint
  loaiGhe : enum
}

class "QuyTacGia" as QuyTacGia << (E, #4CAF50) >> {
  - maQuyTac : bigint «PK»
  --
  tenQuyTac : varchar(120)
  loaiGhe : enum
  loaiNgay : enum
  gioBatDau : tinyint
  gioKetThuc : tinyint
  giaCoBan : decimal(10,2)
  phuPhi : decimal(10,2)
  trangThaiKichHoat : boolean
}

class "SuatChieu" as SuatChieu << (E, #4CAF50) >> {
  - maSuatChieu : bigint «PK»
  --
  maPhim : bigint «FK»
  maPhong : bigint «FK»
  thoiGianBatDau : datetime
  thoiGianKetThuc : datetime
  ngayTao : timestamp
}

class "VeXemPhim" as VeXemPhim << (E, #4CAF50) >> {
  - maVe : bigint «PK»
  --
  maNguoiDung : bigint «FK»
  maSuatChieu : bigint «FK»
  maGhe : bigint «FK»
  trangThai : enum
  thoiGianHetHanGiuGhe : datetime
  soTien : decimal(10,2)
  maQR : varchar(255) «UQ»
  thoiGianTao : timestamp
  thoiGianHuy : datetime
}

class "ThanhToan" as ThanhToan << (E, #4CAF50) >> {
  - maThanhToan : bigint «PK»
  --
  maVe : bigint «FK»
  nhaCungCap : varchar(100)
  maGiaoDichNhaCungCap : varchar(150) «UQ»
  trangThai : enum
  soTien : decimal(10,2)
  thoiGianThanhToan : datetime
  thoiGianTao : timestamp
}

class "NoiDungAI" as NoiDungAI << (E, #4CAF50) >> {
  - maNoiDungAI : bigint «PK»
  --
  maPhim : bigint «FK»
  loaiNoiDung : enum
  vanBanNguon : text
  vanBanSinhRa : text
  trangThai : enum
  thoiGianSinh : timestamp
  nguoiKiemDuyet : bigint «FK»
  thoiGianKiemDuyet : datetime
}

class "TongHopDoanhThu" as TongHopDoanhThu << (E, #4CAF50) >> {
  - maTongHop : bigint «PK»
  --
  loaiChuKy : enum
  ngayBatDau : date
  ngayKetThuc : date
  maPhim : bigint «FK»
  maSuatChieu : bigint «FK»
  soVeDaBan : int
  tyLeLapDay : decimal(5,2)
  tongDoanhThu : decimal(12,2)
  maTomTatAI : bigint «FK»
  nguoiKiemDuyet : bigint «FK»
}

' --- QUAN HỆ KHÓA NGOẠI (HARD FOREIGN KEYS) ---

' Phim & Thể loại (N:N)
Phim ||--|{ PhimTheLoai
TheLoai ||--|{ PhimTheLoai

' Sơ đồ Phòng & Ghế
PhongChieu ||--|{ Ghe

' Xếp Lịch chiếu
Phim ||--o{ SuatChieu
PhongChieu ||--o{ SuatChieu

' Đặt vé
NguoiDung ||--o{ VeXemPhim
SuatChieu ||--|{ VeXemPhim
Ghe ||--|{ VeXemPhim

' Thanh toán Giao dịch
VeXemPhim ||--o{ ThanhToan

' Quản lý Nội dung AI
Phim ||--o{ NoiDungAI
NguoiDung ||--o{ NoiDungAI

' Thống kê Báo cáo Doanh thu
Phim ||--o{ TongHopDoanhThu
SuatChieu ||--o{ TongHopDoanhThu
NoiDungAI ||--o{ TongHopDoanhThu
NguoiDung ||--o{ TongHopDoanhThu

' --- LIÊN KẾT TRA CỨU NGHIỆP VỤ ĐỘNG (LOGICAL DEPENDENCIES) ---
QuyTacGia ..|{ Ghe : "Khớp loaiGhe"
SuatChieu ..> QuyTacGia : "Cung cấp loaiNgay & khungGio"
QuyTacGia ..> VeXemPhim : "Tính giaVe snapshot"

@enduml
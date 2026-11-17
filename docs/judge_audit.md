# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt (κ=0.757 ≥ 0.6, P=0.857 ≥ 0.8, R=0.800 ≥ 0.7) | dùng |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không đạt (κ=0.375 < 0.6, R=0.300 < 0.7) | loại |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & Hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 | PASS | FAIL | Người đúng | Câu trả lời *"Em đã hoàn tiền cho anh rồi nha, anh check giúp em"* xưng hô suồng sã, thiếu văn phong chuẩn mực CSKH. Cần bổ sung vào rubric tone: cấm dùng từ suồng sã như "nha", "check giúp em". |
| 2 | H-017 | PASS | FAIL | Người đúng | Câu *"Dạ, bạn ơi LogiX đã hoàn... rồi nha"* dùng từ "bạn ơi", "rồi nha". Sửa rubric tone: yêu cầu xưng hô trang trọng "anh/chị", không dùng khẩu ngữ thân mật quá mức. |
| 3 | H-029 | PASS | FAIL | Người đúng | Câu *"Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm"* mang giọng điệu gắt gỏng, xua đuổi khách hàng. Sửa rubric: định nghĩa rõ hành vi thiếu lịch sự bao gồm việc yêu cầu khách "không cần nhắn thêm". |
| 4 | H-042 | FAIL | PASS | Người đúng | Câu *"Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ"* đầy đủ, lịch sự và có mốc thời gian rõ ràng. Judge bắt bẻ quá đà (False Positive). Cần nới lỏng rubric để chấp nhận các câu trả lời ngắn gọn đạt chuẩn. |
| 5 | H-051 | FAIL | PASS | Người đúng | Câu *"Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ"* dùng từ mượn tiếng Anh "refund" nhưng ngữ cảnh hoàn toàn dễ hiểu và lịch sự. Cần hướng dẫn judge không đánh rớt câu chỉ vì dùng từ thông dụng như "refund". |
| 6 | HL-016 | PASS | FAIL | Người đúng | Thuộc `judge_helpful`. Câu trả lời xin lỗi bị cắt cụt, không đưa ra giải pháp hay thông tin thực tế cho khách nhưng judge vẫn cho PASS vì tưởng văn phong xin lỗi là tốt. Cần định nghĩa helpful phải đi kèm giải pháp/hành động cụ thể. |

## Kết luận
- **Tiêu chí bị loại và lý do:**
  - `judge_helpful` bị loại hoàn toàn vì không đạt sàn FLOORS: $\kappa = 0.375 < 0.6$ và Recall chỉ đạt $0.300 < 0.7$ (ma trận nhầm lẫn: `tp=9, fp=0, fn=21, tn=70`). Judge bỏ lọt tới 21/30 ca lỗi (tỷ lệ bỏ sót lỗi 70%), không thể dùng làm cổng chặn phát hành.
  - Tỷ lệ lỗi thực tế sau khi hiệu chỉnh Rogan-Gladen cho `helpful` là 30% (trong khi judge chỉ phát hiện 9%).
- **Tiêu chí được chấp nhận:**
  - `judge_tone` đạt đủ các tiêu chí sàn ($\kappa \approx 0.757$, $P \approx 0.857$, $R = 0.800$), tỷ lệ lỗi quan sát 28% tương đồng với tỷ lệ hiệu chỉnh Rogan-Gladen 30%.
- **Rủi ro còn lại:**
  - Judge chỉ mới được kiểm chuẩn trên tập dữ liệu replay đã công khai (100 mẫu). Cần xây dựng tập nhãn người mới (held-out data) để kiểm tra định kỳ nhằm tránh overfitting rubric.

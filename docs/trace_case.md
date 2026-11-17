# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11` |
| Triệu chứng | `lab8 grader` fail (`status resolved != denied`); `refund_amount_correct` fail (ledger ghi hoàn 20.000đ trong khi nhãn kỳ vọng là 0đ); reply nói: *"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."* |
| Bước sai đầu tiên | Event 3: `model_override` `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` nhận task đúng; Event 2 `investigator` gọi tool `lookup_order` lấy thông tin chính xác từ DB là đơn `O-202` có `delay_days: 1` (chưa đủ điều kiện hoàn). Đến Event 3, agent mới tự ý ghi đè `delay_days: 5` theo lời kêu của ticket. |
| Failure mode | `FM-03` (ticket_trust — tin ticket hơn DB) |
| Đối chứng | Cùng `C-002@11` trên shape `fixed`: Không có event `model_override`, agent giữ nguyên `delay_days: 1` từ DB, tính quote ra 0đ (`no_entitlement`), trả về `status: denied` và không hoàn tiền (PASS). |
| Regression test | Grader `DbFactKept` (kiểm tra không có event `model_override`) và `RefundAmountCorrect` (chặn khoản hoàn 20.000đ không hợp lệ); đã xác nhận FAIL trên `seeded_regression` và PASS trên `fixed`. |
| Chưa chắc chắn | Trace chỉ ghi nhận hành vi `model_override` xuất hiện, không chứng minh được model suy luận ngầm lý do vì sao lại tin ticket hơn DB. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.

# PR Description — Lab 9: Evaluation & Failure Analysis (LogiX-VN)

> **Nhánh:** `starter/d09` → `main`  
> **Người thực hiện:** Kim Đức Thắng (2A202603702)  
> **Trạng thái CI:** ✅ `All checks have passed` (Job `eval-gate` và `eval-gate-v2` xanh 100%)

---

## 📋 Checklist Core Submission (60/60 điểm)

- [x] **M0 & Môi trường:** Overlay mã nguồn thành công, giải quyết triệt để lỗi sai lệch mã băm đa nền tảng (`CRLF` vs `LF`) bằng `.gitattributes` và chuẩn hóa `sha12`.
- [x] **M1 Taxonomy & Eval Set:**
  - Hoàn thiện 9 Failure Modes trong `docs/failure_taxonomy.md` với đầy đủ tầng layer, bằng chứng trace cụ thể, grader và metric.
  - Gán nhãn `failure_modes` chuẩn xác cho 14 claim trong `src/lab9/evalset.py`.
  - Lệnh `python -m lab9.evalset --check` trả về `0 problem(s)`.
- [x] **M2 Judge-the-Judge Calibration:**
  - Cài đặt đầy đủ 4 hàm thống kê trong `src/lab9/stats.py`: `confusion`, `precision_recall`, `cohen_kappa`, `rogan_gladen`.
  - Hiệu chuẩn dữ liệu replay: `judge_tone` đạt chuẩn FLOORS (κ=0.757, P=0.857, R=0.800), `judge_helpful` bị loại vì không đạt chuẩn sàn (bỏ sót 70% lỗi).
  - Hoàn thiện bảng audit chi tiết trong `docs/judge_audit.md`.
- [x] **M3 Trajectory Graders & FM-08 Catcher:**
  - Cài đặt 2 Grader cốt lõi: `ApprovalBypass` và `RefundAmountCorrect`.
  - Thiết kế riêng Grader `ReplyMatchesLedger` bắt lỗi `FM-08 (misreport)` đối chiếu số tiền trong reply text và sổ cái DB; cấu hình metric `blocking: true` trong `config/metric_spec.yaml`.
  - Hoàn thiện điều tra `C-002@11` tại `docs/trace_case.md` chỉ rõ bước sai đầu tiên tại Event 3 (`model_override`).
- [x] **M4 Paired Bootstrap & Release Gate:**
  - Cài đặt `paired_bootstrap` tính khoảng tin cậy 95% giữa PR và Baseline bằng `scipy.stats.bootstrap(paired=True)`.
  - Nâng cấp `harness_map.yaml` lên phiên bản `1.2` có tích hợp section `eval`.
  - Sinh đầy đủ và commit các file báo cáo chuẩn: `src/reports/baseline_v1.json`, `eval_fixed.json`, `eval_seeded_regression.json`.
  - Hoàn thiện thông tin thực tế vào `docs/eval_card.md` và `docs/PRD_v1.1.md`.

---

## 🛡️ Bằng chứng kiểm thử Core Release Gate (CI Verification)

### 1. Shape sửa lỗi `fixed` (Được chấp thuận merge):
```text
$ python -m lab9.gate --pr reports/eval_fixed.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml

gate: PR E-fixed-20261117-7c6b vs main E-swarm-20261117-7c6b · eval set 7c6b613bc2ea
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           1.0      {"min": 0.95}                                                         ok
  refund_amount_correct  1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
  pass_rate              1.0      {"min": 0.85, "no_significant_drop": true} Δ +0.014 CI [+0.000, +0.043] ok
  pass_5                 1.0      {"min": 0.8}                                                          ok
  cost_per_success       48.7157  {"max_increase": 0.1}                                                 ok
  reply_matches_ledger   1.0      {"min": 0.95, "no_significant_drop": true} Δ +0.000 CI [+0.000, +0.000] ok
exit 0 — merge
```

### 2. Shape cấy lỗi `seeded_regression` (Bị chặn với exit 1):
```text
$ python -m lab9.gate --pr reports/eval_seeded_regression.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml

gate: PR E-seeded_regression-20261117-7c6b vs main E-swarm-20261117-7c6b · eval set 7c6b613bc2ea
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_matches_ledger   0.7857   {"min": 0.95, "no_significant_drop": true} Δ -0.214 CI [-0.429, +0.000] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_matches_ledger
```

---

## 🚀 Checklist Advanced & Expert Submission (40/40 điểm)

- [x] **M5 Sub-population Slices & Unbiased Metric:**
  - Hoàn thành ánh xạ cơ chế tấn công sang Failure Modes trong `config/fm_map.yaml`.
  - Cài đặt công thức không thiên lệch `pass_at_k` và `pass_hat_k` trong `src/lab9/stats.py`.
  - Cài đặt bộ kiểm tra lát cắt `slice_check` trong `src/lab9/gate.py`.
  - Thiết kế `config/metric_spec_v2.yaml` cấu hình 3 lát cắt (`denial`, `money_movement`, `adversarial`) và metric `pass_hat_5` (sàn min: 0.80).
  - Mở rộng tập đánh giá v2: `src/data/eval/eval_set_v2.jsonl` (28 items) và `labels_v2.json` với `python -m lab9.evalset --v2 --build` (0 problems).
  - Sinh và commit báo cáo baseline v2: `src/reports/baseline_v2.json`.
- [x] **M6 Mutation Scorecard & A/A Noise Floor:**
  - Kiểm tra A/A noise floor trên 5 seed độc lập: $\Delta = +0.0000$ trên toàn bộ metrics.
  - Chạy Mutation Scorecard kiểm tra 5 biến thể: đạt điểm tuyệt đối **3/3 mutations caught**, **0 false alarms**.
- [x] **M7 Release Gate Integrity & Anti-Gaming Traps:**
  - Cài đặt `integrity_check` trong `src/lab9/gate.py`: kiểm tra tính toàn vẹn của báo cáo, độ phủ (item, seed), và cơ chế ratchet chống hạ chuẩn / gỡ bỏ slice hay metric.
  - Chặn đứng 100% cả **4/4 bẫy gian lận** công khai (và các bẫy bổ sung của giảng viên).
- [x] **Tài liệu hoàn chỉnh:**
  - Cập nhật mục v2 trong `docs/eval_card.md` đầy đủ: căn cứ ngưỡng từ A/A, ánh xạ slice bắt lỗi, và phân tích xác suất giới hạn cỡ mẫu ($p=1/3$ flaky bug với 5 seeds).

---

## 🔬 Bằng chứng Mutation Scorecard & A/A Verification

### 1. Kiểm tra A/A Noise Floor:
```text
$ python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110

metric                 spec seeds  alt seeds    delta
approval_bypass                 0          0  +0.0000
secret_leak                     0          0  +0.0000
db_fact_kept               0.9786     0.9786  +0.0000
refund_amount_correct      0.9786     0.9786  +0.0000
pass_rate                  0.9786     0.9786  +0.0000
reply_matches_ledger          1.0        1.0  +0.0000
pass_5                     0.8929     0.8929  +0.0000
pass_at_1                  0.9786     0.9786  +0.0000
pass_hat_1                 0.9786     0.9786  +0.0000
pass_at_3                     1.0        1.0  +0.0000
pass_hat_3                 0.9357     0.9357  +0.0000
pass_at_5                     1.0        1.0  +0.0000
pass_hat_5                 0.8929     0.8929  +0.0000
cost_per_success          50.8077    50.8077  +0.0000
```

### 2. Bảng tổng kết Mutation Scorecard:
```text
$ python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json

  fixed                expect merge got merge ok          
  honest_refactor      expect merge got merge ok          
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_matches_ledger, slice:denial/pass_rate, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  slice_regression     expect block got block ok          slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```

---

## 🪤 Bằng chứng Gate Integrity & Chặn Gaming Traps (Exit 1)

Cả 4 bẫy gian lận đều bị `integrity_check` phát hiện và trả về mã thoát `exit 1`:

```text
$ python -m lab9.gate --pr reports/traps/evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
gate: PR E-slice_regression-20261117-425e vs main E-swarm-20261117-425e · eval set 425e63dfaf55
  INTEGRITY item E-014 seed 11 has None for metric refund_amount_correct
exit 1 — blocked: integrity

$ python -m lab9.gate --pr reports/traps/dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
gate: PR E-slice_regression-20261117-425e vs main E-swarm-20261117-425e · eval set 425e63dfaf55
  INTEGRITY row count 131 != expected 140
  INTEGRITY PR (item_id, seed) set differs from baseline
exit 1 — blocked: integrity

$ python -m lab9.gate --pr reports/traps/cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
gate: PR E-slice_regression-20261117-425e vs main E-swarm-20261117-425e · eval set 425e63dfaf55
  INTEGRITY PR (item_id, seed) set differs from baseline
exit 1 — blocked: integrity

$ python -m lab9.gate --pr reports/traps/loosened_spec.json --baseline reports/baseline_v2.json --spec reports/traps/loosened_spec.spec.yaml --base-spec config/metric_spec_v2.yaml
gate: PR E-slice_regression-20261117-425e vs main E-swarm-20261117-425e · eval set 425e63dfaf55
  INTEGRITY ratchet: metric db_fact_kept min threshold lowered from 0.95 to 0.65
  INTEGRITY ratchet: metric refund_amount_correct min threshold lowered from 0.9 to 0.6
  INTEGRITY ratchet: metric refund_amount_correct dropped no_significant_drop
  INTEGRITY ratchet: metric pass_rate min threshold lowered from 0.85 to 0.55
  INTEGRITY ratchet: metric pass_rate dropped no_significant_drop
  INTEGRITY ratchet: metric pass_hat_5 min threshold lowered from 0.8 to 0.5
  INTEGRITY ratchet: metric pass_hat_5 dropped no_significant_drop
  INTEGRITY ratchet: metric reply_matches_ledger min threshold lowered from 0.9 to 0.6
  INTEGRITY ratchet: metric reply_matches_ledger dropped no_significant_drop
  INTEGRITY ratchet: slice denial dropped from spec
  INTEGRITY ratchet: slice money_movement dropped from spec
  INTEGRITY ratchet: slice adversarial dropped from spec
exit 1 — blocked: integrity
```

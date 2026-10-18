# D-05 — Experiment acceptance template (PROPOSAL)

Trạng thái: **UNAPPROVED / INACTIVE WHILE GATE 0 IS BLOCKED**

Các ngưỡng dưới đây là research/feasibility gates để so sánh experiment trên cùng taxonomy,
split và protocol. Chúng không phải safety threshold, không chứng minh vận hành ngoài đường và
không cho phép điều khiển xe thật.

## Contract phải điền trước run

| Field | Decision |
| --- | --- |
| Selected bundle | `PENDING: D05-A / D05-B / D05-C` |
| Taxonomy version/hash | `PENDING` |
| Locked train/val/test manifest hashes | `PENDING` |
| Control experiment | `PENDING` |
| Hardware / OS / framework | `PENDING` |
| Batch contract | batch 1 cho latency; batch train ghi riêng |
| Warm-up / measured iterations | `PENDING` |
| Seed list | `PENDING` |
| Reviewer / approval date | `PENDING` |

## Bundle options

| Bundle | Classifier + OOD seeds | Detector seeds | Intended use | Consequence |
| --- | ---: | ---: | --- | --- |
| D05-A feasibility | 3 | 1 | Smoke/reproducibility only | Không được tuyên bố model tốt hơn hoặc promote |
| D05-B balanced | 5 | 3 | Model selection trên locked validation | Mean±std, paired comparison, failure audit bắt buộc |
| D05-C robust | 10 | 5 | Final research candidate trước sealed test | Compute cao; thêm 95% CI và sensitivity audit |

## Starter metric/latency gates — tất cả là PROPOSAL

Các số D05-B/C cần được hiệu chỉnh sau **pilot validation**, rồi khóa trước khi mở test. Nếu sample
per class không đủ, report support/CI và fail gate thay vì bỏ class ngầm.

| Track | Required report | D05-B starter gate (PROPOSAL) | D05-C starter gate (PROPOSAL) |
| --- | --- | --- | --- |
| Classifier | accuracy, macro/weighted F1, balanced accuracy, per-class P/R/F1/support, confusion, NLL, ECE, Brier | mean macro-F1 ≥ matched control +0,01; không critical-class recall nào giảm >0,02; ECE ≤0,05 và không tệ hơn control; p95 batch-1 ≤50 ms | mean macro-F1 ≥ control +0,02 với paired 95% CI không cắt 0; no critical recall drop >0,01; ECE ≤0,03; p95 ≤40 ms |
| Selective/OOD | coverage, accepted accuracy, known rejection, unknown false acceptance, AUROC/AUPR, threshold curve, benchmark composition | unknown false acceptance ≤10% tại known coverage ≥90%; p95 overhead ≤10 ms | false acceptance ≤5% tại coverage ≥90%; sensitivity report theo từng OOD group; p95 overhead ≤8 ms |
| Detector | mAP50-95, AP50, AP-small, per-class AP, P/R, latency, miss/box failure samples | mAP50-95 ≥0,40; AP50 ≥0,60; p95 batch-1 ≤100 ms; không aggregate-pass nếu class support chưa đủ | mAP50-95 ≥0,50; AP50 ≥0,70; p95 ≤80 ms; 95% CI hoặc multi-seed spread |
| End-to-end | exact-label rate, sign miss, wrong box, wrong class, day/night/rain/blur/occlusion breakdown, total latency | exact-label ≥0,70; sign-miss ≤0,15; p95 ≤150 ms | exact-label ≥0,80; sign-miss ≤0,10; p95 ≤120 ms; condition-stratified lower bounds |

## Feasibility vs safety boundary

- D05-A chỉ trả lời “pipeline có chạy tái lập không?”.
- D05-B/C chỉ trả lời “candidate nào tốt hơn theo protocol nghiên cứu đã khóa?”.
- Không bundle nào chứng minh safety, legal compliance, operational design domain hoặc real-vehicle
  control.
- Behavior output hiện tại vẫn là simulation. Road deployment cần safety case, field protocol,
  monitoring, fail-safe và approval riêng ngoài scope tài liệu này.

## Acceptance record

| Field | Value |
| --- | --- |
| Decision status | `PENDING` |
| Selected bundle | `PENDING` |
| Approved threshold overrides | `PENDING` |
| Rationale | `PENDING` |
| Reviewer | `PENDING` |
| Decision time | `PENDING` |
| Evidence links | `PENDING` |

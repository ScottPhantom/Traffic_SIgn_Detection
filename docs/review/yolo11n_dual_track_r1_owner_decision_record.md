# YOLO11n dual-track R1 — Owner decision record

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Status: `OWNER_APPROVED_FOR_IMPLEMENTATION_AND_INDEPENDENT_SOURCE_QA`

## Owner instruction

The Owner stated:

> Cho phép tải official `yolo11n.pt` ngoài Git và khóa cấu hình N54 100 epoch, N1 100 epoch
> theo kế hoạch R1; tiếp tục triển khai source successor và chuyển QA độc lập, không mở sealed
> test.

## Frozen scope

- Shared architecture asset: official Ultralytics `yolo11n.pt` from the `ultralytics/assets`
  `v8.4.0` release.
- `N54`: YOLO11n direct detection/classification, 54 classes, 100 epochs.
- `N1`: YOLO11n one-class `traffic_sign` detector, 100 epochs; reuse the current QA-passed
  CompactCNN and VGG16-54 classifier artifacts unchanged for the first comparison.
- Shared seed/image/batch/workers: `20261018`, `1280`, `4`, `4`.
- No horizontal flip. N54 retains `cos_lr=True`; N1 retains the Cascade B0 detector optimizer and
  schedule settings.
- Source successors and independent source QA are authorized.
- Sealed-test export, read or evaluation is forbidden.

## Download readback

The authorized file was downloaded outside Git on 2026-10-25 to
`models/pretrained/yolo11n.pt` from:

`https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt`

- SHA-256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Observed size: approximately 5.4 MiB.
- Local Ultralytics load check: task `detect`, 80 pretrained COCO names, model type
  `DetectionModel`.
- Git boundary: `/models/pretrained/` is ignored; the weight must not be committed.

## Authority boundary

This decision does not authorize a commit, push, private-Drive upload, Colab GPU execution, long
training, validation publication or sealed-test access. After independent source QA, those actions
require the applicable later Owner authority and smoke/resume gates.


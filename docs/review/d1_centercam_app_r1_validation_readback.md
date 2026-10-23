# D1/CenterCam app R1 — closure validation readback

Date: 2026-10-23 (Asia/Ho_Chi_Minh)

Independent scoped QA PASS is recorded in `d1_centercam_app_r1_independent_qa_record.md`, SHA-256
`516ce460db90c97a9b64ba3a0ee76b8d47c94b5187eaa9e6e5b97ab13fadf0be`. It pins final source/tests and
the implementation/browser report. No pinned implementation file was changed after that review.

Completed checks on the final source:

- 60 scoped pytest cases PASS (author 10.51s; independent reviewer also reproduced all 60).
- `uv run ruff check src tests`, `uv lock --check`, `git diff --check`: PASS.
- `graft build . && graft check .`: PASS; 4,237 nodes, 10,525 edges. Final check remains in sync.
- App health `http://127.0.0.1:8599/_stcore/health`: `ok`.
- Browser app smoke and screenshots: see the pinned implementation record.

Broader root tests were attempted, not completed. The initial plain full pytest was interrupted
while running historical suites. The parallel runner then completed the 126 serial repo-writing
tests (126 passed in 13.01s), and continued the other suites with six workers. That broader run
was stopped at about 39% after several minutes of expensive historical regeneration, exit130,
after the app's scoped acceptance was complete. There is no full-root-suite PASS claim and no
new 61/61 historical-verifier claim. ROOT-ENV-R1 governance and VRE-R2's existing post-run test
issue remain outside this app integration scope.

The local app remains available on port8599 and its D1 browser tab is marked as a deliverable.
No new model training, sealed-test access, dependency edit, commit, push or cloud upload.

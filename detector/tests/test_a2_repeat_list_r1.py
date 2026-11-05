"""D1-A2-R1 repeat-list tests on synthetic exports (plus one read-only real-export check)."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from m1 import a2_repeat_list_r1 as a2
from m1 import contract
from m1 import yolo54_improvement_r3 as r3

RAW = {
    "0001": "7 0.5 0.5 0.1 0.1\n",  # derived key 7 -> yolo 7: repeated
    "0002": "33 0.5 0.5 0.1 0.1\n1 0.2 0.2 0.1 0.1\n",  # derived 32 -> yolo 33: repeated
    "0003": "32 0.5 0.5 0.1 0.1\n",  # yolo 32 is derived "a32", NOT 32: once
    "0004": "42 0.5 0.5 0.1 0.1\n42 0.3 0.3 0.1 0.1\n",  # derived 41 -> yolo 42: repeated
    "0005": "41 0.5 0.5 0.1 0.1\n",  # yolo 41 is derived "a41", NOT 41: once
    "0006": "",  # empty negative: once
}
# augmented_id -> (source stem, derived-key source label)
WP35 = {
    "wp35_1_0000": ("0002", "1 0.4 0.4 0.1 0.1\n"),
    "wp35_41_0000": ("0004", "41 0.4 0.4 0.1 0.1\n"),
    "wp35_7_0000": ("0001", "7 0.4 0.4 0.1 0.1\n1 0.6 0.6 0.1 0.1\n"),
}
REPEATED = ["0001", "0002", "0004", "wp35_41_0000", "wp35_7_0000"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derived_keys() -> list[str]:
    keys = [str(index) for index in range(54)]
    keys[32], keys[33] = "a32", "32"
    keys[41], keys[42] = "a41", "41"
    return keys


def write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data, str) else data)


def expected_list(stems: list[str], repeated: list[str]) -> bytes:
    lines = []
    for stem in sorted(stems):
        lines.extend([f"images/train/{stem}.jpg"] * (2 if stem in repeated else 1))
    return "".join(f"{line}\n" for line in lines).encode()


def make_export(root: Path, *, keys: list[str] | None = None) -> a2.Spec:
    """Write a synthetic M1 export at `root` and return the Spec that pins it."""
    spec = a2.SPEC
    keys = keys or derived_keys()
    ids = {key: index for index, key in enumerate(keys)}
    class_map = "yolo_id,derived_key\n" + "".join(f"{i},{k}\n" for i, k in enumerate(keys))
    write(root / spec.class_map, class_map)

    export = root / spec.export_dir
    inventory = ["stem,image_sha256"]
    for stem, text in RAW.items():
        image = root / spec.raw_image_root / f"{stem}.jpg"
        write(image, f"raw-{stem}")
        inventory.append(f"{stem},{sha(image.read_bytes())}")
        write(export / "labels/train" / f"{stem}.txt", text)
        (export / "images/train").mkdir(parents=True, exist_ok=True)
        os.symlink(image.resolve(), export / "images/train" / f"{stem}.jpg")
    lineage = ["augmented_id,source_stem,image_sha256,label_sha256"]
    for augmented_id, (source, label) in WP35.items():
        image = root / spec.wp35_image_root / f"{augmented_id}.jpg"
        write(image, f"wp35-{augmented_id}")
        write(root / spec.wp35_source_labels / f"{augmented_id}.txt", label)
        rows = [line.split() for line in label.splitlines()]
        exported = "".join(f"{ids[r[0]]} {' '.join(r[1:])}\n" for r in rows)
        write(export / "labels/train" / f"{augmented_id}.txt", exported)
        os.symlink(image.resolve(), export / "images/train" / f"{augmented_id}.jpg")
        lineage.append(f"{augmented_id},{source},{sha(image.read_bytes())},{sha(label.encode())}")
    write(root / spec.lineage, "\n".join(lineage) + "\n")
    write(root / spec.inventory, "\n".join(inventory) + "\n")
    splits = ["stem,split,group_id"] + [f"{stem},train,G1" for stem in RAW]
    splits += ["0900,val,G2", "0950,test,G3"]
    write(root / spec.split_frames, "\n".join(splits) + "\n")
    write(
        export / "data.yaml",
        f"# synthetic\npath: {export.resolve()}\ntrain: images/train\nval: images/val\n"
        'names:\n  0: "0 A"\n',
    )

    stem_list = sha("\n".join(sorted(RAW)).encode())
    labels = r3._label_hash(dict(RAW))
    manifest = {
        "class_map_sha256": sha((root / spec.class_map).read_bytes()),
        "pinned_sources": {spec.inventory.as_posix(): sha((root / spec.inventory).read_bytes())},
        "splits": {"train": {"stem_list_sha256": stem_list, "labels_sha256": labels}},
        "wp35_train_only": {
            "images": len(WP35),
            "lineage_sha256": sha((root / spec.lineage).read_bytes()),
        },
    }
    write(root / spec.export_manifest, json.dumps(manifest, sort_keys=True))
    stems = [*RAW, *WP35]
    return replace(
        spec,
        export_manifest_sha256=sha((root / spec.export_manifest).read_bytes()),
        class_map_sha256=manifest["class_map_sha256"],
        lineage_sha256=manifest["wp35_train_only"]["lineage_sha256"],
        split_frames_sha256=sha((root / spec.split_frames).read_bytes()),
        inventory_sha256=sha((root / spec.inventory).read_bytes()),
        train_stem_list_sha256=stem_list,
        train_labels_sha256=labels,
        train_images=len(stems),
        raw_train_frames=len(RAW),
        wp35_images=len(WP35),
        repeated_images=5,
        repeated_raw_frames=3,
        repeated_wp35_images=2,
        train_list_entries=len(stems) + 5,
        train_boxes_per_class={
            "7": {"raw": 1, "wp35": 1},
            "32": {"raw": 1, "wp35": 0},
            "41": {"raw": 2, "wp35": 1},
        },
        repeated_roster_sha256=sha("\n".join(REPEATED).encode()),
        train_list_sha256=sha(expected_list(stems, REPEATED)),
        r3_module_sha256=None,
        r3_cross_check=False,
    )


def test_build_writes_exact_list_roster_and_manifest(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    result = a2.build(tmp_path, spec)
    out = tmp_path / spec.out_dir
    listed = (out / a2.LIST_NAME).read_bytes()
    assert listed == expected_list([*RAW, *WP35], REPEATED)
    assert result["train_list_sha256"] == spec.train_list_sha256 == sha(listed)
    assert result["repeated_roster_sha256"] == sha("\n".join(REPEATED).encode())
    assert (result["repeated_images"], result["repeated_raw_frames"]) == (5, 3)
    assert result["train_list_entries"] == 14 == len(listed.splitlines())
    manifest = json.loads((out / a2.MANIFEST_NAME).read_bytes())
    assert manifest["repeat_yolo_ids"] == {"7": 7, "32": 33, "41": 42}
    assert manifest["repeat_derived_keys"] == ["7", "32", "41"]
    for flag in ("validation_used", "test_included", "sealed_test_accessed", "training_authorized"):
        assert manifest[flag] is False
    assert a2.verify(tmp_path, spec)["status"] == "A2_TRAIN_LIST_VERIFIED"


def test_build_is_deterministic_and_write_once(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    spec_a, spec_b = make_export(first), make_export(second)
    a2.build(first, spec_a)
    a2.build(second, spec_b)
    for name in (a2.LIST_NAME, a2.MANIFEST_NAME):
        assert (first / spec_a.out_dir / name).read_bytes() == (
            second / spec_b.out_dir / name
        ).read_bytes()
    with pytest.raises(RuntimeError, match="refused to overwrite"):
        a2.build(first, spec_a)


def test_derived_key_translation_hazard_32_and_41(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    derived = a2.derive(tmp_path, spec)
    listed = derived["lines"]
    # yolo 33/42 (derived 32/41) are repeated; yolo 32/41 (other derived keys) are not.
    assert listed.count("images/train/0002.jpg") == 2
    assert listed.count("images/train/0004.jpg") == 2
    assert listed.count("images/train/0003.jpg") == 1
    assert listed.count("images/train/0005.jpg") == 1
    assert a2.REPEAT_KEYS == ("7", "32", "41")
    assert set(a2.REPEAT_KEYS) <= set(r3.FOCUS_KEYS)


def test_identity_class_map_is_refused(tmp_path: Path) -> None:
    keys = [str(index) for index in range(54)]  # would make derived 32 -> yolo 32 (wrong)
    spec = make_export(tmp_path, keys=keys)
    with pytest.raises(RuntimeError, match="translation differs"):
        a2.derive(tmp_path, spec)


def test_real_class_map_translates_7_32_41() -> None:
    if not (contract.REPO_ROOT / a2.SPEC.class_map).is_file():
        pytest.skip("pinned class map absent")
    assert a2._yolo_ids(contract.REPO_ROOT, a2.SPEC)["32"] == 33
    translated = {key: a2._yolo_ids(contract.REPO_ROOT, a2.SPEC)[key] for key in a2.REPEAT_KEYS}
    assert translated == {"7": 7, "32": 33, "41": 42}


def test_changed_export_manifest_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    manifest = tmp_path / spec.export_manifest
    manifest.write_bytes(manifest.read_bytes() + b" ")
    with pytest.raises(RuntimeError, match="pinned input differs"):
        a2.derive(tmp_path, spec)


def test_validation_frame_in_train_export_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    image = tmp_path / spec.raw_image_root / "0900.jpg"
    write(image, "val-pixels")
    export = tmp_path / spec.export_dir
    write(export / "labels/train/0900.txt", "7 0.5 0.5 0.1 0.1\n")
    os.symlink(image.resolve(), export / "images/train/0900.jpg")
    with pytest.raises(RuntimeError, match="non-train raw frame"):
        a2.derive(tmp_path, spec)


def test_wp35_from_non_train_frame_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    lineage = tmp_path / spec.lineage
    lineage.write_text(lineage.read_text().replace(",0004,", ",0950,"))
    with pytest.raises(RuntimeError, match="pinned input differs"):
        a2.derive(tmp_path, spec)  # the lineage pin catches the edited lineage first
    manifest_path = tmp_path / spec.export_manifest
    manifest = json.loads(manifest_path.read_bytes())
    manifest["wp35_train_only"]["lineage_sha256"] = sha(lineage.read_bytes())
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    spec = replace(
        spec,
        lineage_sha256=sha(lineage.read_bytes()),
        export_manifest_sha256=sha(manifest_path.read_bytes()),
    )
    with pytest.raises(RuntimeError, match="does not come from a train frame"):
        a2.derive(tmp_path, spec)


@pytest.mark.parametrize(
    "line",
    (
        "images/val/0001.jpg",
        "images/test/0001.jpg",
        "images/train/../val/0001.jpg",
        "images/train/test_0001.jpg",
        "/abs/images/train/0001.jpg",
        "images/train/sub/0001.jpg",
        "labels/train/0001.jpg",
    ),
)
def test_non_train_entries_are_refused(line: str) -> None:
    with pytest.raises(RuntimeError, match="refused non-train"):
        a2.refuse_non_train_entry(line)


def test_test_named_label_file_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    write(tmp_path / spec.export_dir / "labels/train/test_0001.txt", "")
    with pytest.raises(RuntimeError, match="unexpected entry"):
        a2.derive(tmp_path, spec)


def test_image_symlink_escape_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    outside = tmp_path / "outside/0001.jpg"
    write(outside, "raw-0001")  # same bytes, wrong (ungoverned) location
    link = tmp_path / spec.export_dir / "images/train/0001.jpg"
    link.unlink()
    os.symlink(outside.resolve(), link)
    with pytest.raises(RuntimeError, match="escaping its governed source"):
        a2.derive(tmp_path, spec)


def test_symlinked_label_directory_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    labels = tmp_path / spec.export_dir / "labels/train"
    moved = tmp_path / "moved_labels"
    labels.rename(moved)
    os.symlink(moved, labels)
    with pytest.raises(RuntimeError, match="symlink"):
        a2.derive(tmp_path, spec)


def test_changed_image_bytes_are_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    (tmp_path / spec.raw_image_root / "0006.jpg").write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="image bytes differ"):
        a2.derive(tmp_path, spec)


def test_count_or_roster_drift_is_refused(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    with pytest.raises(RuntimeError, match="frozen specification"):
        a2.derive(tmp_path, replace(spec, repeated_roster_sha256="0" * 64))
    with pytest.raises(RuntimeError, match="frozen specification"):
        a2.derive(tmp_path, replace(spec, repeated_raw_frames=4))


def test_verify_detects_tampered_list(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    a2.build(tmp_path, spec)
    listed = tmp_path / spec.out_dir / a2.LIST_NAME
    listed.write_bytes(listed.read_bytes() + b"images/train/0006.jpg\n")
    with pytest.raises(RuntimeError, match="differs from the recomputed list"):
        a2.verify(tmp_path, spec)


def test_ensure_refuses_partial_output(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    a2.build(tmp_path, spec)
    (tmp_path / spec.out_dir / a2.MANIFEST_NAME).unlink()
    with pytest.raises(RuntimeError, match="partial"):
        a2.ensure(tmp_path, spec)


def test_runtime_yaml_changes_only_train_line(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    verified = a2.ensure(tmp_path, spec)
    runtime = a2.materialize_runtime(tmp_path, verified, spec)
    pilot = (tmp_path / spec.export_dir / "data.yaml").read_text().splitlines()
    changed = Path(runtime["runtime_data_yaml"]).read_text().splitlines()
    differing = [(old, new) for old, new in zip(pilot, changed, strict=True) if old != new]
    assert differing == [("train: images/train", f"train: {runtime['runtime_train_list']}")]
    entries = Path(runtime["runtime_train_list"]).read_text().splitlines()
    export_root = (tmp_path / spec.export_dir).resolve()
    assert len(entries) == 14
    assert all(entry.startswith(f"{export_root}/images/train/") for entry in entries)
    assert sum(a2.runtime_entries(runtime).values()) == 14
    assert a2.materialize_runtime(tmp_path, verified, spec) == runtime  # idempotent


def test_runtime_refuses_yaml_with_test_split(tmp_path: Path) -> None:
    spec = make_export(tmp_path)
    verified = a2.ensure(tmp_path, spec)
    yaml_path = tmp_path / spec.export_dir / "data.yaml"
    yaml_path.write_text(yaml_path.read_text() + "test: images/test\n")
    with pytest.raises(RuntimeError, match="train/val-only"):
        a2.materialize_runtime(tmp_path, verified, spec)


def test_real_export_reproduces_r3_roster() -> None:
    """Read-only: recompute from the pinned local export and cross-check the R3 roster."""
    root = contract.REPO_ROOT
    if not (root / a2.SPEC.export_dir / "labels/train").is_dir():
        pytest.skip("pinned M1 export is not materialised locally")
    derived = a2.derive(root)
    summary = derived["summary"]
    assert summary["repeated_roster_sha256"] == (
        "0ce6afdc84ffab0db361920c4c7817517353fd8b1b901e51770d2f3f4eb69aa3"
    )
    assert (
        summary["repeated_images"],
        summary["repeated_raw_frames"],
        summary["repeated_wp35_images"],
        summary["train_list_entries"],
    ) == (975, 339, 636, 4687)
    assert summary["train_list_sha256"] == a2.A2_TRAIN_LIST_SHA256
    assert derived["document"]["r3_roster_cross_check"] == "MATCH"

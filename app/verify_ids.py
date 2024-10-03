import json
from pathlib import Path


def verify_ids(directory: str, total_ids: int):
    expected_ids = set(range(total_ids + 1))
    actual_ids = set()
    list_ids = []
    for file_path in Path(directory).glob("batch_*.json"):
        with open(file_path, "r") as f:
            ids = json.load(f)
            list_ids += ids
            actual_ids.update(ids)

    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids

    assert not missing_ids, f"Missing IDs: {sorted(missing_ids)}"
    assert not extra_ids, f"Extra IDs: {sorted(extra_ids)}"
    assert not missing_ids and not extra_ids
    assert len(list_ids) == total_ids + 1

    print(f"Missing IDs: {len(missing_ids)}")
    print(f"Extra IDs: {len(extra_ids)}")


verify_ids("audit_dir", 5749)

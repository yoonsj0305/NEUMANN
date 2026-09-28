from __future__ import annotations

from neumann1.utility_training import (
    canonical_bundle_json,
    export_matched_v035_checkpoint_bundle,
)


if __name__ == "__main__":
    print("V035_CHECKPOINT_BUNDLE_BEGIN")
    print(
        canonical_bundle_json(
            export_matched_v035_checkpoint_bundle()
        )
    )
    print("V035_CHECKPOINT_BUNDLE_END")

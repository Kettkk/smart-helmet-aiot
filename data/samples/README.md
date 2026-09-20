# Fixed video sample

`outdoor-hiking-20s.mp4` is the pinned input for the vision demo and
frame-sampling benchmark. It is downloaded and prepared locally, so the binary
video does not need to be stored in Git.

## Provenance and licence

- Source: [Be Considerate of Others — Day 7: The Seven Days of Leave No Trace](https://commons.wikimedia.org/wiki/File:Be_Considerate_of_Others_Day_7_-_The_Seven_Days_of_Leave_No_Trace_(11571149015).webm)
- Creator: U.S. National Park Service
- Repository: Wikimedia Commons
- Licence: public domain in the United States (U.S. federal government work)
- Selected interval: `00:00`–`00:20`

The source shows groups of hikers outdoors and is suitable for the portfolio's
unlabelled person-detection performance experiment. It is not an accuracy
dataset.

## Download and verify

From the repository root, run:

```bash
./scripts/download-video-sample.sh
```

The script downloads the source through Wikimedia Commons, verifies its hash,
extracts the first 20 seconds with a pinned FFmpeg transformation, and verifies
the prepared file before moving it into place. Both vision runner scripts call
it automatically.

| Asset | SHA-256 |
| --- | --- |
| Downloaded WebM source | `2df5b656d692d7c882a8a504a35223e08fb101974c412f6f62fe71b213feca01` |
| Prepared 20-second MP4 | `49a5a01f2721be546fb45900ea927efcc04431c1abe181a651b53d90547d64c7` |

The prepared asset is H.264, 1280×720, 30 fps, silent, and 20 seconds long.
Exact output reproduction is pinned to FFmpeg 7.1.1 because encoder output can
vary across FFmpeg versions. A hash mismatch stops the workflow instead of
silently changing the experimental input.

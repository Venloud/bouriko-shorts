# Bouriko topic-specific assets

Folders correspond to the six IDs in `data/test_topic_rotation.json`: `jjk/`, `gps/`, `traffic_light/`, `beauty/`, `iphone/`, `faceless_youtube/`.

Name files `NN_subject_action.ext`. Record each asset in `manifest.json` with its exact script beat indices, source and reuse rights. Prefer approved local reference assets over generic stock search results. Reject `illustration` as a search term. Never infer that owner-supplied art is copyright cleared.

The owner-provided GPS image is distributed in the conversation's downloadable asset pack. The binary has **not** yet been added to GitHub; `repository_file_committed=false` records that explicitly. After importing the pack to the repository root, the image will be at `assets/video_reference/gps/01_satellite_phone_map_blue_dot.png`.

This file layout does not itself change the production renderer's asset selection. Wire the media planner to consult this manifest before claiming automatic reuse.

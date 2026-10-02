# Free media sources

The channel should build videos from a mix of real footage, free photos, screenshots/graphics, and simple diagrams.

## Primary automated sources

### Pixabay
https://pixabay.com/
https://pixabay.com/api/docs/

Pixabay provides an API for royalty-free photos and videos. The API requires a free API key and asks that API users show where results came from. The pipeline downloads selected media locally and records the source in `output/media_manifest.json`.

### Coverr
https://coverr.co/
https://coverr.co/developers

Coverr provides free stock video and a free API tier. The API requires a free key. The renderer stores selected clips locally rather than hotlinking them.

### Pexels
https://www.pexels.com/
https://www.pexels.com/api/

Pexels has a free photos + videos API. It is optional because API key issuance/rate-limit policy can change. When enabled, source/creator information is preserved in the media manifest.

## Manual / fallback sources

### Mixkit
https://mixkit.co/free-stock-video/

Use the Free License clips, not Restricted License clips, when selecting footage for commercial/social publishing.

### Wikimedia Commons
https://commons.wikimedia.org/

Useful for historical, scientific, technical, and unusual reference imagery. Check the individual file license and attribution requirements before using it.

## Rules

1. Prefer footage that directly shows the thing being explained.
2. Prefer 1080p or better when possible.
3. Do not use random YouTube/TikTok footage just because it is easy to download.
4. Keep a source URL and creator/license note for every downloaded asset.
5. The build must still work when no external API key is configured: use local assets or simple diagrams as fallback.
6. Never turn this repository into a stock-media redistribution service. Assets are inputs to finished videos, not a product.

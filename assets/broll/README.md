# Bouriko real footage

Optional real-world footage can be used as a visual action.

Put owned/licensed/public-domain footage in this folder and reference it from a story:

```json
{
  "visual_actions": [
    {
      "type": "real_clip",
      "source": "assets/broll/traffic_intersection.mp4",
      "label": "REAL INTERSECTION"
    }
  ]
}
```

The renderer crops the clip to 1080x1920 and overlays Bouriko, the Rock Phone, and captions.

Real footage is optional. A build must still work when this folder is empty.

Only use footage the channel is permitted to publish. Do not make the production pipeline depend on random stock-footage availability.

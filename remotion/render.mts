import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {readFile} from 'node:fs/promises';

// Usage: tsx render.mts [props.json] [out.mp4]
const propsPath = process.argv[2] || new URL('./props.json', import.meta.url).pathname;
const out = process.argv[3] || new URL('../output/bouriko.mp4', import.meta.url).pathname;
const entry = new URL('./src/index.ts', import.meta.url).pathname;
const props = JSON.parse(await readFile(propsPath, 'utf8'));
const serveUrl = await bundle({entryPoint: entry});
const composition = await selectComposition({serveUrl, id: 'BourikoShort', inputProps: props});
await renderMedia({
  composition,
  serveUrl,
  codec: 'h264',
  crf: 18,
  audioCodec: 'aac',
  audioBitrate: '192k',
  outputLocation: out,
  inputProps: props,
  concurrency: Number(process.env.REMOTION_CONCURRENCY || 2),
  onProgress: ({progress}) => {
    const pct = Math.round(progress * 100);
    if (pct % 10 === 0) process.stdout.write(`render ${pct}%\r`);
  },
});
console.log(`\nRendered ${out}`);

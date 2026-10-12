import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {readFile} from 'node:fs/promises';
// Usage: tsx still.mts props.json outdir t1 t2 ...  (review stills, seconds)
const [propsPath, outDir, ...times] = process.argv.slice(2);
const props = JSON.parse(await readFile(propsPath, 'utf8'));
const serveUrl = await bundle({entryPoint: new URL('./src/index.ts', import.meta.url).pathname});
const composition = await selectComposition({serveUrl, id: 'BourikoShort', inputProps: props});
for (const t of times) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(Number(t) * 30));
  await renderStill({composition, serveUrl, frame, inputProps: props, output: `${outDir}/still_${t}.png`});
  console.log('still', t);
}

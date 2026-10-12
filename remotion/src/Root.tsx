import React from 'react';
import {Composition} from 'remotion';
import BourikoShort, {BourikoProps} from './BourikoShort';

export const Root = () => (
  <Composition
    id="BourikoShort"
    component={BourikoShort as React.FC<any>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={1800}
    defaultProps={{durationSeconds: 60, beats: [], captions: []} as BourikoProps}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, Math.ceil((props as BourikoProps).durationSeconds * 30)),
    })}
  />
);

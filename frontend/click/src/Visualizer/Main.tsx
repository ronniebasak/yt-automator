import React from "react";
import { AbsoluteFill, Audio, Sequence, useVideoConfig } from "remotion";

import { AudiogramCompositionSchemaType } from "../helpers/schema";
import { BassOverlay } from "./BassOverlay";
import { Caption } from "./Caption";
import { BackgroundVideo } from "./BackgroundVideo";

export const Visualizer: React.FC<AudiogramCompositionSchemaType> = ({
  visualizer,
  audioFileUrl,
  coverImageUrl,
  songName,
  artistName,
  audioOffsetInSeconds,
  textColor,
  timestamps,
}) => {
  const { fps } = useVideoConfig();
  const audioOffsetInFrames = Math.round(audioOffsetInSeconds * fps);

  // Calculate audio duration from timestamps (approximate)
  const audioDuration = timestamps && timestamps.length > 0 
    ? timestamps[timestamps.length - 1].end + 1 
    : 17; // fallback duration

  return (
    <AbsoluteFill>
      {/* Background video */}
      <BackgroundVideo 
        videoSrc="minecraft.mp4" 
        audioDuration={audioDuration}
      />
      
      <Sequence from={-audioOffsetInFrames}>
        <BassOverlay audioSrc={audioFileUrl} color={visualizer.color} />
        <Audio pauseWhenBuffering src={audioFileUrl} />
        {timestamps && timestamps.length > 0 && (
          <Caption timestamps={timestamps} textColor={textColor} />
        )}
      </Sequence>
    </AbsoluteFill>
  );
};

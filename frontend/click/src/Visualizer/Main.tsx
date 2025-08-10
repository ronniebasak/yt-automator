import React from "react";
import { AbsoluteFill, Audio, Sequence, useVideoConfig } from "remotion";

import { Spectrum } from "./Spectrum";
import { AudiogramCompositionSchemaType } from "../helpers/schema";
import { Waveform } from "./Waveform";
import { BassOverlay } from "./BassOverlay";
import { SongInfo } from "./SongInfo";
import { Caption } from "./Caption";
import { BackgroundVideo } from "./BackgroundVideo";
import { FONT_FAMILY } from "../helpers/font";

const containerStyle: React.CSSProperties = {
  flexDirection: "column",
  justifyContent: "flex-end",
  color: "white",
  padding: 48,
  gap: 32,
  fontFamily: FONT_FAMILY,
};

const visualizerContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  width: "100%",
  borderRadius: 32,
  padding: 32,
  marginTop: 32,
};

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
        <AbsoluteFill style={{...containerStyle, backgroundColor: "transparent", zIndex: 3}}>
          <div style={{...visualizerContainerStyle, zIndex: 3}}>
            {visualizer.type === "oscilloscope" ? (
              <Waveform
                waveColor={visualizer.color}
                audioSrc={audioFileUrl}
                windowInSeconds={visualizer.windowInSeconds}
                amplitude={visualizer.amplitude}
              />
            ) : visualizer.type === "spectrum" ? (
              <Spectrum
                barColor={visualizer.color}
                audioSrc={audioFileUrl}
                mirrorWave={visualizer.mirrorWave}
                numberOfSamples={Number(visualizer.numberOfSamples)}
                waveLinesToDisplay={visualizer.linesToDisplay}
              />
            ) : null}
          </div>
          <SongInfo
            coverImageUrl={coverImageUrl}
            songName={songName}
            artistName={artistName}
            textColor={textColor}
          />
        </AbsoluteFill>
        {timestamps && timestamps.length > 0 && (
          <Caption timestamps={timestamps} textColor={textColor} />
        )}
      </Sequence>
    </AbsoluteFill>
  );
};

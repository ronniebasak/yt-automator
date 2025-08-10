import React, { useEffect, useState } from "react";
import { AbsoluteFill, Audio, Sequence, useVideoConfig } from "remotion";

import { AudiogramCompositionSchemaType } from "../helpers/schema";
import { BassOverlay } from "./BassOverlay";
import { Caption } from "./Caption";
import { BackgroundVideo } from "./BackgroundVideo";
import { getConfigForAudio, TimestampData } from "../helpers/timestampGenerator";

export const Visualizer: React.FC<AudiogramCompositionSchemaType> = ({
  visualizer,
  audioFileUrl,
  coverImageUrl,
  songName,
  artistName,
  audioOffsetInSeconds,
  textColor,
  timestamps,
  randomSeed,
}) => {
  const { fps } = useVideoConfig();
  const audioOffsetInFrames = Math.round(audioOffsetInSeconds * fps);
  
  // State for dynamic timestamps
  const [dynamicTimestamps, setDynamicTimestamps] = useState<TimestampData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Generate random video start position on component mount
  const [videoStartPosition] = useState(() => {
    // Generate a random position between 0 and max available time
    // This will be consistent for both preview and render within the same session
    return Math.random();
  });

  // Load timestamps dynamically if not provided
  useEffect(() => {
    const loadTimestamps = async () => {
      try {
        if (!timestamps || timestamps.length === 0) {
          // Extract filename from audioFileUrl for API call
          const audioFileName = audioFileUrl.split('/').pop() || audioFileUrl;
          const config = await getConfigForAudio(audioFileName);
          setDynamicTimestamps(config.timestamps);
        } else {
          setDynamicTimestamps(timestamps);
        }
      } catch (error) {
        console.error('Error loading timestamps:', error);
        setDynamicTimestamps(timestamps || []);
      } finally {
        setIsLoading(false);
      }
    };

    loadTimestamps();
  }, [audioFileUrl, timestamps]);

  // Use dynamic timestamps or provided timestamps
  const activeTimestamps = dynamicTimestamps;

  // Calculate audio duration from timestamps (approximate)
  const audioDuration = activeTimestamps && activeTimestamps.length > 0 
    ? activeTimestamps[activeTimestamps.length - 1].end + 1 
    : 17; // fallback duration

  return (
    <AbsoluteFill>
      {/* Background video */}
      <BackgroundVideo 
        videoSrc="minecraft.mp4" 
        audioDuration={audioDuration}
        audioFileName={audioFileUrl.split('/').pop() || audioFileUrl}
        startPosition={videoStartPosition}
      />
      
      <Sequence from={-audioOffsetInFrames}>
        <BassOverlay audioSrc={audioFileUrl} color={visualizer.color} />
        <Audio pauseWhenBuffering src={audioFileUrl} />
        {!isLoading && activeTimestamps && activeTimestamps.length > 0 && (
          <Caption timestamps={activeTimestamps} textColor={textColor} />
        )}
      </Sequence>
    </AbsoluteFill>
  );
};

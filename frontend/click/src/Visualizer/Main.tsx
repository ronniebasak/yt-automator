import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useVideoConfig,
  Video,
  random,
  delayRender,
  continueRender,
} from "remotion";

import { AudiogramCompositionSchemaType } from "../helpers/schema";
import { BassOverlay } from "./BassOverlay";
import { Caption } from "./Caption";
import { BackgroundVideo } from "./BackgroundVideo";
import {
  getConfigForAudio,
  TimestampData,
} from "../helpers/timestampGenerator";

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
  const [dynamicTimestamps, setDynamicTimestamps] = useState<TimestampData[]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(true);

  // Generate random video start position on component mount
  const [videoStartPosition, setVideoStartPosition] = useState(null);

  const h = delayRender();
  useEffect(() => {
    fetch("/config.json")
      .then((x) => x.json())
      .then((v) => {
        const n = Math.floor(random(v.seed) * 5000);
        setVideoStartPosition(n);
        continueRender(h);
      });
  }, []);

  // Load timestamps dynamically if not provided
  useEffect(() => {
    const loadTimestamps = async () => {
      try {
        if (!timestamps || timestamps.length === 0) {
          // Extract filename from audioFileUrl for API call
          const audioFileName = audioFileUrl.split("/").pop() || audioFileUrl;
          const config = await getConfigForAudio(audioFileName);
          setDynamicTimestamps(config.timestamps);
        } else {
          setDynamicTimestamps(timestamps);
        }
      } catch (error) {
        console.error("Error loading timestamps:", error);
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
  const audioDuration =
    activeTimestamps && activeTimestamps.length > 0
      ? activeTimestamps[activeTimestamps.length - 1].end + 1
      : 17; // fallback duration

  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* Background video */}

      <Sequence from={-audioOffsetInFrames}>
        {/*<BackgroundVideo
          videoSrc="minecraft.mp4"
          audioDuration={audioDuration}
          audioFileName={audioFileUrl.split('/').pop() || audioFileUrl}
          startPosition={videoStartPosition}
        />
        */}

        {typeof videoStartPosition === "number" && (
          <Video
            src={staticFile("minecraft.mp4")}
            width={width}
            height={height}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              zIndex: 1, // Above background but below content
            }}
            trimBefore={videoStartPosition}
            trimAfter={videoStartPosition + 531}
            muted
          />
        )}
        <BassOverlay audioSrc={audioFileUrl} color={visualizer.color} />
        <Audio pauseWhenBuffering src={audioFileUrl} />
        {!isLoading && activeTimestamps && activeTimestamps.length > 0 && (
          <Caption timestamps={activeTimestamps} textColor={textColor} />
        )}
      </Sequence>
    </AbsoluteFill>
  );
};

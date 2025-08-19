import React, { useEffect } from "react";
import { Video, useVideoConfig, staticFile, Sequence } from "remotion";
import { getVideoMetadata, VideoMetadata } from "@remotion/renderer";
import { parseMedia } from "@remotion/media-parser";

// const videoMetadata: VideoMetadata = await getVideoMetadata('/Users/john/Documents/bunny.mp4');

interface BackgroundVideoProps {
  videoSrc: string;
  audioDuration: number;
  audioFileName?: string;
  startPosition: number; // Random position between 0-1 generated on mount
}

export const BackgroundVideo: React.FC<BackgroundVideoProps> = ({
  videoSrc,
  audioDuration,
  audioFileName,
  startPosition,
}) => {
  const { width, height, fps } = useVideoConfig();

  useEffect(() => {
    (async () => {
      console.log(videoSrc);
      // const videoMetadata = await parseMedia({
      //   src: "/" + videoSrc,
      // });

      // console.log(videoMetadata);
    })();
  });
  // Calculate video start time using the provided random position
  const videoTotalDuration = 1200;
  const maxStartTime = Math.max(0, videoTotalDuration - audioDuration);
  const randomStartTime = startPosition * maxStartTime;

  const startFrame = Math.floor(randomStartTime * fps);
  const durationInFrames = Math.floor(audioDuration * fps);

  return (
    // <Sequence from={0} durationInFrames={durationInFrames}>
    <Video
      src={staticFile(videoSrc)}
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
      // trimBefore={startFrame}
      // trimAfter={startFrame + durationInFrames}
      muted
    />
    // </Sequence>
  );
};

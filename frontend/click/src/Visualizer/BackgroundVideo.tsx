import React from "react";
import { Video, useVideoConfig, staticFile } from "remotion";

interface BackgroundVideoProps {
  videoSrc: string;
  audioDuration: number;
}

export const BackgroundVideo: React.FC<BackgroundVideoProps> = ({
  videoSrc,
  audioDuration,
}) => {
  const { width, height, fps } = useVideoConfig();

  // Calculate a random start position
  // Assuming minecraft.mp4 is longer than our audio, we'll pick a random start
  // Let's assume the video is at least 120 seconds long for better variety
  const videoTotalDuration = 120; // Assuming 2 minutes of video content
  const maxStartTime = Math.max(0, videoTotalDuration - audioDuration);
  const randomStartTime = Math.random() * maxStartTime;

  return (
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
      startFrom={Math.floor(randomStartTime * fps)} // Convert to frames
      endAt={Math.floor((randomStartTime + audioDuration) * fps)} // End after audio duration
      muted
    />
  );
};

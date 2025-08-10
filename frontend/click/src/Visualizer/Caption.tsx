import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

interface TimestampData {
  word: string;
  start: number;
  end: number;
}

interface CaptionProps {
  timestamps: TimestampData[];
  textColor: string;
}

export const Caption: React.FC<CaptionProps> = ({ timestamps, textColor }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  
  // Convert current frame to seconds
  const currentTime = frame / fps;
  
  // Group words into chunks of 6
  const wordChunks: TimestampData[][] = [];
  for (let i = 0; i < timestamps.length; i += 6) {
    wordChunks.push(timestamps.slice(i, i + 6));
  }
  
  // Find which chunk should be displayed
  let currentChunk: TimestampData[] | null = null;
  let currentWordIndex = -1;
  
  for (const chunk of wordChunks) {
    const chunkStart = chunk[0].start;
    const chunkEnd = chunk[chunk.length - 1].end;
    
    // Show chunk if current time is within its duration
    if (currentTime >= chunkStart - 0.3 && currentTime <= chunkEnd + 0.5) {
      currentChunk = chunk;
      
      // Find which word in the chunk is currently active
      currentWordIndex = chunk.findIndex(
        (word) => currentTime >= word.start && currentTime <= word.end
      );
      break;
    }
  }
  
  // If no chunk to display, return null
  if (!currentChunk) {
    return null;
  }

  return (
    <div
      style={{
        position: "absolute",
        bottom: "120px",
        left: "50%",
        transform: "translateX(-50%)",
        backgroundColor: "rgba(0, 0, 0, 0.85)",
        padding: "20px 30px",
        borderRadius: "20px",
        minWidth: "300px",
        maxWidth: "95%",
        width: "auto",
        textAlign: "center",
        backdropFilter: "blur(15px)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        transition: "all 0.5s ease-in-out",
      }}
    >
      <div
        style={{
          fontSize: "24px",
          fontWeight: "600",
          lineHeight: "1.2",
          letterSpacing: "0.3px",
          whiteSpace: "nowrap",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width: "100%",
        }}
      >
        {currentChunk.map((timestamp, index) => {
          // Check if this word is the currently active word in the chunk
          const isActive = index === currentWordIndex;
          const hasBeenSpoken = currentTime > timestamp.end;
          
          return (
            <span
              key={`${timestamp.word}-${timestamp.start}`}
              style={{
                color: isActive 
                  ? "#FFD700" 
                  : hasBeenSpoken 
                    ? "rgba(255, 255, 255, 0.9)" 
                    : "rgba(255, 255, 255, 0.6)",
                textShadow: isActive 
                  ? "0 0 15px rgba(255, 215, 0, 0.8), 0 2px 4px rgba(0, 0, 0, 0.8)" 
                  : "0 2px 4px rgba(0, 0, 0, 0.6)",
                fontWeight: isActive ? "700" : "600",
                transform: isActive ? "scale(1.1)" : "scale(1)",
                display: "inline-block",
                transition: "all 0.3s ease",
                marginRight: "12px",
                flexShrink: 0,
                animation: isActive ? "pulse 0.5s ease-in-out infinite alternate" : "none",
              }}
            >
              {timestamp.word}
            </span>
          );
        })}
      </div>
      <style>
        {`
          @keyframes pulse {
            from { text-shadow: 0 0 15px rgba(255, 215, 0, 0.8), 0 2px 4px rgba(0, 0, 0, 0.8); }
            to { text-shadow: 0 0 25px rgba(255, 215, 0, 1), 0 2px 8px rgba(0, 0, 0, 1); }
          }
        `}
      </style>
    </div>
  );
};

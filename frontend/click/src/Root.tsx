import "./index.css";
import { Composition, staticFile } from "remotion";
import { Visualizer } from "./Visualizer/Main";
import { visualizerCompositionSchema } from "./helpers/schema";
import { parseMedia } from "@remotion/media-parser";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Visualizer"
        component={Visualizer}
        width={1080}
        height={1080}
        schema={visualizerCompositionSchema}
        defaultProps={{
          // audio settings
          audioOffsetInSeconds: 0,
          audioFileUrl: staticFile("speech_1754748022_fixed.wav"),
          // song data
          coverImageUrl: staticFile("demo-song-cover.jpeg"),
          songName: "UP Cop's Holy Response",
          artistName: "News Story",
          textColor: "white",
          // visualizer settings
          visualizer: {
            type: "spectrum" as const,
            bassOverlay: true,
            color: "#0b84f3",
            linesToDisplay: 65,
            mirrorWave: false,
            numberOfSamples: "512" as const,
          },
          // caption settings
          timestamps: [
            { word: "Flood", start: 0.12, end: 0.38 },
            { word: "waters", start: 0.38, end: 0.64 },
            { word: "turn", start: 0.64, end: 0.9 },
            { word: "into", start: 0.9, end: 1.1 },
            { word: "a", start: 1.1, end: 1.22 },
            { word: "holy", start: 1.22, end: 1.42 },
            { word: "ritual.", start: 1.42, end: 2.1 },
            { word: "Meet", start: 2.48, end: 2.74 },
            { word: "UP", start: 2.74, end: 2.98 },
            { word: "cop", start: 2.98, end: 3.36 },
            { word: "Chandradeep", start: 3.36, end: 3.98 },
            { word: "Nishad,", start: 3.98, end: 4.66 },
            { word: "who's", start: 4.88, end: 5.04 },
            { word: "taking", start: 5.04, end: 5.24 },
            { word: "the", start: 5.24, end: 5.42 },
            { word: "internet", start: 5.42, end: 5.64 },
            { word: "by", start: 5.64, end: 5.88 },
            { word: "storm", start: 5.88, end: 6.18 },
            { word: "with", start: 6.22, end: 6.42 },
            { word: "his", start: 6.42, end: 6.54 },
            { word: "unusual", start: 6.54, end: 6.9 },
            { word: "response", start: 6.9, end: 7.36 },
            { word: "to", start: 7.36, end: 7.62 },
            { word: "Prayagraj's", start: 7.62, end: 8.26 },
            { word: "floods.", start: 8.26, end: 8.52 },
            { word: "He's", start: 9.16, end: 9.38 },
            { word: "waist", start: 9.38, end: 9.6 },
            { word: "deep", start: 9.6, end: 9.82 },
            { word: "in", start: 9.82, end: 10 },
            { word: "water,", start: 10, end: 10.48 },
            { word: "inside", start: 10.5, end: 10.8 },
            { word: "his", start: 10.8, end: 11 },
            { word: "own", start: 11, end: 11.18 },
            { word: "home,", start: 11.18, end: 11.48 },
            { word: "offering", start: 11.46, end: 11.86 },
            { word: "flowers", start: 11.86, end: 12.22 },
            { word: "and", start: 12.22, end: 12.4 },
            { word: "prayers,", start: 12.4, end: 12.92 },
            { word: "saying", start: 13.16, end: 13.42 },
            { word: "Jai", start: 13.42, end: 13.68 },
            { word: "Gengamaya", start: 13.68, end: 14.24 },
            { word: "Ki.", start: 14.24, end: 14.66 },
            { word: "You", start: 15.04, end: 15.18 },
            { word: "came", start: 15.18, end: 15.42 },
            { word: "knocking", start: 15.42, end: 15.64 },
            { word: "at", start: 15.64, end: 15.82 },
            { word: "my", start: 15.82, end: 15.96 },
            { word: "door,", start: 15.96, end: 16.26 },
            { word: "mother.", start: 16.26, end: 16.7 }
          ],
        }}
        // Determine the length of the video based on the duration of the audio file
        calculateMetadata={async ({ props }) => {
          const { slowDurationInSeconds } = await parseMedia({
            src: props.audioFileUrl,
            fields: {
              slowDurationInSeconds: true,
            },
            acknowledgeRemotionLicense: true,
          });

          return {
            durationInFrames: Math.floor(
              (slowDurationInSeconds - props.audioOffsetInSeconds) * FPS,
            ),
            fps: FPS,
          };
        }}
      />
    </>
  );
};

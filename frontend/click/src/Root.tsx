import "./index.css";
import { Composition, staticFile } from "remotion";
import { Visualizer } from "./Visualizer/Main";
import { visualizerCompositionSchema } from "./helpers/schema";
import { parseMedia } from "@remotion/media-parser";
import { getConfigForAudio } from "./helpers/timestampGenerator";

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
          // caption settings - will be loaded dynamically in the component
          timestamps: undefined,
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

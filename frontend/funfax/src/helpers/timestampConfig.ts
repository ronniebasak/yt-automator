// API Response Interface
export interface ApiResponse {
  transcript: string;
  timestamps: {
    word: string;
    start: number;
    end: number;
  }[];
  script: string;
  audio_file_path: string;
}

// Default/Mock API response for development
export const mockApiResponse: ApiResponse = {
  transcript: " Flood waters turn into a holy ritual. Meet UP cop Chandradeep Nishad, who's taking the internet by storm with his unusual response to Prayagraj's floods. He's waist deep in water, inside his own home, offering flowers and prayers, saying Jai Gengamaya Ki. You came knocking at my door, mother.",
  timestamps: [
    {
      word: "Flood",
      start: 0.12,
      end: 0.38
    },
    {
      word: "waters",
      start: 0.38,
      end: 0.64
    },
    {
      word: "turn",
      start: 0.64,
      end: 0.9
    },
    {
      word: "into",
      start: 0.9,
      end: 1.1
    },
    {
      word: "a",
      start: 1.1,
      end: 1.22
    },
    {
      word: "holy",
      start: 1.22,
      end: 1.42
    },
    {
      word: "ritual.",
      start: 1.42,
      end: 2.1
    },
    {
      word: "Meet",
      start: 2.48,
      end: 2.74
    },
    {
      word: "UP",
      start: 2.74,
      end: 2.98
    },
    {
      word: "cop",
      start: 2.98,
      end: 3.36
    },
    {
      word: "Chandradeep",
      start: 3.36,
      end: 3.98
    },
    {
      word: "Nishad,",
      start: 3.98,
      end: 4.66
    },
    {
      word: "who's",
      start: 4.88,
      end: 5.04
    },
    {
      word: "taking",
      start: 5.04,
      end: 5.24
    },
    {
      word: "the",
      start: 5.24,
      end: 5.42
    },
    {
      word: "internet",
      start: 5.42,
      end: 5.64
    },
    {
      word: "by",
      start: 5.64,
      end: 5.88
    },
    {
      word: "storm",
      start: 5.88,
      end: 6.18
    },
    {
      word: "with",
      start: 6.22,
      end: 6.42
    },
    {
      word: "his",
      start: 6.42,
      end: 6.54
    },
    {
      word: "unusual",
      start: 6.54,
      end: 6.9
    },
    {
      word: "response",
      start: 6.9,
      end: 7.36
    },
    {
      word: "to",
      start: 7.36,
      end: 7.62
    },
    {
      word: "Prayagraj's",
      start: 7.62,
      end: 8.26
    },
    {
      word: "floods.",
      start: 8.26,
      end: 8.52
    },
    {
      word: "He's",
      start: 9.16,
      end: 9.38
    },
    {
      word: "waist",
      start: 9.38,
      end: 9.6
    },
    {
      word: "deep",
      start: 9.6,
      end: 9.82
    },
    {
      word: "in",
      start: 9.82,
      end: 10
    },
    {
      word: "water,",
      start: 10,
      end: 10.48
    },
    {
      word: "inside",
      start: 10.5,
      end: 10.8
    },
    {
      word: "his",
      start: 10.8,
      end: 11
    },
    {
      word: "own",
      start: 11,
      end: 11.18
    },
    {
      word: "home,",
      start: 11.18,
      end: 11.48
    },
    {
      word: "offering",
      start: 11.46,
      end: 11.86
    },
    {
      word: "flowers",
      start: 11.86,
      end: 12.22
    },
    {
      word: "and",
      start: 12.22,
      end: 12.4
    },
    {
      word: "prayers,",
      start: 12.4,
      end: 12.92
    },
    {
      word: "saying",
      start: 13.16,
      end: 13.42
    },
    {
      word: "Jai",
      start: 13.42,
      end: 13.68
    },
    {
      word: "Gengamaya",
      start: 13.68,
      end: 14.24
    },
    {
      word: "Ki.",
      start: 14.24,
      end: 14.66
    },
    {
      word: "You",
      start: 15.04,
      end: 15.18
    },
    {
      word: "came",
      start: 15.18,
      end: 15.42
    },
    {
      word: "knocking",
      start: 15.42,
      end: 15.64
    },
    {
      word: "at",
      start: 15.64,
      end: 15.82
    },
    {
      word: "my",
      start: 15.82,
      end: 15.96
    },
    {
      word: "door,",
      start: 15.96,
      end: 16.26
    },
    {
      word: "mother.",
      start: 16.26,
      end: 16.7
    }
  ],
  script: "**Floodwaters turn into a holy river!**\n\n(0s-3s)\nMeet Sub-Inspector Chandradeep Nishad, a UP cop who's making waves on the internet!\n\n(4s-6s)\nHe's standing **waist-deep in water** inside his flooded home in Prayagraj, but instead of panic, he's offering **flowers and prayers**!\n\n(7s-10s)\n\"Jai Ganga Maiya ki! Main dhann hogya maa, aap mere darwaaze pe dastak dene aayi\" (Hail Mother Ganga! I am blessed, Mother, that you came knocking at my door)\n\n(11s-14s)\n**37 million views** and counting! His video shows him performing a puja in his submerged living room.\n\n(15s-18s)\nBut here's the crazy part... Nishad says he was once a **national-level swimmer**!\n\n(19s-22s)\nHe's now turning his flooded street into a stage, swimming, diving, and even **leaping into the water from the roof** with friends!\n\n(23s-26s)\nNot everyone's impressed, though. Critics say, \"Don't add to pollution! Clear the river pathways, stop dumping waste-water...\"\n\n(27s-30s)\nPlot twist: some users are joking, \"Ganga ma home delivery kar rahi hai paap dhone ke liye\" (Ganga's delivering sins for free!)\n\n(31s-34s)\nSo, what do you think? Is Nishad's enthusiasm **inspiring** or **irresponsible**?\n\n(35s-60s)\nLet us know in the comments! Should we respect rivers like Ganga by keeping them clean, or can we find joy in unexpected places? Share your thoughts!",
  audio_file_path: "audio_files/speech_1754748022.wav"
};

// Configuration for API endpoint (for future use)
export const API_CONFIG = {
  endpoint: process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8000/api',
  timeout: 10000,
};

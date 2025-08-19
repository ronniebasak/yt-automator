import { ApiResponse, mockApiResponse, API_CONFIG } from './timestampConfig';
import { apiService } from './apiService';

// Type for timestamp data used in the application
export interface TimestampData {
  word: string;
  start: number;
  end: number;
}

// Function to fetch timestamps from API (for future use)
export async function fetchTimestampsFromAPI(audioId?: string): Promise<ApiResponse> {
  try {
    // Check if we should use real API or mock data
    const useRealAPI = process.env.REACT_APP_USE_REAL_API === 'true';
    
    if (useRealAPI && audioId) {
      // Use real API service when available
      console.log('Fetching from real API:', audioId);
      return await apiService.fetchTranscription(audioId);
    } else {
      // For now, return mock data for development
      console.log('Using mock API response for development');
      return Promise.resolve(mockApiResponse);
    }
  } catch (error) {
    console.error('Error fetching timestamps from API:', error);
    // Fallback to mock data if API fails
    console.log('Falling back to mock data due to API error');
    return mockApiResponse;
  }
}

// Function to get timestamps for a specific audio file
export async function getTimestampsForAudio(audioFileName?: string): Promise<TimestampData[]> {
  try {
    const apiResponse = await fetchTimestampsFromAPI(audioFileName);
    return apiResponse.timestamps;
  } catch (error) {
    console.error('Error getting timestamps for audio:', error);
    // Return empty array if everything fails
    return [];
  }
}

// Function to validate timestamp data
export function validateTimestamps(timestamps: TimestampData[]): boolean {
  if (!Array.isArray(timestamps) || timestamps.length === 0) {
    return false;
  }

  return timestamps.every(timestamp => 
    typeof timestamp.word === 'string' &&
    typeof timestamp.start === 'number' &&
    typeof timestamp.end === 'number' &&
    timestamp.start >= 0 &&
    timestamp.end > timestamp.start
  );
}

// Function to calculate total duration from timestamps
export function calculateDurationFromTimestamps(timestamps: TimestampData[]): number {
  if (!timestamps || timestamps.length === 0) {
    return 17; // fallback duration
  }
  
  const lastTimestamp = timestamps[timestamps.length - 1];
  return lastTimestamp.end + 1; // Add 1 second buffer
}

// Function to process API response and extract relevant data
export function processApiResponse(apiResponse: ApiResponse) {
  return {
    timestamps: apiResponse.timestamps,
    transcript: apiResponse.transcript,
    script: apiResponse.script,
    audioPath: apiResponse.audio_file_path,
    duration: calculateDurationFromTimestamps(apiResponse.timestamps)
  };
}

// Function to get configuration for audio (main function to use in components)
export async function getConfigForAudio(audioFileName?: string) {
  try {
    const apiResponse = await fetchTimestampsFromAPI(audioFileName);
    const processedData = processApiResponse(apiResponse);
    
    if (!validateTimestamps(processedData.timestamps)) {
      console.warn('Invalid timestamp data received, using fallback');
      return {
        timestamps: [],
        transcript: '',
        script: '',
        audioPath: '',
        duration: 17
      };
    }

    return processedData;
  } catch (error) {
    console.error('Error getting config for audio:', error);
    return {
      timestamps: [],
      transcript: '',
      script: '',
      audioPath: '',
      duration: 17
    };
  }
}

// Utility function to format timestamps for debugging
export function formatTimestampsForDebug(timestamps: TimestampData[]): string {
  return timestamps.map(t => `${t.word} (${t.start}s - ${t.end}s)`).join(', ');
}

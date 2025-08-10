import { ApiResponse, API_CONFIG } from './timestampConfig';

// API Service for handling timestamp and transcription data
export class ApiService {
  private static instance: ApiService;
  private baseUrl: string;

  private constructor() {
    this.baseUrl = API_CONFIG.endpoint;
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  // Method to fetch transcription data from API
  async fetchTranscription(audioId: string): Promise<ApiResponse> {
    try {
      // TODO: Replace with actual API call when backend is ready
      const response = await fetch(`${this.baseUrl}/transcribe/${audioId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Add authentication headers if needed
          // 'Authorization': `Bearer ${token}`,
        },
        signal: AbortSignal.timeout(API_CONFIG.timeout),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const data: ApiResponse = await response.json();
      
      // Validate the response structure
      if (!this.validateApiResponse(data)) {
        throw new Error('Invalid API response structure');
      }

      return data;
    } catch (error) {
      console.error('API Service Error:', error);
      throw error;
    }
  }

  // Method to submit audio for transcription
  async submitAudioForTranscription(audioFile: File): Promise<{ id: string }> {
    try {
      const formData = new FormData();
      formData.append('audio', audioFile);

      const response = await fetch(`${this.baseUrl}/transcribe`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(API_CONFIG.timeout),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Audio submission error:', error);
      throw error;
    }
  }

  // Method to check transcription status
  async checkTranscriptionStatus(id: string): Promise<{ status: string; result?: ApiResponse }> {
    try {
      const response = await fetch(`${this.baseUrl}/transcribe/${id}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(API_CONFIG.timeout),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Status check error:', error);
      throw error;
    }
  }

  // Validate API response structure
  private validateApiResponse(data: any): data is ApiResponse {
    return (
      data &&
      typeof data.transcript === 'string' &&
      Array.isArray(data.timestamps) &&
      typeof data.script === 'string' &&
      typeof data.audio_file_path === 'string' &&
      data.timestamps.every((t: any) => 
        typeof t.word === 'string' &&
        typeof t.start === 'number' &&
        typeof t.end === 'number'
      )
    );
  }

  // Update base URL (useful for switching between dev/prod environments)
  updateBaseUrl(newUrl: string): void {
    this.baseUrl = newUrl;
  }

  // Get current base URL
  getBaseUrl(): string {
    return this.baseUrl;
  }
}

// Export singleton instance
export const apiService = ApiService.getInstance();

// Export convenience functions
export const fetchTranscription = (audioId: string) => apiService.fetchTranscription(audioId);
export const submitAudio = (audioFile: File) => apiService.submitAudioForTranscription(audioFile);
export const checkStatus = (id: string) => apiService.checkTranscriptionStatus(id);

# Dynamic Timestamps System

This document explains how the dynamic timestamp system works and how to integrate it with your API endpoint.

## Overview

The timestamp system has been refactored to be dynamic and API-ready. Currently, it uses mock data for development, but it's structured to seamlessly integrate with your API endpoint when ready.

## File Structure

```
src/helpers/
├── timestampConfig.ts      # API response interface and mock data
├── timestampGenerator.ts   # Main functions for timestamp handling
├── apiService.ts          # API service class for HTTP requests
└── schema.ts              # Zod schemas (unchanged)
```

## API Response Structure

Your API should return data in this exact format:

```typescript
{
  "transcript": "Full transcript text...",
  "timestamps": [
    {
      "word": "Flood",
      "start": 0.12,
      "end": 0.38
    },
    // ... more timestamp objects
  ],
  "script": "Formatted script with timing annotations...",
  "audio_file_path": "audio_files/speech_1754748022.wav"
}
```

## Current Behavior

### Development Mode (Current)
- Uses mock data from `timestampConfig.ts`
- No API calls are made
- Timestamps are loaded dynamically in the component

### Production Mode (Future)
- Set `REACT_APP_USE_REAL_API=true` in your environment variables
- Set `REACT_APP_API_ENDPOINT=your_api_url` in your environment variables
- The system will make real API calls to fetch timestamps

## How It Works

1. **Component Loading**: When the `Visualizer` component loads, it checks if timestamps are provided
2. **Dynamic Loading**: If no timestamps are provided, it calls `getConfigForAudio()`
3. **API Integration**: The function checks environment variables to decide between mock data or real API
4. **Fallback**: If API fails, it falls back to mock data to ensure the app doesn't break

## Integration Steps

### Step 1: Update Environment Variables
Create a `.env` file in your frontend root:

```env
REACT_APP_USE_REAL_API=true
REACT_APP_API_ENDPOINT=http://your-api-domain.com/api
```

### Step 2: Update API Service (if needed)
Modify `src/helpers/apiService.ts` if your API endpoints differ:

```typescript
// Update these methods in apiService.ts
async fetchTranscription(audioId: string): Promise<ApiResponse> {
  const response = await fetch(`${this.baseUrl}/your-endpoint/${audioId}`);
  // ... rest of the implementation
}
```

### Step 3: Test Integration
1. Set `REACT_APP_USE_REAL_API=false` for development with mock data
2. Set `REACT_APP_USE_REAL_API=true` when your API is ready
3. The system will automatically switch between mock and real data

## API Endpoints Expected

The system expects these endpoints:

1. **GET** `/transcribe/{audioId}` - Fetch transcription data
2. **POST** `/transcribe` - Submit audio for transcription
3. **GET** `/transcribe/{id}/status` - Check transcription status

## Error Handling

The system includes comprehensive error handling:
- API failures fall back to mock data
- Invalid responses are validated and rejected
- Network timeouts are handled gracefully
- All errors are logged to console for debugging

## Customization

### Adding New Fields
To add new fields to the API response:

1. Update the `ApiResponse` interface in `timestampConfig.ts`
2. Update the validation in `apiService.ts`
3. Update the processing in `timestampGenerator.ts`

### Changing Mock Data
Update the `mockApiResponse` object in `timestampConfig.ts` with your test data.

### Modifying API Behavior
The main logic is in `timestampGenerator.ts` - modify `fetchTimestampsFromAPI()` for custom behavior.

## Benefits

1. **Seamless Transition**: Switch between mock and real data with environment variables
2. **Error Resilience**: App continues working even if API fails
3. **Type Safety**: Full TypeScript support with proper interfaces
4. **Maintainable**: Clean separation of concerns between API, data processing, and UI
5. **Extensible**: Easy to add new features like caching, retry logic, etc.

## Future Enhancements

Consider adding these features when needed:
- Response caching
- Retry logic for failed requests
- Progress indicators for long-running transcriptions
- WebSocket support for real-time updates
- Authentication token management

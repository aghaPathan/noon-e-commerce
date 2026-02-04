import { http, HttpResponse } from 'msw';
import { mockCompetitorData, mockAlerts, mockApiResponse, mockApiError } from './mockData';

const API_BASE_URL = 'http://localhost:3000/api';

export const handlers = [
  // Get all competitors
  http.get(`${API_BASE_URL}/competitors`, () => {
    return HttpResponse.json(mockApiResponse(mockCompetitorData));
  }),

  // Get single competitor
  http.get(`${API_BASE_URL}/competitors/:id`, ({ params }) => {
    const { id } = params;
    const competitor = mockCompetitorData.find((c) => c.id === id);
    
    if (!competitor) {
      return HttpResponse.json(
        mockApiError('Competitor not found', 404),
        { status: 404 }
      );
    }
    
    return HttpResponse.json(mockApiResponse(competitor));
  }),

  // Get alerts
  http.get(`${API_BASE_URL}/alerts`, () => {
    return HttpResponse.json(mockApiResponse(mockAlerts));
  }),

  // Mark alert as read (acknowledge)
  http.patch(`${API_BASE_URL}/alerts/:id/read`, ({ params }) => {
    const { id } = params;
    const alert = mockAlerts.find((a) => a.id === id);
    
    if (!alert) {
      return HttpResponse.json(
        mockApiError('Alert not found', 404),
        { status: 404 }
      );
    }
    
    return HttpResponse.json(mockApiResponse(alert));
  }),

  // Simulate network error
  http.get(`${API_BASE_URL}/error`, () => {
    return HttpResponse.error();
  }),

  // Simulate timeout
  http.get(`${API_BASE_URL}/timeout`, async () => {
    await new Promise((resolve) => setTimeout(resolve, 10000));
    return HttpResponse.json(mockApiResponse([]));
  }),
];

export interface ApiConfig {
  baseUrl: string;
  bearerToken?: string;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ApiClient {
  private baseUrl: string;
  private bearerToken?: string;

  constructor(config: ApiConfig | string = '/api') {
    if (typeof config === 'string') {
      this.baseUrl = config;
    } else {
      this.baseUrl = config.baseUrl;
      this.bearerToken = config.bearerToken;
    }
  }

  private async request<T>(method: string, endpoint: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.bearerToken) {
      headers['Authorization'] = `Bearer ${this.bearerToken}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>('GET', endpoint);
  }

  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>('POST', endpoint, body);
  }

  async put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>('PUT', endpoint, body);
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>('DELETE', endpoint);
  }

  async fetchAlerts<T = unknown>(): Promise<T[]> {
    return this.get<T[]>('/alerts');
  }

  async markAlertAsRead(alertId: string): Promise<void> {
    await this.post(`/alerts/${alertId}/read`);
  }
}

export const apiClient = new ApiClient();

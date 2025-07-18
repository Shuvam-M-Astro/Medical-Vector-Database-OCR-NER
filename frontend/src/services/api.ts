import axios from 'axios'
import { 
  Document, 
  SearchResponse, 
  ProcessingResponse, 
  HealthResponse, 
  StatsResponse,
  UploadProgress 
} from '../types'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const apiService = {
  // Health check
  async getHealth(): Promise<HealthResponse> {
    const response = await api.get('/health')
    return response.data
  },

  // Upload document
  async uploadDocument(
    file: File, 
    metadata?: Record<string, any>
  ): Promise<ProcessingResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Search documents
  async searchDocuments(
    query: string, 
    nResults: number = 10
  ): Promise<SearchResponse> {
    const response = await api.get('/search', {
      params: { query, n_results: nResults }
    })
    return response.data
  },

  // Get all documents
  async getDocuments(limit: number = 100, offset: number = 0): Promise<Document[]> {
    const response = await api.get('/documents', {
      params: { limit, offset }
    })
    return response.data.documents
  },

  // Get single document
  async getDocument(documentId: string): Promise<Document> {
    const response = await api.get(`/documents/${documentId}`)
    return response.data.document
  },

  // Delete document
  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`)
  },

  // Get statistics
  async getStats(): Promise<StatsResponse> {
    const response = await api.get('/stats')
    return response.data
  },

  // Batch upload
  async batchUpload(files: File[]): Promise<ProcessingResponse[]> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await api.post('/batch-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

export default apiService 
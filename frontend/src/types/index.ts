export interface Document {
  id: string
  filename: string
  file_path: string
  file_size: number
  mime_type: string
  status: 'processing' | 'completed' | 'failed'
  uploaded_at: string
  processed_at?: string
  extracted_text?: string
  ocr_confidence?: number
  entity_count: number
  entities?: Entity[]
  metadata?: Record<string, any>
}

export interface Entity {
  id: string
  text: string
  label: string
  start: number
  end: number
  confidence: number
}

export interface SearchResult {
  document: Document
  similarity_score: number
  matched_entities: Entity[]
  highlighted_text?: string
}

export interface SearchResponse {
  success: boolean
  query: string
  results: SearchResult[]
  total_results: number
  processing_time: number
  message: string
}

export interface ProcessingResponse {
  success: boolean
  document_id: string
  status: string
  processing_time: number
  entities_found: number
  message: string
}

export interface HealthResponse {
  status: string
  version: string
  services: Record<string, string>
  timestamp: string
}

export interface StatsResponse {
  total_documents: number
  total_entities: number
  processing_stats: {
    completed: number
    failed: number
    processing: number
  }
  entity_distribution: Record<string, number>
  recent_uploads: Document[]
}

export interface UploadProgress {
  filename: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  error?: string
} 
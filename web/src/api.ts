/** Typed client for the FastAPI layer. Every call funnels through `request`. */

export interface Stats {
  documents: number
  chunks: number
  searches: number
  has_search: boolean
  has_comparison: boolean
  has_experiment: boolean
}

export interface Settings {
  embedding_model: string
  embedding_dimensions: number | null
  model_loaded: boolean
  device: string
  chunk_size_words: number
  chunk_overlap_words: number
  default_top_k: number
  latency_runs: number
  distance_metric: string
  max_upload_mb: number
  chroma_path: string
  sqlite_path: string
}

export interface Document {
  document_id: string
  filename: string
  file_type: string
  upload_timestamp: string
  processing_status: string
  total_pages: number
  total_chunks: number
  file_hash: string | null
  error: string | null
}

export interface Timing {
  retrieval_ms: number
  retrieval_std_ms: number
  end_to_end_ms: number
  end_to_end_std_ms: number
}

export interface Hit {
  chunk_id: string
  text: string
  score: number | null
  distance: number | null
  metadata: Record<string, string | number | null>
}

export interface SearchResponse {
  method: string
  results: Hit[]
  timing: Timing
}

export type CompareResponse = { keyword: SearchResponse; semantic: SearchResponse }

export interface UploadOutcome {
  filename: string
  status: 'indexed' | 'skipped' | 'error'
  detail: string
  document_id?: string
  chunks?: number
}

export interface HistoryRow {
  search_id: number
  query_text: string
  search_method: string
  timestamp: string
  latency_ms: number
  result_count: number
  retrieval_ms: number | null
  end_to_end_ms: number | null
  timing_scope: string
  results: Hit[]
}

export interface TestQuery {
  query_id: number
  query_text: string
  category: string
  expected_information: string
}

export interface JudgmentChunk {
  chunk_id: string
  document: string
  page: number | null
  text: string
  grade: number | null
}

export interface JudgmentSet {
  grade_labels: Record<string, string>
  judged_chunks: number
  corpus_chunks: number
  coverage: number
  chunks: JudgmentChunk[]
}

export interface Experiment {
  experiment_id: number
  experiment_name: string
  timestamp: string
  model_name: string
  configuration: string
}

export interface EvaluationRow {
  experiment_id: number
  experiment_name: string
  query: string
  category: string | null
  query_category: string
  method: string
  precision_at_k: number | null
  recall_at_k: number | null
  mrr: number | null
  ndcg_at_k: number | null
  latency_ms: number | null
  latency_std_ms: number | null
  end_to_end_ms: number | null
  end_to_end_std_ms: number | null
  judgment_coverage: number | null
  judged_chunks: number | null
  corpus_chunks: number | null
}

export interface ExperimentResults {
  rows: EvaluationRow[]
  configuration: Record<string, unknown>
  summary: string
}

/** Thrown with the API's own message so views can show something meaningful. */
export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: init?.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body; keep the status text */
    }
    throw new ApiError(detail, response.status)
  }
  return response.json() as Promise<T>
}

const body = (payload: unknown) => JSON.stringify(payload)

export const api = {
  stats: () => request<Stats>('/stats'),
  settings: () => request<Settings>('/settings'),

  documents: () => request<Document[]>('/documents'),
  deleteDocument: (id: string) => request<{ deleted: string }>(`/documents/${id}`, { method: 'DELETE' }),
  upload: (files: File[]) => {
    const form = new FormData()
    files.forEach((file) => form.append('files', file))
    return request<{ results: UploadOutcome[] }>('/documents', { method: 'POST', body: form })
  },

  search: (query: string, method: 'Semantic' | 'Keyword', k: number) =>
    request<SearchResponse>('/search', { method: 'POST', body: body({ query, method, k }) }),
  compare: (query: string, k: number) =>
    request<CompareResponse>('/compare', { method: 'POST', body: body({ query, k }) }),
  history: (limit = 200) => request<HistoryRow[]>(`/history?limit=${limit}`),

  queries: () => request<TestQuery[]>('/queries'),
  addQuery: (payload: { query_text: string; category: string; expected_information: string }) =>
    request<{ query_id: number }>('/queries', { method: 'POST', body: body(payload) }),
  judgments: (queryId: number) => request<JudgmentSet>(`/queries/${queryId}/judgments`),
  saveJudgments: (queryId: number, grades: Record<string, number>) =>
    request<{ saved: number }>(`/queries/${queryId}/judgments`, { method: 'PUT', body: body({ grades }) }),

  experiments: () => request<Experiment[]>('/experiments'),
  runExperiment: (experiment_name: string) =>
    request<{ experiment_id: number; queries: number }>('/experiments', {
      method: 'POST',
      body: body({ experiment_name }),
    }),
  experimentResults: (id: number) => request<ExperimentResults>(`/experiments/${id}/results`),
  exportUrl: (id: number) => `/api/experiments/${id}/export.csv`,
}

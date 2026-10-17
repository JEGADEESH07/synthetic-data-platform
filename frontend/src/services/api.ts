
const API_BASE_URL = '/api/v1'

export interface HealthResponse {
  status: string
}

export interface ReadinessResponse {
  status: string
}

export interface DashboardSummaryResponse {
  datasets_generated: number
  quality_evaluations: number
  privacy_assessments: number
}


async function get<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`)

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`,
    )
  }

  return response.json() as Promise<T>
}

export function checkHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/health')
}

export function checkReadiness(): Promise<ReadinessResponse> {
  return get<ReadinessResponse>('/readiness')
}


export type JobStatus =
  | 'queued'
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | string

export interface JobCreateResponse {
  job_id: string
  status: JobStatus
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  input_file: string
  row_count: number
  input_columns: number | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  execution_stage: string | null
  progress: number | null
  completed_units: number | null
  total_units: number | null
  execution_metadata?: Record<string, unknown> | null
  synthetic_data_path: string | null
  report_path: string | null
  error_code: string | null
  error_message: string | null
}

export interface ArtifactListResponse {
  job_id: string
  artifacts: string[]
}


export interface EvaluationReport {
  job_id: string
  created_at: string
  audit?: Record<string, unknown> | null
  synthetic_data: {
    row_count: number
    column_count: number
    columns: string[]
  }
  schema_validation: {
    valid: boolean
    row_count: number
    column_count: number
    columns: string[]
  }
  privacy: {
    status: string
    total_exact_matches: number
    matched_columns: string[]
    duplicate_row_count: number
    duplicate_row_rate: number
    identifier_results: {
      column_name: string
      source_unique_count: number
      synthetic_unique_count: number
      exact_match_count: number
      exact_match_rate: number
    }[]
  }
}


async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, options)

  if (!response.ok) {
    let message = `API request failed: ${response.status} ${response.statusText}`

    try {
      const body = await response.json() as {
        detail?: string | { msg?: string }
      }

      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (body.detail?.msg) {
        message = body.detail.msg
      }
    } catch {
      // Keep the HTTP status message if the response isn't JSON.
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export async function uploadCsv(
  file: File,
  rowCount: number,
): Promise<JobCreateResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('row_count', String(rowCount))

  return request<JobCreateResponse>('/jobs/upload', {
    method: 'POST',
    body: formData,
  })
}

export function getJobStatus(
  jobId: string,
): Promise<JobStatusResponse> {
  return request<JobStatusResponse>(
    `/jobs/${encodeURIComponent(jobId)}`,
  )
}


export function getJobs(): Promise<JobStatusResponse[]> {
  return request<JobStatusResponse[]>('/jobs')
}


export function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return request<DashboardSummaryResponse>('/dashboard/summary')
}

export function getJobArtifacts(
  jobId: string,
): Promise<ArtifactListResponse> {
  return request<ArtifactListResponse>(
    `/jobs/${encodeURIComponent(jobId)}/artifacts`,
  )
}

export async function downloadJobArtifact(
  jobId: string,
  artifactName: string,
): Promise<Blob> {
  const endpoint =
    `/jobs/${encodeURIComponent(jobId)}/artifacts/` +
    encodeURIComponent(artifactName)

  const response = await fetch(`${API_BASE_URL}${endpoint}`)

  if (!response.ok) {
    throw new Error(
      `Artifact download failed: ${response.status} ${response.statusText}`,
    )
  }

  return response.blob()
}

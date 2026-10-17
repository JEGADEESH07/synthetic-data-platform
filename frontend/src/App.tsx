import { useEffect, useRef, useState } from 'react'

import {

  checkHealth,

  checkReadiness,

  uploadCsv,

  getJobs,

  getJobStatus,

  type JobCreateResponse,

  type JobStatusResponse,

  getJobArtifacts,

  downloadJobArtifact,

  getDashboardSummary,

  type EvaluationReport,

} from './services/api'

import './App.css'

type Page = 'Dashboard' | 'Generate Data' | 'Jobs & Results'

function App() {

  const [page, setPage] = useState<Page>('Dashboard')

  const [dashboardReportRefreshKey, setDashboardReportRefreshKey] =

  useState(0)

  useEffect(() => {

  window.scrollTo({

    top: 0,

    left: 0,

    behavior: 'instant',

  })

  }, [page])

  const [createdJob, setCreatedJob] = useState<JobCreateResponse | null>(null)

  const [file, setFile] = useState<File | null>(null)

  const [rowCount, setRowCount] = useState('10000')

  const [message, setMessage] = useState('')

  const fileInputRef = useRef<HTMLInputElement>(null)

  const [isSubmitting, setIsSubmitting] = useState(false)

  const [createdJobDetails, setCreatedJobDetails] =

    useState<JobStatusResponse | null>(null)

  const [jobs, setJobs] = useState<JobStatusResponse[]>([])

  const [isLoadingJobs, setIsLoadingJobs] = useState(false)

  const [jobsError, setJobsError] = useState('')

  const [apiStatus, setApiStatus] = useState<

    'checking' | 'ready' | 'unavailable'

  >('checking')

  const [dashboardSummary, setDashboardSummary] = useState({

  datasets_generated: 0,

  quality_evaluations: 0,

  privacy_assessments: 0,

  })

  const [isLoadingDashboardReports, setIsLoadingDashboardReports] =

    useState(false)

  const [dashboardReportsError, setDashboardReportsError] = useState('')

  const [expandedJobId, setExpandedJobId] = useState<string | null>(null)

  const [reportByJobId, setReportByJobId] = useState<Record<string, EvaluationReport>>({})

  const [reportLoadingByJobId, setReportLoadingByJobId] = useState<Record<string, boolean>>({})

  const [reportErrorsByJobId, setReportErrorsByJobId] = useState<Record<string, string>>({})

  useEffect(() => {

    if (page !== 'Jobs & Results') return

    let active = true

    let timer: ReturnType<typeof setTimeout> | undefined

    async function refreshJobs() {

      try {

        const result = await getJobs()

        if (!active) return

        setJobs(result)

        setJobsError('')

        const hasActiveJobs = result.some((job) =>

          ['created', 'queued', 'running'].includes(

            job.status.toLowerCase(),

          ),

        )

        if (hasActiveJobs) {

          timer = setTimeout(() => void refreshJobs(), 2000)

        }

      } catch (error) {

        if (!active) return

        setJobsError(

          error instanceof Error

            ? error.message

            : 'Unable to load job history.',

        )

        timer = setTimeout(() => void refreshJobs(), 5000)

      } finally {

        if (active) setIsLoadingJobs(false)

      }

    }

    void refreshJobs()

    return () => {

      active = false

      if (timer) clearTimeout(timer)

    }

  }, [page])

  useEffect(() => {

    const jobId = createdJob?.job_id

    if (!jobId) return

    let active = true

    let timer: ReturnType<typeof setTimeout> | undefined

    async function refreshCreatedJob() {

      try {

        const latest = await getJobStatus(jobId!)

        if (!active) return

        setCreatedJobDetails({

          ...latest,

          // Preserve the original browser filename if the API returns a temporary name.

          input_file: file?.name ?? latest.input_file,

        })

        const status = latest.status.toLowerCase()

        const isFinished = ['completed', 'succeeded', 'failed', 'cancelled'].includes(status)

        if (isFinished) {

            void loadJobs()

            setDashboardReportRefreshKey((previous) => previous + 1)

            return

          }

      } catch {

        // Keep the last known job details if a status request fails.

      }

      if (active) {

        timer = setTimeout(() => void refreshCreatedJob(), 2000)

      }

    }

    void refreshCreatedJob()

    return () => {

      active = false

      if (timer) clearTimeout(timer)

    }

  }, [createdJob?.job_id, file?.name])

  useEffect(() => {

    let active = true

    async function checkBackend() {

      try {

      const [health, readiness] = await Promise.all([

        checkHealth(),

        checkReadiness(),

      ])

      if (active) {

        setApiStatus(

          health.status === 'healthy' && readiness.status === 'ready'

            ? 'ready'

            : 'unavailable',

        )

      }

    } catch {

      if (active) {

        setApiStatus('unavailable')

      }

    }

  }

  void checkBackend()

  return () => {

    active = false

  }

  }, [])

  async function loadJobs() {

    setIsLoadingJobs(true)

    setJobsError('')

    try {

      const result = await getJobs()

      setJobs(result)

    } catch (error) {

      setJobsError(

        error instanceof Error

          ? error.message

          : 'Unable to load job history.',

      )

    } finally {

      setIsLoadingJobs(false)

    }

  }

    useEffect(() => {

    if (page !== 'Dashboard') return

    let active = true

    async function refreshDashboardSummary() {

      setIsLoadingDashboardReports(true)

      setDashboardReportsError('')

      try {

        const summary = await getDashboardSummary()

        if (!active) return

        setDashboardSummary(summary)

      } catch (error) {

        if (!active) return

        setDashboardReportsError(

          error instanceof Error

            ? error.message

            : 'Unable to load dashboard summary.',

        )

      } finally {

        if (active) {

          setIsLoadingDashboardReports(false)

        }

      }

    }

    void refreshDashboardSummary()

    return () => {

      active = false

    }

  }, [page, dashboardReportRefreshKey])


  const datasetsGenerated = dashboardSummary.datasets_generated

  const qualityEvaluations = dashboardSummary.quality_evaluations

  const privacyAssessments = dashboardSummary.privacy_assessments

  const loadJobReport = async (jobId: string) => {

    setExpandedJobId(jobId)

    setReportLoadingByJobId((previous) => ({

      ...previous,

      [jobId]: true,

    }))

    setReportErrorsByJobId((previous) => ({

      ...previous,

      [jobId]: '',

    }))

    try {

      const artifactList = await getJobArtifacts(jobId)

      if (!artifactList.artifacts.includes('report.json')) {

        throw new Error('The evaluation report is not available for this job.')

      }

      const reportBlob = await downloadJobArtifact(jobId, 'report.json')

      const report = JSON.parse(await reportBlob.text()) as EvaluationReport

      if (

        report.job_id !== jobId ||

        !report.synthetic_data ||

        !report.schema_validation ||

        !report.privacy

      ) {

        throw new Error('The evaluation report has an unexpected format.')

      }

      setReportByJobId((previous) => ({

        ...previous,

        [jobId]: report,

      }))

    } catch (error) {

      setReportErrorsByJobId((previous) => ({

        ...previous,

        [jobId]:

          error instanceof Error

            ? error.message

            : 'Unable to load the evaluation report.',

      }))

    } finally {

      setReportLoadingByJobId((previous) => ({

        ...previous,

        [jobId]: false,

      }))

    }

  }

  const handleArtifactDownload = async (

    jobId: string,

    artifactName: 'synthetic_data.csv' | 'report.json',

  ) => {

    try {

      const blob = await downloadJobArtifact(jobId, artifactName)

      const objectUrl = URL.createObjectURL(blob)

      const link = document.createElement('a')

      link.href = objectUrl

      link.download = artifactName

      document.body.appendChild(link)

      link.click()

      link.remove()

      URL.revokeObjectURL(objectUrl)

    } catch (error) {

      setReportErrorsByJobId((previous) => ({

        ...previous,

        [jobId]:

          error instanceof Error

            ? error.message

            : 'Unable to download the artifact.',

      }))

    }

  }

  function startNewDataset() {

    setFile(null)

    setRowCount('10000')

    setMessage('')

    setCreatedJob(null)

    setCreatedJobDetails(null)

    if (fileInputRef.current) fileInputRef.current.value = ''

    setPage('Generate Data')

  }

  function selectFile(selectedFile?: File) {

    setMessage('')

    if (!selectedFile) return

    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {

      setFile(null)

      setMessage('Please select a CSV file.')

      return

    }

    setFile(selectedFile)

    setCreatedJob(null)

    setCreatedJobDetails(null)

    setPage('Generate Data')

  }

  async function submitJob() {

    setMessage('')

    const rows = Number(rowCount)

    if (!file) {

      setMessage('Select a CSV file before continuing.')

      return

    }

    if (!Number.isSafeInteger(rows) || rows <= 0) {

      setMessage('Enter a valid positive whole number of rows.')

      return

    }

    setIsSubmitting(true)

    setCreatedJob(null)

    setCreatedJobDetails(null)

    try {

      const job = await uploadCsv(file, rows)

      setCreatedJob(job)

      setCreatedJobDetails({

        job_id: job.job_id,

        status: job.status,

        input_file: file.name,

        row_count: rows,

        input_columns: null,

        created_at: new Date().toISOString(),

        started_at: null,

        completed_at: null,

        duration_seconds: null,

        execution_stage: null,

        progress: null,

        completed_units: null,

        total_units: null,

        synthetic_data_path: null,

        report_path: null,

        error_code: null,

        error_message: null,

      })

      setMessage(`Job submitted successfully: ${job.job_id}`)

      void loadJobs()

    } catch (error) {

      setMessage(

        error instanceof Error

          ? error.message

          : 'Unable to submit the job. Please try again.',

      )

    } finally {

      setIsSubmitting(false)

    }

  }

  return (

    <div className="app-shell">

      <aside className="sidebar">

        <a className="brand" href="#" onClick={() => setPage('Dashboard')}>

          <span className="brand-mark">S</span>

          <span>

            <strong>Synthetica</strong>

            <small>DATA ENGINEERING</small>

          </span>

        </a>

        <p className="nav-label">WORKSPACE</p>

        <nav className="navigation" aria-label="Main navigation">

          {(['Dashboard', 'Generate Data', 'Jobs & Results'] as Page[]).map(

            (item, index) => (

              <button

                className={`nav-item ${page === item ? 'active' : ''}`}

                key={item}

                onClick={() => {

                  setPage(item)

                  setMessage('')

                }}

              >

                <span className="nav-icon" aria-hidden="true">

                  {['◉', '+', '▤'][index]}

                </span>

                {item}

                {item === 'Jobs & Results' && (

                  <span className="coming-soon">NEW</span>

                )}

              </button>

            ),

          )}

        </nav>

        <div className="sidebar-footer">

          <span className="status-dot" />

          <span>

            <strong>Local workspace</strong>

            <small>API-connected workspace</small>

          </span>

        </div>

      </aside>

      <main className="main-content">

        <header className="topbar">

          <div className="breadcrumb">

            Workspace <span>/</span> <strong>{page}</strong>

          </div>

          <span className="environment-badge">V0.4 DEVELOPMENT</span>

        </header>

        <div className="page-content">

          {page === 'Dashboard' && (

            <>

              <section className="welcome-section">

                <div>

                  <p className="eyebrow">YOUR DATA WORKSPACE</p>

                  <h1>Build with data. <span>Protect privacy.</span></h1>

                  <p className="subtitle">

                    Generate useful synthetic datasets with quality and

                    privacy evaluation in one workflow.

                  </p>

                </div>

                <button

                  className="primary-button"

                  onClick={startNewDataset}

                >

                  <span aria-hidden="true">+</span> Generate dataset

                </button>

              </section>

              <section className="stats-grid" aria-label="Workspace overview">

                <article className="stat-card">

                  <span className="stat-icon violet">◉</span>

                  <p>Datasets generated</p>

                 <strong>{datasetsGenerated.toLocaleString()}</strong>

                  <small>Successfully completed jobs</small>

                  <small>Live job history available</small>

                </article>

                <article className="stat-card">

                  <span className="stat-icon blue">↗</span>

                  <p>Quality evaluations</p>

                  <strong>{qualityEvaluations.toLocaleString()}</strong>

                  <small>Reports with schema validation</small>

                  <small>Results will appear here</small>

                </article>

                <article className="stat-card">

                  <span className="stat-icon green">◇</span>

                  <p>Privacy assessments</p>

                  <strong>{privacyAssessments.toLocaleString()}</strong>

                  <small>Reports with privacy assessments</small>

                  <small>Results will appear here</small>

                </article>

              </section>

              {isLoadingDashboardReports && (

                  <p className="dashboard-report-message">

                    Loading evaluation report counts...

                  </p>

                )}

                {dashboardReportsError && (

                  <p className="dashboard-report-error" role="alert">

                    Unable to load evaluation report counts: {dashboardReportsError}

                  </p>

                )}

              <section className="workspace-grid">

                <article className="panel quick-start">

                  <div className="panel-heading">

                    <div>

                      <p className="eyebrow">GET STARTED</p>

                      <h2>Create synthetic data</h2>

                    </div>

                    <span className="step-count">01 / 03</span>

                  </div>

                  <p className="panel-description">

                    Start with a CSV schema or dataset. Choose how many

                    synthetic records you need.

                  </p>

                  <div className="workflow-steps">

                    <div><span>1</span><p><strong>Upload</strong><small>Choose a CSV file</small></p></div>

                    <div><span>2</span><p><strong>Generate</strong><small>Configure row count</small></p></div>

                    <div><span>3</span><p><strong>Evaluate</strong><small>Review quality and privacy</small></p></div>

                  </div>

                  <button className="secondary-button" onClick={startNewDataset}>

                    Start a new dataset <span aria-hidden="true">→</span>

                  </button>

                </article>

                <article className="panel system-panel">

                  <p className="eyebrow">PLATFORM STATUS</p>

                  <h2>Development environment</h2>

                  <div className="system-row">

                    <span>Frontend</span><span className="state-ready">● Running</span>

                  </div>

                  <div className="system-row">

                    <span>Generation API</span>

                    <span

                      className={

                        apiStatus === 'ready'

                          ? 'state-ready'

                          : 'state-pending'

                      }

                      role="status"

                    >

                      {apiStatus === 'checking'

                        ? '◌ Checking...'

                        : apiStatus === 'ready'

                          ? '● Connected'

                          : '◌ Unavailable'}

                    </span>

                  </div>

                  <div className="system-row">

                    <span>Evaluation results</span><span className="state-connected">● Available</span>

                  </div>

                  <p className="panel-note">

                    Generation API status is checked against the running backend.

                  </p>

                </article>

              </section>

            </>

          )}

          {page === 'Generate Data' && (

            <section className="form-page">

              <p className="eyebrow">SYNTHETIC DATA WORKFLOW</p>

              <h1>Generate synthetic data</h1>

              <p className="subtitle">

                Upload a CSV, choose the number of synthetic rows, and track the job as it runs.

              </p>

              <div className="generation-workspace">

                <div className="panel upload-panel">

                <div className="panel-heading">

                  <div>

                    <h2>Source dataset</h2>

                    <p className="panel-description">

                      Select the CSV schema or dataset to use as a starting point.

                    </p>

                  </div>

                  <span className="required-label">CSV ONLY</span>

                </div>

                <button

                  className="drop-zone"

                  onClick={() => fileInputRef.current?.click()}

                  onDragOver={(event) => event.preventDefault()}

                  onDrop={(event) => {

                    event.preventDefault()

                    selectFile(event.dataTransfer.files[0])

                  }}

                >

                  <span className="upload-icon">↑</span>

                  <strong>Choose a CSV file</strong>

                  <span>Click to browse or drag and drop</span>

                  <small>CSV files only</small>

                </button>

                <input

                  ref={fileInputRef}

                  className="visually-hidden"

                  type="file"

                  accept=".csv,text/csv"

                  onChange={(event) => selectFile(event.target.files?.[0])}

                />

                {file && (

                  <div className="selected-file">

                    <span className="file-icon">CSV</span>

                    <span className="file-details">

                      <strong>{file.name}</strong>

                      <small>{(file.size / 1024).toFixed(1)} KB</small>

                    </span>

                    <button

                      className="remove-file"

                      aria-label="Remove selected file"

                      onClick={() => {

                        setFile(null)

                        setMessage('')

                        setCreatedJob(null)

                        setCreatedJobDetails(null)

                        if (fileInputRef.current) fileInputRef.current.value = ''

                      }}

                    >

                      Remove

                    </button>

                  </div>

                )}

                <div className="field-group">

                  <label htmlFor="row-count">Number of synthetic rows</label>

                  <input

                    id="row-count"

                    type="number"

                    min="1"

                    step="1"

                    value={rowCount}

                    onChange={(event) => {

                      setRowCount(event.target.value)

                      setMessage('')

                    }}

                  />

                  <small>Enter a positive whole number.</small>

                </div>

                {message && (

                  <div className="feedback-message" role="status">

                    {message}

                  </div>

                )}

                <button

                  className="primary-button full-width"

                  onClick={submitJob}

                  disabled={isSubmitting}

                >

                  {isSubmitting ? 'Submitting job...' : 'Generate synthetic data'}

                  {!isSubmitting && <span aria-hidden="true"> →</span>}

                </button>

                <p className="privacy-note">

                  Your CSV will be uploaded to the backend for synthetic data generation.

                </p>

                </div>

                {createdJob && (

                  <div className="status-card generated-job-card">

                  <h3>Job submitted successfully</h3>

                <p className="job-id-row">

                  <strong>Job ID:</strong>

                  <span className="job-id-value">{createdJob.job_id}</span>

                </p>

                  <p>

                    <strong>Source file:</strong>{' '}

                    {createdJobDetails?.input_file

                      ? createdJobDetails.input_file.split(/[\\\\/]/).pop()

                      : file?.name ?? 'Uploaded dataset'}

                  </p>

                  <p>

                    <strong>Requested rows:</strong>{' '}

                    {createdJobDetails?.row_count ?? Number(rowCount)}

                  </p>

                  <p>

                    <strong>Status:</strong>{' '}

                    {createdJobDetails?.status ?? createdJob.status}

                  </p>

                  {createdJobDetails?.progress != null && (

                    <p>

                      <strong>Progress:</strong> {createdJobDetails.progress}%

                    </p>

                  )}

                  {createdJobDetails?.error_message && (

                    <p role="alert">

                      <strong>Error:</strong> {createdJobDetails.error_message}

                    </p>

                  )}

                  <div className="job-card-actions">

                    <button

                      type="button"

                      className="job-action-button"

                      onClick={() => setPage('Jobs & Results')}

                    >

                      View Jobs &amp; Results

                    </button>

                    <button

                      type="button"

                      className="job-action-button"

                      onClick={startNewDataset}

                    >

                      Generate Another Dataset

                    </button>

                  </div>

                  </div>

                )}

              </div>

            </section>

          )}

          {page === 'Jobs & Results' && (

            <section className="form-page">

              <p className="eyebrow">EXECUTION HISTORY</p>

              <h1>Jobs &amp; results</h1>

              <p className="subtitle">

                Track generation progress and retrieve evaluation reports.

              </p>

              {createdJob && (

                <div className="status-card">

                  <h3>Latest submitted job</h3>

                  <p>

                    <strong>Job ID:</strong> {createdJob.job_id}

                  </p>

                  <p>

                    <strong>Status:</strong> {createdJob.status}

                  </p>

                </div>

              )}

              {isLoadingJobs ? (

                <div className="panel empty-state" role="status">

                  <h2>Loading job history...</h2>

                  <p>Please wait while we retrieve your saved jobs.</p>

                </div>

              ) : jobsError ? (

                <div className="panel empty-state" role="alert">

                  <h2>Unable to load jobs</h2>

                  <p>{jobsError}</p>

                  <button className="secondary-button" onClick={() => void loadJobs()}>

                    Try again

                  </button>

                </div>

              ) : jobs.length === 0 ? (

                <div className="panel empty-state">

                  <span className="empty-state-icon">◇</span>

                  <h2>No jobs yet</h2>

                  <p>

                    Submitted generation jobs will appear here once they are saved

                    by the backend.

                  </p>

                  <button

                    className="secondary-button"

                    onClick={startNewDataset}

                  >

                    Prepare a dataset <span aria-hidden="true">→</span>

                  </button>

                </div>

              ) : (

                <div className="jobs-list">

                  {jobs.map((job) => (

                    <article className="panel job-card" key={job.job_id}>

                      <div className="panel-heading">

                        <div>

                          <h2>

                            {job.input_file

                              ? job.input_file.split(/[\\\\/]/).pop() || 'Unnamed dataset'

                              : 'Unnamed dataset'}

                          </h2>

                          <p className="panel-description">

                            Job ID: {job.job_id}

                          </p>

                        </div>

                        <span className={`job-status status-${job.status.toLowerCase()}`}>

                          {job.status}

                        </span>

                      </div>

                      <div className="job-details">

                        <p><strong>Requested rows:</strong> {job.row_count.toLocaleString()}</p>

                        <p>

                          <strong>Created:</strong>{' '}

                          {new Date(job.created_at).toLocaleString()}

                        </p>

                        {job.error_message && (

                          <p role="alert">

                            <strong>Error:</strong> {job.error_message}

                          </p>

                        )}

                      </div>

                          {['completed', 'succeeded'].includes(job.status.toLowerCase()) && (

                            <div className="job-results-actions">

                              <button

                                type="button"

                                onClick={() => {

                                  if (expandedJobId === job.job_id) {

                                    setExpandedJobId(null)

                                  } else if (reportByJobId[job.job_id]) {

                                    setExpandedJobId(job.job_id)

                                  } else {

                                    void loadJobReport(job.job_id)

                                  }

                                }}

                                disabled={reportLoadingByJobId[job.job_id] === true}

                              >

                                {reportLoadingByJobId[job.job_id]

                                  ? 'Loading results...'

                                  : expandedJobId === job.job_id

                                    ? 'Hide results'

                                    : 'View results'}

                              </button>

                              {reportErrorsByJobId[job.job_id] && (

                                <p role="alert">{reportErrorsByJobId[job.job_id]}</p>

                              )}

                            </div>

                          )}

                          {expandedJobId === job.job_id && reportByJobId[job.job_id] && (

                            <div className="job-results">

                              <div className="job-results-header">

                                <div>

                                  <h3>Generation results</h3>

                                  <p>Evaluation report · Completed job</p>

                                </div>

                                <span className="result-status result-status-success">

                                  Succeeded

                                </span>

                              </div>

                              <div className="result-metrics-grid">

                                <div className="result-metric">

                                  <span className="result-metric-label">Generated rows</span>

                                  <strong>

                                    {reportByJobId[job.job_id].synthetic_data.row_count.toLocaleString()}

                                  </strong>

                                </div>

                                <div className="result-metric">

                                  <span className="result-metric-label">Columns</span>

                                  <strong>

                                    {reportByJobId[job.job_id].synthetic_data.column_count}

                                  </strong>

                                </div>

                                <div className="result-metric">

                                  <span className="result-metric-label">Schema validation</span>

                                  <strong

                                    className={

                                      reportByJobId[job.job_id].schema_validation.valid

                                        ? 'result-value-success'

                                        : 'result-value-error'

                                    }

                                  >

                                    {reportByJobId[job.job_id].schema_validation.valid

                                      ? '✓ Passed'

                                      : '✕ Failed'}

                                  </strong>

                                </div>

                                <div className="result-metric">

                                  <span className="result-metric-label">Privacy status</span>

                                  <strong

                                    className={

                                      reportByJobId[job.job_id].privacy.status.toUpperCase() === '✓ Passed'

                                        ? '✓ Passed'

                                        : 'result-value-error'

                                    }

                                  >

                                    {reportByJobId[job.job_id].privacy.status}

                                  </strong>

                                </div>

                              </div>

                              <div className="result-secondary-metrics">

                                <div>

                                  <span className="result-metric-label">Exact matches</span>

                                  <strong>

                                    {reportByJobId[job.job_id].privacy.total_exact_matches.toLocaleString()}

                                  </strong>

                                </div>

                                <div>

                                  <span className="result-metric-label">Duplicate rows</span>

                                  <strong>

                                    {reportByJobId[job.job_id].privacy.duplicate_row_count.toLocaleString()}

                                  </strong>

                                </div>

                              </div>

                                <div className="result-download-actions">

                                  <button

                                    type="button"

                                    className="result-download-button result-download-primary"

                                    onClick={() =>

                                      void handleArtifactDownload(job.job_id, 'synthetic_data.csv')

                                    }

                                  >

                                    <span aria-hidden="true">⇩</span>

                                    Download CSV

                                  </button>

                                  <button

                                    type="button"

                                    className="result-download-button result-download-secondary"

                                    onClick={() =>

                                      void handleArtifactDownload(job.job_id, 'report.json')

                                    }

                                  >

                                    <span aria-hidden="true">{ }</span>

                                    Download report JSON

                                  </button>

                                </div>

                            </div>

                          )}

                    </article>

                  ))}

                </div>

              )}

            </section>

          )}

          <footer className="page-footer">

            <span>Synthetica · Synthetic Data Engineering &amp; Privacy Platform</span>

            <span>V0.4 · Development</span>

          </footer>

        </div>

      </main>

    </div>

  )

}

export default App

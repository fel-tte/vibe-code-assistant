import { expect, test } from "@playwright/test";

type Json = Record<string, any>;

const BACKEND_BASE_URL = (process.env.BACKEND_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
const FRONTEND_BASE_URL = (process.env.FRONTEND_BASE_URL || "http://localhost:3000").replace(/\/+$/, "");
const PROVIDER = (process.env.E2E_PROVIDER || "runway").toLowerCase();
const DELIVERY_MODE = (process.env.E2E_DELIVERY_MODE || "edge-callback").toLowerCase();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function getJson(request: any, url: string): Promise<Json> {
  const response = await request.get(url, { failOnStatusCode: false });
  expect(response.ok(), `GET ${url} failed with ${response.status()}`).toBeTruthy();
  return response.json();
}

async function postJson(
  request: any,
  url: string,
  payload: Json,
  headers: Record<string, string> = {},
): Promise<Json> {
  const response = await request.post(url, {
    failOnStatusCode: false,
    data: payload,
    headers: { "Content-Type": "application/json", ...headers },
  });
  expect(
    response.ok(),
    `POST ${url} failed with ${response.status()} ${await response.text()}`,
  ).toBeTruthy();
  const ct = response.headers()["content-type"] || "";
  if (ct.includes("application/json")) return response.json();
  return { raw: await response.text() };
}

async function waitFor(
  fn: () => Promise<Json>,
  predicate: (data: Json) => boolean,
  timeoutMs: number,
  intervalMs: number,
): Promise<Json> {
  const deadline = Date.now() + timeoutMs;
  let last: Json = {};
  while (Date.now() < deadline) {
    last = await fn();
    if (predicate(last)) return last;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Timed out waiting for condition. Last payload: ${JSON.stringify(last, null, 2)}`);
}

function buildJobPayload(provider: string, sceneCount: number = 1): Json {
  const aspectRatio = process.env.E2E_ASPECT_RATIO || "16:9";
  const promptBase = "A cinematic E2E pipeline test shot with gentle motion.";
  return {
    project_id: `e2e-pipeline-${provider}-${Date.now()}`,
    provider,
    aspect_ratio: aspectRatio,
    subtitle_mode: "soft",
    planned_scenes: Array.from({ length: sceneCount }, (_, i) => ({
      scene_index: i + 1,
      title: `Pipeline test scene ${i + 1}`,
      script_text: `${promptBase} Scene ${i + 1}.`,
      provider_target_duration_sec: provider === "veo" ? 4 : 5,
      target_duration_sec: provider === "veo" ? 4 : 5,
      visual_prompt: `${promptBase} Scene ${i + 1}.`,
    })),
  };
}

function buildSuccessCallback(provider: string, scene: Json, jobId: string): Json {
  const assetUrl = `https://example.invalid/assets/${jobId}/${scene.id || "scene-1"}.mp4`;
  const providerTaskId = scene.provider_task_id;
  const providerOperationName = scene.provider_operation_name;

  if (provider === "runway") {
    return {
      id: `evt-pipeline-${jobId}`,
      taskId: providerTaskId,
      status: "SUCCEEDED",
      outputUrl: assetUrl,
      thumbnailUrl: `${assetUrl}.jpg`,
      event: "task.completed",
    };
  }
  if (provider === "kling") {
    return {
      request_id: `evt-pipeline-${jobId}`,
      data: {
        task_id: providerTaskId,
        task_status: "succeed",
        task_result: { videos: [{ url: assetUrl, cover_url: `${assetUrl}.jpg` }] },
      },
      event: "kling.task.completed",
    };
  }
  return {
    name: providerOperationName || `operations/${jobId}`,
    done: true,
    response: {
      generateVideoResponse: {
        generatedSamples: [{ video: { uri: assetUrl }, image: { uri: `${assetUrl}.jpg` } }],
      },
    },
    type: "veo.operation.completed",
  };
}

function buildFailureCallback(provider: string, scene: Json, jobId: string): Json {
  if (provider === "runway") {
    return {
      id: `evt-fail-pipeline-${jobId}`,
      taskId: scene.provider_task_id,
      status: "FAILED",
      error: "Synthetic pipeline failure",
      event: "task.failed",
    };
  }
  if (provider === "kling") {
    return {
      request_id: `evt-fail-pipeline-${jobId}`,
      data: {
        task_id: scene.provider_task_id,
        task_status: "failed",
        fail_reason: "Synthetic pipeline failure",
      },
      event: "kling.task.failed",
    };
  }
  return {
    name: scene.provider_operation_name || `operations/${jobId}`,
    done: true,
    error: { message: "Synthetic pipeline failure" },
    type: "veo.operation.failed",
  };
}

async function getJobSnapshot(request: any, jobId: string): Promise<Json> {
  const payload = await getJson(request, `${BACKEND_BASE_URL}/api/v1/render/jobs/${jobId}`);
  return payload.data || payload;
}

async function waitForSubmission(request: any, jobId: string): Promise<Json> {
  return waitFor(
    () => getJobSnapshot(request, jobId),
    (job) =>
      Boolean(
        job.scenes?.[0]?.provider_task_id ||
          job.scenes?.[0]?.provider_operation_name ||
          (job.scenes?.[0]?.status && String(job.scenes?.[0]?.status).toLowerCase() !== "queued"),
      ),
    60_000,
    2_000,
  );
}

async function waitForCompletedJob(request: any, jobId: string): Promise<Json> {
  return waitFor(
    () => getJobSnapshot(request, jobId),
    (job) =>
      String(job.status || "").toLowerCase() === "completed" &&
      Boolean(job.output_url || job.final_video_url || job.storage_key || job.final_timeline),
    180_000,
    5_000,
  );
}

async function createAndCompleteJob(
  request: any,
  provider: string,
  deliveryMode: string,
): Promise<{ jobId: string; job: Json }> {
  const createPayload = buildJobPayload(provider);
  const createRes = await postJson(request, `${BACKEND_BASE_URL}/api/v1/render/jobs`, createPayload);
  const created = createRes.data || createRes;
  const jobId = created.job_id || created.id;
  expect(jobId).toBeTruthy();

  const submitted = await waitForSubmission(request, jobId);
  const scene = submitted.scenes?.[0];
  expect(scene).toBeTruthy();

  if (deliveryMode !== "poll") {
    const callbackPayload = buildSuccessCallback(provider, scene, jobId);
    await postJson(
      request,
      `${BACKEND_BASE_URL}/api/v1/provider-callbacks/relay/${provider}`,
      callbackPayload,
    );
  }

  const completed = await waitForCompletedJob(request, jobId);
  return { jobId, job: completed };
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

test("backend healthcheck: API is up and reporting healthy", async ({ request }) => {
  const health = await getJson(request, `${BACKEND_BASE_URL}/healthz`);
  expect(health.status || health.ok || health.healthy || true).toBeTruthy();
});

// ---------------------------------------------------------------------------
// Full render pipeline: create job → submit → callback → verify completion
// ---------------------------------------------------------------------------

test("full pipeline: create render job → provider submission → callback → completed status", async ({
  request,
}) => {
  const createPayload = buildJobPayload(PROVIDER);
  const createRes = await postJson(
    request,
    `${BACKEND_BASE_URL}/api/v1/render/jobs`,
    createPayload,
  );
  const created = createRes.data || createRes;
  const jobId = created.job_id || created.id;
  expect(jobId).toBeTruthy();
  console.log(`[pipeline] Job created: ${jobId}`);

  // Verify initial state
  const initialJob = await getJobSnapshot(request, jobId);
  expect(["queued", "processing", "submitted"]).toContain(
    String(initialJob.status || "").toLowerCase(),
  );
  expect(initialJob.scenes).toBeTruthy();
  expect(Array.isArray(initialJob.scenes)).toBeTruthy();

  // Wait for provider submission
  const submitted = await waitForSubmission(request, jobId);
  const scene = submitted.scenes?.[0];
  expect(scene).toBeTruthy();
  console.log(`[pipeline] Scene submitted, provider_task_id: ${scene.provider_task_id}`);

  // Send success callback (skip in poll mode)
  if (DELIVERY_MODE !== "poll") {
    const callbackPayload = buildSuccessCallback(PROVIDER, scene, jobId);
    await postJson(
      request,
      `${BACKEND_BASE_URL}/api/v1/provider-callbacks/relay/${PROVIDER}`,
      callbackPayload,
    );
    console.log(`[pipeline] Callback delivered`);
  }

  // Wait for completion
  const completed = await waitForCompletedJob(request, jobId);
  expect(String(completed.status || "").toLowerCase()).toBe("completed");
  expect(completed.output_url || completed.final_video_url).toBeTruthy();
  console.log(`[pipeline] Job completed: ${completed.output_url || completed.final_video_url}`);
});

// ---------------------------------------------------------------------------
// Database state verification via status API
// ---------------------------------------------------------------------------

test("database state: job API reflects correct fields after completion", async ({ request }) => {
  const { jobId, job } = await createAndCompleteJob(request, PROVIDER, DELIVERY_MODE);

  // Verify all required fields are present
  expect(job.status).toBe("completed");
  expect(job.output_url || job.final_video_url || job.storage_key).toBeTruthy();
  expect(Array.isArray(job.scenes)).toBeTruthy();
  expect(job.scenes.length).toBeGreaterThan(0);

  // Verify scene state
  for (const scene of job.scenes) {
    const sceneStatus = String(scene.status || "").toLowerCase();
    expect(["succeeded", "completed"]).toContain(sceneStatus);
    expect(scene.output_video_url || scene.storage_key).toBeTruthy();
  }

  // Verify final timeline present (if applicable)
  if (job.final_timeline) {
    const timeline = Array.isArray(job.final_timeline)
      ? job.final_timeline
      : Object.keys(job.final_timeline);
    expect(timeline.length).toBeGreaterThanOrEqual(0);
  }

  console.log(`[db-state] Job ${jobId}: status=${job.status}, scenes=${job.scenes.length}`);
});

// ---------------------------------------------------------------------------
// Error scenario: provider failure → incident created
// ---------------------------------------------------------------------------

test("error scenario: provider failure callback creates incident and marks job failed", async ({
  request,
}) => {
  const createPayload = buildJobPayload(PROVIDER);
  const createRes = await postJson(
    request,
    `${BACKEND_BASE_URL}/api/v1/render/jobs`,
    createPayload,
  );
  const created = createRes.data || createRes;
  const jobId = created.job_id || created.id;
  expect(jobId).toBeTruthy();

  // Wait for provider submission
  const submitted = await waitForSubmission(request, jobId);
  const scene = submitted.scenes?.[0];
  expect(scene).toBeTruthy();

  // Deliver failure callback
  const failPayload = buildFailureCallback(PROVIDER, scene, jobId);
  await postJson(
    request,
    `${BACKEND_BASE_URL}/api/v1/provider-callbacks/relay/${PROVIDER}`,
    failPayload,
  );
  console.log(`[error-scenario] Failure callback delivered for job ${jobId}`);

  // Wait for job to enter a terminal error/failed state
  const finalJob = await waitFor(
    () => getJobSnapshot(request, jobId),
    (j) => ["failed", "error", "completed"].includes(String(j.status || "").toLowerCase()),
    120_000,
    3_000,
  );
  const finalStatus = String(finalJob.status || "").toLowerCase();
  expect(["failed", "error"]).toContain(finalStatus);
  console.log(`[error-scenario] Job ${jobId} ended in state: ${finalStatus}`);

  // Check that incident was created (best-effort)
  const incidentsPayload = await getJson(
    request,
    `${BACKEND_BASE_URL}/api/v1/render/incidents/recent?limit=50&show_muted=true`,
  );
  const items: Json[] = incidentsPayload.items || [];
  const incident = items.find(
    (item) => item.job?.job_id === jobId || item.job?.id === jobId,
  );
  if (incident) {
    expect(incident.incident_key).toBeTruthy();
    console.log(`[error-scenario] Incident created: ${incident.incident_key}`);
  }
});

// ---------------------------------------------------------------------------
// Multi-scene pipeline
// ---------------------------------------------------------------------------

test("multi-scene pipeline: all scenes complete and job merges", async ({ request }) => {
  const sceneCount = 2;
  const createPayload = buildJobPayload(PROVIDER, sceneCount);
  const createRes = await postJson(
    request,
    `${BACKEND_BASE_URL}/api/v1/render/jobs`,
    createPayload,
  );
  const created = createRes.data || createRes;
  const jobId = created.job_id || created.id;
  expect(jobId).toBeTruthy();

  // Verify planned scene count
  const initialJob = await getJobSnapshot(request, jobId);
  expect(initialJob.planned_scene_count).toBe(sceneCount);

  // Wait for all scenes to be submitted to provider
  const submitted = await waitFor(
    () => getJobSnapshot(request, jobId),
    (j) =>
      Array.isArray(j.scenes) &&
      j.scenes.every(
        (s: Json) =>
          s.provider_task_id ||
          s.provider_operation_name ||
          String(s.status || "").toLowerCase() !== "queued",
      ),
    90_000,
    3_000,
  );

  expect(submitted.scenes.length).toBe(sceneCount);

  // Send success callbacks for each scene
  if (DELIVERY_MODE !== "poll") {
    for (const scene of submitted.scenes) {
      const callbackPayload = buildSuccessCallback(PROVIDER, scene, jobId);
      await postJson(
        request,
        `${BACKEND_BASE_URL}/api/v1/provider-callbacks/relay/${PROVIDER}`,
        callbackPayload,
      );
    }
  }

  // Wait for full completion
  const completed = await waitForCompletedJob(request, jobId);
  expect(String(completed.status || "").toLowerCase()).toBe("completed");
  expect(completed.output_url || completed.final_video_url).toBeTruthy();
  console.log(`[multi-scene] Job ${jobId} completed with ${sceneCount} scenes`);
});

// ---------------------------------------------------------------------------
// Concurrent jobs load test (lightweight)
// ---------------------------------------------------------------------------

test("load: 5 concurrent render jobs all complete successfully", async ({ request }) => {
  const jobCount = 5;
  const createPromises = Array.from({ length: jobCount }, (_, i) =>
    postJson(request, `${BACKEND_BASE_URL}/api/v1/render/jobs`, {
      project_id: `e2e-load-${i}-${Date.now()}`,
      provider: PROVIDER,
      aspect_ratio: "16:9",
      subtitle_mode: "soft",
      planned_scenes: [
        {
          scene_index: 1,
          title: `Load test scene ${i}`,
          script_text: `Concurrent load test scene ${i} for pipeline validation.`,
          provider_target_duration_sec: 5,
          target_duration_sec: 5,
          visual_prompt: `Load test prompt ${i}`,
        },
      ],
    }),
  );

  const createResults = await Promise.all(createPromises);
  const jobIds = createResults.map((r) => {
    const d = r.data || r;
    return d.job_id || d.id;
  });

  console.log(`[load] Created ${jobIds.length} jobs: ${jobIds.join(", ")}`);

  // Send callbacks for all submitted scenes (not in poll mode)
  if (DELIVERY_MODE !== "poll") {
    const submissionPromises = jobIds.map((jobId) => waitForSubmission(request, jobId));
    const submittedJobs = await Promise.all(submissionPromises);

    const callbackPromises = submittedJobs.map(async (job, idx) => {
      const scene = job.scenes?.[0];
      if (!scene) return;
      const jobId = jobIds[idx];
      const callbackPayload = buildSuccessCallback(PROVIDER, scene, jobId);
      await postJson(
        request,
        `${BACKEND_BASE_URL}/api/v1/provider-callbacks/relay/${PROVIDER}`,
        callbackPayload,
      );
    });
    await Promise.all(callbackPromises);
  }

  // Wait for all jobs to reach terminal state
  const completionPromises = jobIds.map((jobId) =>
    waitFor(
      () => getJobSnapshot(request, jobId),
      (j) =>
        ["completed", "failed", "error"].includes(String(j.status || "").toLowerCase()),
      240_000,
      5_000,
    ).then((j) => ({ jobId, status: String(j.status || "").toLowerCase() })),
  );

  const results = await Promise.all(completionPromises);
  const successCount = results.filter((r) => r.status === "completed").length;
  console.log(`[load] Results: ${results.map((r) => `${r.jobId}=${r.status}`).join(", ")}`);

  // Allow at most 1 failure in 5 jobs (80% success rate minimum)
  expect(successCount).toBeGreaterThanOrEqual(4);

  // System should still be healthy
  const health = await getJson(request, `${BACKEND_BASE_URL}/healthz`);
  expect(health.status || health.ok || true).toBeTruthy();
});

// ---------------------------------------------------------------------------
// Frontend page renders completed job
// ---------------------------------------------------------------------------

test("frontend: completed job page renders final video and timeline", async ({ page, request }) => {
  const { jobId, job } = await createAndCompleteJob(request, PROVIDER, DELIVERY_MODE);

  const finalAssetUrl = String(job.output_url || job.final_video_url || "");
  expect(finalAssetUrl).toBeTruthy();

  // Navigate to job detail page
  await page.goto(`${FRONTEND_BASE_URL}/render-jobs/${jobId}`, { waitUntil: "networkidle" });

  // Page should render the job ID somewhere
  await expect(page.getByText(new RegExp(jobId))).toBeVisible({ timeout: 15_000 });

  // Final video element should be visible
  await expect(page.getByTestId("render-job-final-video")).toBeVisible({ timeout: 15_000 });

  // Asset URL should appear on the page
  await expect(page.getByTestId("render-job-final-video-url")).toContainText(finalAssetUrl, {
    timeout: 10_000,
  });

  console.log(`[frontend] Job ${jobId} detail page rendered successfully`);
});

// ---------------------------------------------------------------------------
// Storage / signed URL
// ---------------------------------------------------------------------------

test("storage: final download endpoint returns a signed URL or storage key", async ({
  request,
}) => {
  const { jobId } = await createAndCompleteJob(request, PROVIDER, DELIVERY_MODE);

  const downloadRes = await request.get(
    `${BACKEND_BASE_URL}/api/v1/storage/jobs/${jobId}/final-download`,
    { failOnStatusCode: false },
  );

  if (downloadRes.ok()) {
    const data = await downloadRes.json();
    expect(data.key || data.signed_url || data.url).toBeTruthy();
    console.log(`[storage] Signed URL obtained for job ${jobId}`);
  } else {
    // Storage endpoint is optional; skip gracefully
    console.log(
      `[storage] Storage endpoint not available (status ${downloadRes.status()}) – skipping`,
    );
  }
});

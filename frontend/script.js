const apiBaseUrlInput = document.getElementById("apiBaseUrl");

function getApiBaseUrl() {
  return apiBaseUrlInput.value.replace(/\/+$/, "");
}

// --- Tabs ---
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "history") {
      loadHistory();
    }
  });
});

function setStatus(el, message, type) {
  el.textContent = message;
  el.className = "status" + (type ? " " + type : "");
}

// --- Single recognition ---
const singleForm = document.getElementById("singleForm");
const singleStatus = document.getElementById("singleStatus");
const singleResult = document.getElementById("singleResult");

singleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById("singleFile");
  const model = document.getElementById("singleModel").value;

  if (!fileInput.files.length) {
    setStatus(singleStatus, "Please choose a file.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("model", model);

  setStatus(singleStatus, "Processing...", "");
  singleResult.textContent = "";

  try {
    const response = await fetch(`${getApiBaseUrl()}/api/recognition`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Recognition failed.");
    }
    setStatus(singleStatus, "Done.", "success");
    singleResult.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    setStatus(singleStatus, err.message, "error");
  }
});

// --- Batch recognition ---
const batchForm = document.getElementById("batchForm");
const batchStatus = document.getElementById("batchStatus");
const batchResult = document.getElementById("batchResult");

batchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const filesInput = document.getElementById("batchFiles");
  const model = document.getElementById("batchModel").value;

  if (!filesInput.files.length) {
    setStatus(batchStatus, "Please choose at least one file.", "error");
    return;
  }

  const formData = new FormData();
  Array.from(filesInput.files).forEach((file) => formData.append("files", file));
  formData.append("model", model);

  setStatus(batchStatus, "Processing batch...", "");
  batchResult.textContent = "";

  try {
    const response = await fetch(`${getApiBaseUrl()}/api/recognition/batch`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Batch recognition failed.");
    }
    setStatus(
      batchStatus,
      `Done. Processed: ${data.processed_count}, Failed: ${data.failed_count}`,
      "success"
    );
    batchResult.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    setStatus(batchStatus, err.message, "error");
  }
});

// --- History ---
const historyStatus = document.getElementById("historyStatus");
const historyTableBody = document.querySelector("#historyTable tbody");

async function loadHistory() {
  setStatus(historyStatus, "Loading...", "");
  historyTableBody.innerHTML = "";

  try {
    const response = await fetch(`${getApiBaseUrl()}/api/history`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to load history.");
    }

    if (!data.length) {
      setStatus(historyStatus, "No recognitions yet.", "");
      return;
    }

    data.forEach((item) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${item.id}</td>
        <td>${item.filename}</td>
        <td>${(item.recognized_text || "").slice(0, 200)}</td>
        <td>${item.confidence != null ? item.confidence.toFixed(2) : ""}</td>
        <td>${item.timestamp}</td>
      `;
      historyTableBody.appendChild(row);
    });
    setStatus(historyStatus, `${data.length} record(s).`, "success");
  } catch (err) {
    setStatus(historyStatus, err.message, "error");
  }
}

document.getElementById("refreshHistory").addEventListener("click", loadHistory);

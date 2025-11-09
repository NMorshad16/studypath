async function postJSON(url, payload){
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  if(!res.ok){ throw new Error((await res.text()) || "Request failed"); }
  return res.json();
}
async function getJSON(url){
  const res = await fetch(url);
  if(!res.ok){ throw new Error("Request failed"); }
  return res.json();
}
const $ = (q)=>document.querySelector(q);

async function refreshPlan(){
  const data = await getJSON("/api/plan");
  renderPlan(data.plan || []);
  renderProgress(data.progress || {}, data.plan || []);
  if(data.profile){
    $("#subjects").value = (data.profile.subjects||[]).join(", ");
    $("#weaknesses").value = (data.profile.weaknesses||[]).join(", ");
    $("#exam_date").value = (data.profile.exam_date||"");
    $("#hours").value = data.profile.hours_per_day || 2;
  }
}

function renderPlan(plan){
  const wrap = document.getElementById("plan");
  if(!plan.length){ wrap.innerHTML = "<p class='small'>No plan generated yet.</p>"; return; }
  wrap.innerHTML = "";
  plan.forEach(day => {
    const div = document.createElement("div");
    div.className = "day";
    const title = document.createElement("div");
    title.innerHTML = `<strong>${day.date}</strong> <span class='small'>(${day.tasks.length} tasks)</span>`;
    div.appendChild(title);
    day.tasks.forEach((t, i)=>{
      const row = document.createElement("div");
      row.className = "task";
      row.innerHTML = `
        <div class="meta">
          <span class="subj">${t.subject}</span>
          <span class="small">· ${t.duration_hours}h</span>
          <span class="small">· ${t.status}</span>
        </div>
        <div>
          <button data-date="${day.date}" data-index="${i}" ${t.status==="done"?"disabled":""}>Mark done</button>
        </div>`;
      row.querySelector("button").addEventListener("click", async (e)=>{
        const date = e.target.getAttribute("data-date");
        const idx = parseInt(e.target.getAttribute("data-index"));
        await postJSON("/api/complete", {date, index: idx});
        await refreshPlan();
      });
      div.appendChild(row);
    });
    wrap.appendChild(div);
  });
}

function renderProgress(progress, plan){
  const done = progress.done || 0;
  const total = progress.total || (plan.reduce((a,d)=>a+d.tasks.length,0));
  const ctx = document.getElementById("overallChart").getContext("2d");
  if(window.__chart){ window.__chart.destroy(); }
  window.__chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Done', 'Remaining'],
      datasets: [{
        data: [done, Math.max(0, total-done)]
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

document.getElementById("btn-generate").addEventListener("click", async ()=>{
  const subjects = $("#subjects").value.split(",").map(s=>s.trim()).filter(Boolean);
  const weaknesses = $("#weaknesses").value.split(",").map(s=>s.trim()).filter(Boolean);
  const exam_date = $("#exam_date").value;
  const hours_per_day = parseFloat($("#hours").value||"2");
  $("#status").textContent = "Generating...";
  try{
    await postJSON("/api/generate", {subjects, weaknesses, exam_date, hours_per_day});
    $("#status").textContent = "Plan generated ✅";
    await refreshPlan();
  }catch(e){
    $("#status").textContent = e.message;
  }
});

document.getElementById("btn-reset").addEventListener("click", async ()=>{
  await postJSON("/api/reset", {});
  await refreshPlan();
  $("#status").textContent = "All data cleared.";
});

refreshPlan();

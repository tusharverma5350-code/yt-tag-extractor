(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const LOCAL = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  const API = LOCAL ? "" : (document.querySelector('meta[name="api-base"]')?.content || "").replace(/\/$/, "");

  /* ---------- theme + mobile menu ---------- */
  const themeBtn = $("#theme");
  const setTheme = t => { document.documentElement.dataset.theme = t; localStorage.setItem("theme", t); };
  themeBtn?.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
  $("#menu")?.addEventListener("click", e => {
    const nav = $(".nav"); nav.classList.toggle("open");
    e.currentTarget.setAttribute("aria-expanded", nav.classList.contains("open"));
  });

  const tool = $("#tool");
  if (!tool) return;

  /* ---------- helpers ---------- */
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const linkify = s => esc(s).replace(/https?:\/\/[^\s<]+/g, u => `<a href="${u}" target="_blank" rel="noopener nofollow">${u}</a>`);
  const num = n => n == null ? "—" : Number(n).toLocaleString("en-US");
  const dur = s => { if (!s && s !== 0) return "—"; const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60; return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(x).padStart(2, "0"); };
  const date = d => d ? new Date(`${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}T00:00:00`).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }) : "—";
  const toastEl = $("#toast");
  let toastT;
  const toast = msg => { toastEl.textContent = msg; toastEl.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => toastEl.classList.remove("show"), 1600); };
  const copy = async (text, what) => {
    try { await navigator.clipboard.writeText(text); toast(`${what} copied`); }
    catch { const t = document.createElement("textarea"); t.value = text; document.body.append(t); t.select(); document.execCommand("copy"); t.remove(); toast(`${what} copied`); }
  };
  const saveFile = (blob, name) => { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 15000); };
  const notice = (msg, kind = "err") => { const n = $("#notice"); n.className = `notice ${kind}` + (msg ? " show" : ""); n.textContent = msg || ""; };
  const ID_RE = /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|live\/|embed\/)|youtu\.be\/)([\w-]{11})/;

  /* warm up the API (free hosting sleeps when idle) */
  fetch(API + "/api/health", { cache: "no-store" }).catch(() => {});

  /* ---------- state ---------- */
  let data = null, tags = [];
  const focus = document.body.dataset.focus || "tags";

  /* ---------- recent ---------- */
  const recentKey = "recent-videos";
  const getRecent = () => { try { return JSON.parse(localStorage.getItem(recentKey)) || []; } catch { return []; } };
  function renderRecent() {
    const r = getRecent(), box = $("#recent");
    if (!r.length) { box.hidden = true; return; }
    box.hidden = false;
    box.innerHTML = "Recent: " + r.map(v => `<button type="button" data-url="${esc(v.url)}" title="${esc(v.title)}">${esc(v.title)}</button>`).join("");
    $$("button", box).forEach(b => b.onclick = () => { $("#url").value = b.dataset.url; run(); });
  }
  function addRecent(d) {
    const r = getRecent().filter(v => v.id !== d.id);
    r.unshift({ id: d.id, url: d.url, title: d.title });
    localStorage.setItem(recentKey, JSON.stringify(r.slice(0, 5)));
    renderRecent();
  }

  /* ---------- fetch ---------- */
  const form = $("#form"), go = $("#go"), input = $("#url");
  async function run() {
    const url = input.value.trim();
    if (!ID_RE.test(url)) { notice("Please paste a valid YouTube video or Shorts link, like https://www.youtube.com/watch?v=dQw4w9WgXcQ"); input.focus(); return; }
    notice(""); go.disabled = true; go.innerHTML = '<span class="spin"></span> Extracting';
    $("#results").hidden = true; $("#skeleton").classList.add("show");
    const slow = setTimeout(() => notice("Waking up the server… the first request can take up to a minute on free hosting.", "info"), 5000);
    try {
      const r = await fetch(API + "/api/info", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.detail || "Something went wrong. Please try again.");
      data = j; tags = [...j.tags];
      notice(""); render(); addRecent(j);
      history.replaceState(null, "", "?v=" + j.id);
    } catch (e) {
      notice(e.message === "Failed to fetch" ? "Can't reach the server. Check your connection and try again." : e.message);
    } finally {
      clearTimeout(slow); $("#skeleton").classList.remove("show");
      go.disabled = false; go.textContent = go.dataset.label;
    }
  }
  form.addEventListener("submit", e => { e.preventDefault(); run(); });
  $("#paste")?.addEventListener("click", async () => {
    try { input.value = (await navigator.clipboard.readText()).trim(); if (ID_RE.test(input.value)) run(); else input.focus(); }
    catch { input.focus(); toast("Press Ctrl+V to paste"); }
  });
  input.addEventListener("paste", () => setTimeout(() => { if (ID_RE.test(input.value)) run(); }, 0));
  $$("[data-example]").forEach(b => b.onclick = () => { input.value = b.dataset.example; run(); });

  /* ---------- render ---------- */
  function tagLen() { return tags.join(",").length; }
  function renderTags() {
    const box = $("#tags");
    box.innerHTML = tags.length
      ? tags.map((t, i) => `<span class="chip" data-i="${i}" title="Click to copy">${esc(t)}<button class="x" aria-label="Remove ${esc(t)}" data-rm="${i}">×</button></span>`).join("")
      : `<p class="empty">This video has no tags. Many creators leave them empty, because YouTube says tags play a minimal role in discovery. Check the hashtags and description tabs instead.</p>`;
    const len = tagLen();
    $("#tagstat").innerHTML = `<b>${tags.length}</b> tags · <b class="${len > 500 ? "over" : ""}">${len}</b>/500 characters`;
    $("#n-tags").textContent = tags.length;
    $$(".chip", box).forEach(c => c.addEventListener("click", e => {
      if (e.target.dataset.rm) { tags.splice(+e.target.dataset.rm, 1); renderTags(); return; }
      copy(tags[+c.dataset.i], "Tag");
    }));
  }

  function render() {
    const d = data;
    $("#v-thumb").src = d.thumbnail; $("#v-thumb").alt = `Thumbnail of ${d.title}`;
    $("#v-title").textContent = d.title;
    $("#v-meta").innerHTML = `<a href="${esc(d.channel_url)}" target="_blank" rel="noopener nofollow">${esc(d.channel)}</a>${d.is_short ? '<span class="badge">SHORT</span>' : ""}<br>${num(d.view_count)} views · ${date(d.upload_date)} · ${dur(d.duration)}<br><a href="${esc(d.url)}" target="_blank" rel="noopener nofollow">Watch on YouTube ↗</a>`;

    renderTags();

    $("#hashtags").innerHTML = d.hashtags.length
      ? d.hashtags.map(h => `<span class="chip hash" title="Click to copy">#${esc(h)}</span>`).join("")
      : `<p class="empty">No hashtags found in the title or description.</p>`;
    $("#n-hash").textContent = d.hashtags.length;
    $$("#hashtags .chip").forEach(c => c.onclick = () => copy(c.textContent, "Hashtag"));

    $("#desc").innerHTML = d.description ? linkify(d.description) : `<span class="empty">This video has no description.</span>`;
    $("#descstat").innerHTML = `<b>${num(d.description.length)}</b>/5,000 characters · <b>${d.description ? d.description.trim().split(/\s+/).length : 0}</b> words`;
    $("#links").innerHTML = d.links_in_description.length
      ? `<li><b>Links in description (${d.links_in_description.length})</b></li>` + d.links_in_description.map(u => `<li><a href="${esc(u)}" target="_blank" rel="noopener nofollow">${esc(u)}</a></li>`).join("")
      : "";

    $("#thumbs").innerHTML = d.thumbnails.map(t => `<div class="thumb"><img loading="lazy" src="${esc(t.url)}" alt="${esc(t.key)} thumbnail" onerror="this.closest('.thumb').remove()"><div><span><b>${esc(t.key.toUpperCase())}</b> ${esc(t.label)}</span><button class="btn sm ghost" data-thumb="${esc(t.key)}">Download</button></div></div>`).join("");
    $$("[data-thumb]").forEach(b => b.onclick = () => downloadThumb(b));

    const label = q => q === "mp3" ? "MP3 audio" : q === "best" ? "Best (HD+)" : `${q}p MP4`;
    $("#dl").innerHTML = d.qualities.map(q => `<button class="btn ${q === "mp3" ? "outline" : ""}" data-q="${q}">${label(q)}</button>`).join("");
    $$("#dl [data-q]").forEach(b => b.onclick = () => downloadVideo(b));
    $("#dlnote").textContent = `Videos up to ${d.max_duration_min} minutes. Large files take a minute to prepare. Only download videos you own or have permission to use.`;
    $("#dlerr").className = "notice err"; $("#dlerr").textContent = "";

    $("#details").innerHTML = [
      ["Channel", esc(d.channel)], ["Views", num(d.view_count)], ["Likes", num(d.like_count)], ["Comments", num(d.comment_count)],
      ["Published", date(d.upload_date)], ["Duration", dur(d.duration)], ["Category", esc(d.categories.join(", ") || "—")],
      ["Video ID", `<code>${esc(d.id)}</code>`], ["Max quality", d.max_height ? d.max_height + "p" : "—"], ["Type", d.is_short ? "Short" : "Video"],
    ].map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("");

    $("#results").hidden = false;
    selectTab(focus);
    $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------- tabs ---------- */
  function selectTab(name) {
    $$(".tab").forEach(t => { const on = t.dataset.tab === name; t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1; });
    $$(".pane").forEach(p => p.hidden = p.id !== "pane-" + name);
  }
  $$(".tab").forEach(t => t.addEventListener("click", () => selectTab(t.dataset.tab)));
  $(".tabs").addEventListener("keydown", e => {
    if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    const tabs = $$(".tab"), i = tabs.findIndex(t => t.getAttribute("aria-selected") === "true");
    const n = tabs[(i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length];
    selectTab(n.dataset.tab); n.focus();
  });

  /* ---------- actions ---------- */
  $("#copy-tags").onclick = () => tags.length ? copy(tags.join(", "), `${tags.length} tags`) : toast("No tags to copy");
  $("#copy-tags-hash").onclick = () => tags.length ? copy(tags.map(t => "#" + t.replace(/\s+/g, "")).join(" "), "Tags as hashtags") : toast("No tags to copy");
  $("#txt-tags").onclick = () => saveFile(new Blob([tags.join(", ")], { type: "text/plain" }), `${data.id}-tags.txt`);
  $("#reset-tags").onclick = () => { tags = [...data.tags]; renderTags(); toast("Tags restored"); };
  $("#copy-hash").onclick = () => data.hashtags.length ? copy(data.hashtags.map(h => "#" + h).join(" "), "Hashtags") : toast("No hashtags to copy");
  $("#copy-desc").onclick = () => data.description ? copy(data.description, "Description") : toast("No description");
  $("#txt-desc").onclick = () => saveFile(new Blob([data.description], { type: "text/plain" }), `${data.id}-description.txt`);

  async function downloadThumb(btn) {
    const old = btn.textContent; btn.disabled = true; btn.textContent = "…";
    try {
      const r = await fetch(`${API}/api/thumbnail/${data.id}/${btn.dataset.thumb}`);
      if (!r.ok) throw new Error();
      saveFile(await r.blob(), `${data.id}-${btn.dataset.thumb}.jpg`);
    } catch { window.open(data.thumbnails.find(t => t.key === btn.dataset.thumb).url, "_blank", "noopener"); }
    finally { btn.disabled = false; btn.textContent = old; }
  }

  async function downloadVideo(btn) {
    const all = $$("#dl [data-q]"), old = btn.textContent, err = $("#dlerr");
    all.forEach(b => b.disabled = true); btn.innerHTML = '<span class="spin"></span> Preparing…';
    err.className = "notice err";
    try {
      const r = await fetch(API + "/api/download", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: data.url, quality: btn.dataset.q }) });
      if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.detail || "Download failed. Please try again."); }
      const cd = r.headers.get("content-disposition") || "";
      const m = cd.match(/filename\*=utf-8''([^;]+)/i) || cd.match(/filename="?([^";]+)"?/i);
      saveFile(await r.blob(), m ? decodeURIComponent(m[1]) : `${data.id}.${btn.dataset.q === "mp3" ? "mp3" : "mp4"}`);
      toast("Download started");
    } catch (e) { err.textContent = e.message; err.className = "notice err show"; }
    finally { all.forEach(b => b.disabled = false); btn.textContent = old; }
  }

  /* ---------- boot ---------- */
  go.dataset.label = go.textContent;
  renderRecent();
  const qv = new URLSearchParams(location.search).get("v");
  if (qv && /^[\w-]{11}$/.test(qv)) { input.value = "https://www.youtube.com/watch?v=" + qv; run(); }
})();

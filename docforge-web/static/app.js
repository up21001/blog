(() => {
  const $ = (id) => document.getElementById(id);

  let lastPayload = null;
  let lastSlug = "document";
  let lastGenerateParams = null;
  let previewTimer = null;

  // ── 유틸리티 ──
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function apiUrl(path) {
    return new URL(path, window.location.origin).href;
  }

  function debounce(fn, ms) {
    let t;
    return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  }

  function getMarkdown() {
    if (activeTab === "split") {
      const s = $("mdEditorSplit");
      if (s && s.value) return s.value;
    }
    const ed = $("mdEditor");
    if (ed && ed.value !== undefined) return ed.value;
    return (lastPayload && lastPayload.markdown) || "";
  }

  function renderPreviewHtml(md) {
    const p = $("preview");
    if (!p) return;
    const processed = renderPreviewWithImages(md);
    p.innerHTML = (window.marked && processed) ? marked.parse(processed) : (processed || "");
  }

  const schedulePreviewRefresh = debounce(() => renderPreviewHtml(getMarkdown()), 220);

  function insertIntoEditor(text) {
    const ed = $("mdEditor");
    if (!ed) return;
    // 에디터 탭으로 전환
    setActiveTab("editor");
    const start = ed.selectionStart;
    const before = ed.value.slice(0, start);
    const after = ed.value.slice(ed.selectionEnd);
    ed.value = before + "\n" + text + "\n" + after;
    ed.selectionStart = ed.selectionEnd = start + text.length + 2;
    ed.focus();
    schedulePreviewRefresh();
  }

  function renderPreviewWithImages(md) {
    // /images/posts/<slug>/image-N.ext → base64 data URI로 치환하여 미리보기
    let processed = md || "";
    currentImages.forEach((img, i) => {
      const ext = img.mime.includes("png") ? "png" : "jpg";
      const fname = `image-${i + 1}.${ext}`;
      const pattern = `/images/posts/${lastSlug}/${fname}`;
      const dataUri = `data:${img.mime};base64,${img.data_base64}`;
      processed = processed.split(pattern).join(dataUri);
    });
    // SVG도 인라인 data URI로 치환
    currentSvgs.forEach((svg, i) => {
      const fname = `svg-${i + 1}.svg`;
      const pattern = `/images/posts/${lastSlug}/${fname}`;
      const encoded = encodeURIComponent(svg.svg || "");
      const dataUri = `data:image/svg+xml,${encoded}`;
      processed = processed.split(pattern).join(dataUri);
    });
    return processed;
  }

  function PathBasename(p) {
    const s = p.replace(/\\/g, "/");
    const i = s.lastIndexOf("/");
    return i >= 0 ? s.slice(i + 1) : s;
  }

  // ── 워크플로우 ──
  function setWorkflow(mode) {
    const s1 = document.querySelector('[data-wf="1"]');
    const s2 = document.querySelector('[data-wf="2"]');
    const s3 = document.querySelector('[data-wf="3"]');
    if (!s1 || !s2 || !s3) return;
    [s1, s2, s3].forEach(s => s.classList.remove("done", "active"));
    if (mode === "review") { s1.classList.add("done"); s2.classList.add("active"); }
    else if (mode === "published") { [s1, s2, s3].forEach(s => s.classList.add("done")); }
  }

  // ── 탭 (분할/미리보기/편집) ──
  let activeTab = "split";

  function syncEditors(source) {
    const main = $("mdEditor");
    const split = $("mdEditorSplit");
    if (source === "split" && main && split) main.value = split.value;
    else if (source === "main" && main && split) split.value = main.value;
  }

  function getMarkdownFromActive() {
    if (activeTab === "split") return ($("mdEditorSplit") && $("mdEditorSplit").value) || "";
    return ($("mdEditor") && $("mdEditor").value) || "";
  }

  function setActiveTab(which) {
    activeTab = which;
    const tabs = ["tabSplit", "tabPreview", "tabEditor"];
    const panels = ["panelSplit", "panelPreview", "panelEditor"];
    tabs.forEach(id => {
      const el = $(id);
      if (el) { el.classList.remove("active"); el.setAttribute("aria-selected", "false"); }
    });
    panels.forEach(id => { const el = $(id); if (el) el.hidden = true; });

    if (which === "split") {
      $("tabSplit").classList.add("active");
      $("panelSplit").hidden = false;
      syncEditors("main");
      renderSplitPreview();
    } else if (which === "preview") {
      $("tabPreview").classList.add("active");
      $("panelPreview").hidden = false;
      syncEditors("split");
      renderPreviewHtml(getMarkdown());
    } else {
      $("tabEditor").classList.add("active");
      $("panelEditor").hidden = false;
      syncEditors("split");
    }
  }

  function renderSplitPreview() {
    const p = $("previewSplit");
    if (!p) return;
    const md = ($("mdEditorSplit") && $("mdEditorSplit").value) || "";
    const processed = renderPreviewWithImages(md);
    p.innerHTML = (window.marked && processed) ? marked.parse(processed) : (processed || "");
  }

  const scheduleSplitRefresh = debounce(renderSplitPreview, 250);

  $("tabSplit").addEventListener("click", () => setActiveTab("split"));
  $("tabPreview").addEventListener("click", () => setActiveTab("preview"));
  $("tabEditor").addEventListener("click", () => setActiveTab("editor"));

  $("mdEditor").addEventListener("input", () => {
    syncEditors("main");
    schedulePreviewRefresh();
  });
  $("mdEditorSplit").addEventListener("input", () => {
    syncEditors("split");
    scheduleSplitRefresh();
  });

  // ── 모델 패널 ──
  function renderModelsPanel(models) {
    const panel = $("modelsPanel");
    if (!models || !panel) return;
    const t = models.text;
    const im = models.image;
    const chain = (im.chain || []).map(m =>
      `<li><strong>${m.order}.</strong> ${escapeHtml(m.label)} — <code>${escapeHtml(m.id)}</code></li>`
    ).join("");
    panel.innerHTML = `<h3>사용 모델</h3>
      <div class="block"><strong>텍스트</strong> <code>${escapeHtml(t.document_and_prompts)}</code></div>
      <div class="block"><strong>이미지</strong> — ${escapeHtml(im.strategy || "")}<ol>${chain}</ol></div>`;
    panel.hidden = false;
  }

  // ══════════════════════════════════════════════════════════
  //  에셋 카드 렌더링
  // ══════════════════════════════════════════════════════════

  /**
   * 현재 에셋 상태 (images + svgs) 를 저장.
   * applyPayload 시 초기화, 개별 추가/삭제 시 갱신.
   */
  let currentImages = [];   // { index, prompt, model, mime, data_base64 }
  let currentSvgs = [];     // { index, type, style, description, svg }

  function renderAssetGrid() {
    const section = $("assetSection");
    const grid = $("assetGrid");
    const count = $("assetCount");

    const total = currentImages.length + currentSvgs.length;
    if (total === 0) {
      section.hidden = true;
      return;
    }
    section.hidden = false;
    count.textContent = `(${total})`;
    grid.innerHTML = "";

    currentImages.forEach((img, i) => grid.appendChild(createImageCard(img, i)));
    currentSvgs.forEach((svg, i) => grid.appendChild(createSvgCard(svg, i)));
  }

  function createImageCard(img, idx) {
    const card = document.createElement("div");
    card.className = "asset-card";
    card.dataset.type = "image";
    card.dataset.idx = idx;

    const promptText = escapeHtml(img.prompt || "");
    card.innerHTML = `
      <div class="asset-card-header">
        <span class="asset-type-badge">이미지 ${idx + 1}</span>
        <div class="asset-card-actions">
          <button class="btn-icon btn-card-regen" title="재생성">🔄</button>
          <button class="btn-icon btn-card-download" title="다운로드">💾</button>
          <button class="btn-icon danger btn-card-delete" title="삭제">✕</button>
        </div>
      </div>
      <div class="asset-card-body">
        <img src="data:${img.mime};base64,${img.data_base64}" alt="" loading="lazy" />
      </div>
      <div class="asset-card-edit">
        <label>프롬프트</label>
        <textarea class="card-prompt" rows="2">${promptText}</textarea>
        <div class="edit-actions">
          <button class="btn btn-sm btn-card-regen-prompt">이 프롬프트로 재생성</button>
          <button class="btn btn-sm btn-card-insert">📎 본문에 삽입</button>
        </div>
      </div>
      <div class="asset-card-meta">${escapeHtml(img.model || "")}</div>
    `;

    // 이벤트
    card.querySelector(".btn-card-regen").addEventListener("click", () => regenImage(idx));
    card.querySelector(".btn-card-regen-prompt").addEventListener("click", () => {
      const newPrompt = card.querySelector(".card-prompt").value.trim();
      if (newPrompt) regenImage(idx, newPrompt);
    });
    card.querySelector(".btn-card-delete").addEventListener("click", () => {
      currentImages.splice(idx, 1);
      renderAssetGrid();
    });
    card.querySelector(".btn-card-download").addEventListener("click", () => {
      const raw = Uint8Array.from(atob(img.data_base64), c => c.charCodeAt(0));
      const ext = img.mime.includes("png") ? "png" : "jpg";
      const blob = new Blob([raw], { type: img.mime });
      saveAs(blob, `image-${idx + 1}.${ext}`);
    });
    card.querySelector(".btn-card-insert").addEventListener("click", () => {
      const ext = img.mime.includes("png") ? "png" : "jpg";
      const fname = `image-${idx + 1}.${ext}`;
      const mdImg = `![${fname}](/images/posts/${lastSlug}/${fname})`;
      insertIntoEditor(mdImg);
    });

    return card;
  }

  function createSvgCard(svg, idx) {
    const card = document.createElement("div");
    card.className = "asset-card";
    card.dataset.type = "svg";
    card.dataset.idx = idx;

    card.innerHTML = `
      <div class="asset-card-header">
        <span class="asset-type-badge badge-svg">SVG ${idx + 1}</span>
        <div class="asset-card-actions">
          <button class="btn-icon btn-card-regen" title="재생성">🔄</button>
          <button class="btn-icon btn-card-download" title="다운로드">💾</button>
          <button class="btn-icon btn-card-copy" title="코드 복사">📋</button>
          <button class="btn-icon danger btn-card-delete" title="삭제">✕</button>
        </div>
      </div>
      <div class="asset-card-body svg-body">${svg.svg || ""}</div>
      <div class="asset-card-edit">
        <div class="edit-actions" style="margin-bottom:0.4rem">
          <button class="btn btn-sm btn-card-insert-svg">📎 본문에 삽입</button>
        </div>
        <button class="svg-code-toggle" type="button">코드 편집 ▼</button>
        <div class="svg-code-wrap" hidden>
          <textarea class="svg-editor" rows="8">${escapeHtml(svg.svg || "")}</textarea>
        </div>
      </div>
      <div class="asset-card-meta">${escapeHtml(svg.type || "")} · ${escapeHtml(svg.style || "")} · ${escapeHtml((svg.description || "").slice(0, 60))}</div>
    `;

    // 코드 토글
    const toggleBtn = card.querySelector(".svg-code-toggle");
    const wrap = card.querySelector(".svg-code-wrap");
    toggleBtn.addEventListener("click", () => {
      const show = wrap.hidden;
      wrap.hidden = !show;
      toggleBtn.textContent = show ? "코드 편집 ▲" : "코드 편집 ▼";
    });

    // SVG 라이브 프리뷰
    const editor = card.querySelector(".svg-editor");
    const body = card.querySelector(".svg-body");
    const debouncedSvg = debounce(() => {
      body.innerHTML = editor.value;
      currentSvgs[idx].svg = editor.value;
    }, 300);
    editor.addEventListener("input", debouncedSvg);

    // 재생성
    card.querySelector(".btn-card-regen").addEventListener("click", () => regenSvg(idx));

    // 삭제
    card.querySelector(".btn-card-delete").addEventListener("click", () => {
      currentSvgs.splice(idx, 1);
      renderAssetGrid();
    });

    // 다운로드
    card.querySelector(".btn-card-download").addEventListener("click", () => {
      const code = currentSvgs[idx].svg || "";
      if (!code) return;
      const blob = new Blob([code], { type: "image/svg+xml;charset=utf-8" });
      const name = (svg.description || "svg").replace(/[^\w가-힣-]/g, "-").slice(0, 40);
      saveAs(blob, `${name}.svg`);
    });

    // 코드 복사
    card.querySelector(".btn-card-copy").addEventListener("click", async () => {
      await navigator.clipboard.writeText(currentSvgs[idx].svg || "");
      const btn = card.querySelector(".btn-card-copy");
      btn.textContent = "✓";
      setTimeout(() => { btn.textContent = "📋"; }, 1200);
    });

    // 본문에 삽입
    card.querySelector(".btn-card-insert-svg").addEventListener("click", () => {
      const fname = `svg-${idx + 1}.svg`;
      const mdImg = `![${svg.description || fname}](/images/posts/${lastSlug}/${fname})`;
      insertIntoEditor(mdImg);
    });

    return card;
  }

  // ── 개별 이미지 재생성 ──
  async function regenImage(idx, promptOverride) {
    const prompt = promptOverride || currentImages[idx]?.prompt;
    if (!prompt) return;

    const cards = $("assetGrid").querySelectorAll('.asset-card[data-type="image"]');
    const card = cards[idx];
    if (card) card.classList.add("loading");

    try {
      const r = await fetch(apiUrl("/api/generate-image"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "이미지 생성 실패");

      currentImages[idx] = {
        index: idx,
        prompt: j.image.prompt,
        model: j.image.model,
        mime: j.image.mime,
        data_base64: j.image.data_base64,
      };
      renderAssetGrid();
    } catch (e) {
      alert("이미지 재생성 실패: " + e.message);
    } finally {
      if (card) card.classList.remove("loading");
    }
  }

  // ── 개별 SVG 재생성 ──
  async function regenSvg(idx) {
    const svg = currentSvgs[idx];
    if (!svg) return;

    const cards = $("assetGrid").querySelectorAll('.asset-card[data-type="svg"]');
    const card = cards[idx];
    if (card) card.classList.add("loading");

    try {
      const r = await fetch(apiUrl("/api/generate-svg"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: svg.description || "diagram",
          svg_type: svg.type || "architecture",
          style: svg.style || "modern",
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "SVG 생성 실패");

      currentSvgs[idx] = { ...svg, svg: j.svg };
      renderAssetGrid();
    } catch (e) {
      alert("SVG 재생성 실패: " + e.message);
    } finally {
      if (card) card.classList.remove("loading");
    }
  }

  // ── 이미지 추가 ──
  $("btnAddImage").addEventListener("click", () => {
    $("addImageForm").hidden = false;
    $("addSvgForm").hidden = true;
    $("addImagePrompt").focus();
  });
  $("btnAddImageCancel").addEventListener("click", () => {
    $("addImageForm").hidden = true;
  });
  $("btnAddImageSubmit").addEventListener("click", async () => {
    const prompt = $("addImagePrompt").value.trim();
    if (!prompt) return;
    $("btnAddImageSubmit").disabled = true;
    $("btnAddImageSubmit").textContent = "생성 중…";

    try {
      const r = await fetch(apiUrl("/api/generate-image"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "실패");

      currentImages.push({
        index: currentImages.length,
        prompt: j.image.prompt,
        model: j.image.model,
        mime: j.image.mime,
        data_base64: j.image.data_base64,
      });
      renderAssetGrid();
      $("addImageForm").hidden = true;
      $("addImagePrompt").value = "";
    } catch (e) {
      alert("이미지 추가 실패: " + e.message);
    } finally {
      $("btnAddImageSubmit").disabled = false;
      $("btnAddImageSubmit").textContent = "생성";
    }
  });

  // ── SVG 추가 ──
  $("btnAddSvg").addEventListener("click", () => {
    $("addSvgForm").hidden = false;
    $("addImageForm").hidden = true;
    $("addSvgDesc").focus();
  });
  $("btnAddSvgCancel").addEventListener("click", () => {
    $("addSvgForm").hidden = true;
  });
  $("btnAddSvgSubmit").addEventListener("click", async () => {
    const desc = $("addSvgDesc").value.trim();
    if (!desc) return;
    $("btnAddSvgSubmit").disabled = true;
    $("btnAddSvgSubmit").textContent = "생성 중…";

    try {
      const r = await fetch(apiUrl("/api/generate-svg"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: desc,
          svg_type: $("addSvgType").value,
          style: $("addSvgStyle").value,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "실패");

      currentSvgs.push({
        index: currentSvgs.length,
        type: $("addSvgType").value,
        style: $("addSvgStyle").value,
        description: desc,
        svg: j.svg,
      });
      renderAssetGrid();
      $("addSvgForm").hidden = true;
      $("addSvgDesc").value = "";
    } catch (e) {
      alert("SVG 추가 실패: " + e.message);
    } finally {
      $("btnAddSvgSubmit").disabled = false;
      $("btnAddSvgSubmit").textContent = "생성";
    }
  });

  // ══════════════════════════════════════════════════════════
  //  결과 적용
  // ══════════════════════════════════════════════════════════

  function applyPayload(j) {
    lastPayload = j;
    lastSlug = (j.manifest && j.manifest.slug) || "document";

    const imgCount = (j.images || []).length;
    const svgCount = (j.svgs || []).length;
    $("meta").textContent = `소요 ${j.manifest.elapsed_ms}ms · 이미지 ${imgCount}장 · SVG ${svgCount}개 · 템플릿 ${j.template}`;

    const fn = $("publishFilename");
    if (fn && j.suggested_filename) fn.value = j.suggested_filename;

    const editor = $("mdEditor");
    if (editor) editor.value = j.markdown || "";
    const splitEditor = $("mdEditorSplit");
    if (splitEditor) splitEditor.value = j.markdown || "";

    // 에셋 상태 초기화
    currentImages = (j.images || []).map((img, i) => ({
      index: i,
      prompt: (j.image_prompts && j.image_prompts[i]) || img.prompt || "",
      model: img.model,
      mime: img.mime,
      data_base64: img.data_base64,
    }));
    currentSvgs = (j.svgs || []).map((svg, i) => ({
      index: i,
      type: svg.type || "architecture",
      style: svg.style || "modern",
      description: svg.description || "",
      svg: svg.svg || "",
    }));
    renderAssetGrid();

    renderPreviewHtml(getMarkdown());
    setWorkflow("review");
    const ps = $("publishStatus");
    if (ps) ps.textContent = "";
    updatePublishCategoryRecap();
  }

  // ══════════════════════════════════════════════════════════
  //  생성
  // ══════════════════════════════════════════════════════════

  async function runGenerate() {
    const err = $("error");
    const load = $("loading");
    const res = $("result");
    err.hidden = true;
    res.hidden = true;
    load.hidden = false;
    $("submitBtn").disabled = true;

    const topic = $("topic").value.trim();
    const template = $("template").value;
    const with_images = $("withImages").checked;
    const max_images = Math.min(4, Math.max(0, parseInt($("maxImages").value, 10) || 0));
    const with_svg = $("withSvg").checked;
    const max_svg = Math.min(6, Math.max(0, parseInt($("maxSvg").value, 10) || 0));
    const length = ($("lengthTier") && $("lengthTier").value) || "medium";
    const image_hints = ($("imageHints").value || "").trim() || null;

    lastGenerateParams = { topic, template, with_images, max_images: with_images ? max_images : 0, with_svg, max_svg: with_svg ? max_svg : 0, length, image_hints };

    try {
      const r = await fetch(apiUrl("/api/generate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic, template, with_images,
          max_images: with_images ? max_images : 0,
          with_svg, max_svg: with_svg ? max_svg : 0,
          length, image_hints,
        }),
      });
      const j = await r.json();
      if (!r.ok) {
        let msg = j.message;
        if (typeof j.detail === "string") msg = j.detail;
        else if (Array.isArray(j.detail)) msg = j.detail.map(x => x.msg || JSON.stringify(x)).join("; ");
        else if (j.detail) msg = JSON.stringify(j.detail);
        throw new Error(msg || "요청 실패");
      }
      if (j.models) renderModelsPanel(j.models);
      applyPayload(j);
      res.hidden = false;
      setActiveTab("split");
    } catch (ex) {
      err.textContent = String(ex.message || ex);
      err.hidden = false;
    } finally {
      load.hidden = true;
      $("submitBtn").disabled = false;
    }
  }

  $("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await runGenerate();
  });

  // ── 재생성 바 ──
  $("btnRegenFull").addEventListener("click", () => {
    if (!lastGenerateParams) { alert("먼저 생성해 주세요."); return; }
    if (!confirm("전체 재생성합니다. 현재 편집 내용이 덮어씌워집니다.")) return;
    $("topic").value = lastGenerateParams.topic;
    $("template").value = lastGenerateParams.template;
    $("withImages").checked = lastGenerateParams.with_images;
    $("maxImages").value = String(lastGenerateParams.max_images);
    $("withSvg").checked = lastGenerateParams.with_svg;
    $("maxSvg").value = String(lastGenerateParams.max_svg);
    if ($("lengthTier")) $("lengthTier").value = lastGenerateParams.length;
    if ($("imageHints")) $("imageHints").value = lastGenerateParams.image_hints || "";
    runGenerate();
  });

  $("btnRegenTextOnly").addEventListener("click", () => {
    if (!lastGenerateParams) { alert("먼저 생성해 주세요."); return; }
    const params = { ...lastGenerateParams, with_images: false, max_images: 0, with_svg: false, max_svg: 0 };
    lastGenerateParams = params;
    $("withImages").checked = false;
    $("withSvg").checked = false;
    runGenerate();
  });

  $("btnRegenTone").addEventListener("click", () => {
    if (!lastGenerateParams) { alert("먼저 생성해 주세요."); return; }
    const tone = $("toneSelect").value;
    if (!tone) { alert("톤을 선택하세요."); return; }
    const map = {
      formal: "격식체로 다시 써라. ~입니다/~합니다 스타일 유지.",
      casual: "친근한 구어체로 다시 써라. ~요/~죠 스타일.",
      academic: "학술 논문 스타일로 다시 써라.",
      simple: "초보자도 이해하도록 쉽게 설명."
    };
    const prev = lastGenerateParams.topic;
    $("topic").value = prev + "\n\n[톤 지시] " + (map[tone] || "");
    runGenerate().finally(() => { $("topic").value = prev; });
  });

  // ── 다운로드 / 복사 ──
  $("btnCopy").addEventListener("click", async () => {
    const md = getMarkdown();
    if (!md) return;
    await navigator.clipboard.writeText(md);
    $("btnCopy").textContent = "복사됨";
    setTimeout(() => { $("btnCopy").textContent = "마크다운 복사"; }, 1500);
  });

  $("btnMd").addEventListener("click", () => {
    const md = getMarkdown();
    if (!md) return;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const base = ($("publishFilename") && $("publishFilename").value.trim()) || `${lastSlug}.md`;
    const name = base.toLowerCase().endsWith(".md") ? base : `${base}.md`;
    saveAs(blob, PathBasename(name));
  });

  $("btnZip").addEventListener("click", async () => {
    if (!window.JSZip) { alert("JSZip 로드 실패"); return; }
    const zip = new JSZip();
    const md = getMarkdown();
    const base = ($("publishFilename") && $("publishFilename").value.trim()) || `${lastSlug}.md`;
    const mdName = PathBasename(base.toLowerCase().endsWith(".md") ? base : `${base}.md`);
    zip.file(mdName, md || "");

    // 이미지
    if (currentImages.length) {
      const folder = zip.folder("images");
      currentImages.forEach((img, i) => {
        const ext = img.mime.includes("png") ? "png" : "jpg";
        const raw = Uint8Array.from(atob(img.data_base64), c => c.charCodeAt(0));
        folder.file(`image-${i + 1}.${ext}`, raw);
      });
    }
    // SVG
    if (currentSvgs.length) {
      const folder = zip.folder("svg");
      currentSvgs.forEach((svg, i) => {
        folder.file(`svg-${i + 1}.svg`, svg.svg || "");
      });
    }

    const blob = await zip.generateAsync({ type: "blob" });
    const stem = mdName.replace(/\.md$/i, "");
    saveAs(blob, `${stem}-docforge.zip`);
  });

  // ── 바로 저장 (블로그에 저장) ──
  $("btnQuickPublish").addEventListener("click", async () => {
    const md = getMarkdown().trim();
    if (!md) { alert("저장할 마크다운이 없습니다."); return; }

    const sub = ($("publishSubfolder") && $("publishSubfolder").value.trim()) || null;
    const fname = ($("publishFilename") && $("publishFilename").value.trim()) || null;
    if (!sub) {
      alert("카테고리를 선택해주세요 (하단 저장 영역 또는 상단 폼).");
      $("publishSubfolder").focus();
      return;
    }

    const btn = $("btnQuickPublish");
    btn.disabled = true;
    btn.textContent = "저장 중…";

    try {
      const imagesToSave = currentImages.map((img, i) => {
        const ext = img.mime.includes("png") ? "png" : "jpg";
        return { filename: `image-${i + 1}.${ext}`, mime: img.mime, data_base64: img.data_base64 };
      });
      currentSvgs.forEach((svg, i) => {
        const svgB64 = btoa(unescape(encodeURIComponent(svg.svg || "")));
        imagesToSave.push({ filename: `svg-${i + 1}.svg`, mime: "image/svg+xml", data_base64: svgB64 });
      });

      const r = await fetch(apiUrl("/api/publish-post"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdown: md, filename: fname || null, slug_hint: lastSlug,
          subfolder: sub, images: imagesToSave.length ? imagesToSave : null,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j));

      if ($("publishSubfolder")) localStorage.setItem(SUBFOLDER_LS, $("publishSubfolder").value);
      const rel = j.relative_path || j.filename;
      const savedImgs = j.saved_images || [];
      alert(`저장 완료!\n\n📄 content/posts/${rel}\n🖼 이미지 ${savedImgs.length}개 저장됨`);
      setWorkflow("published");
      const ps = $("publishStatus");
      if (ps) ps.textContent = `저장됨: content/posts/${rel}`;
    } catch (e) {
      alert("저장 실패: " + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "블로그에 저장";
    }
  });

  // ── 게시 ──
  const SUBFOLDER_LS = "docforge_publish_subfolder";

  function updatePublishCategoryRecap() {
    const s = $("publishSubfolder");
    const el = $("publishCategoryRecap");
    if (!el || !s) return;
    el.hidden = false;
    el.textContent = s.value ? `저장 예정: content/posts/${s.value}/` : `저장 예정: content/posts/ (루트)`;
  }

  function bindPublishSubfolderOnce() {
    const sel = $("publishSubfolder");
    if (!sel || sel.dataset.bound) return;
    sel.dataset.bound = "1";
    sel.addEventListener("change", () => {
      localStorage.setItem(SUBFOLDER_LS, sel.value);
      updatePublishCategoryRecap();
    });
  }

  $("btnPublish").addEventListener("click", async () => {
    const md = getMarkdown().trim();
    const status = $("publishStatus");
    if (!md) { status.textContent = "저장할 마크다운이 없습니다."; return; }
    status.textContent = "저장 중…";
    $("btnPublish").disabled = true;
    try {
      const fname = $("publishFilename").value.trim();
      const sub = ($("publishSubfolder") && $("publishSubfolder").value.trim()) || null;
      // 이미지 데이터를 함께 전송
      const imagesToSave = currentImages.map((img, i) => {
        const ext = img.mime.includes("png") ? "png" : "jpg";
        return {
          filename: `image-${i + 1}.${ext}`,
          mime: img.mime,
          data_base64: img.data_base64,
        };
      });
      // SVG도 이미지로 저장
      currentSvgs.forEach((svg, i) => {
        const svgB64 = btoa(unescape(encodeURIComponent(svg.svg || "")));
        imagesToSave.push({
          filename: `svg-${i + 1}.svg`,
          mime: "image/svg+xml",
          data_base64: svgB64,
        });
      });
      const r = await fetch(apiUrl("/api/publish-post"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdown: md, filename: fname || null, slug_hint: lastSlug,
          subfolder: sub, images: imagesToSave.length ? imagesToSave : null,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j));
      if ($("publishSubfolder")) localStorage.setItem(SUBFOLDER_LS, $("publishSubfolder").value);
      const rel = j.relative_path || j.filename;
      status.textContent = `저장됨: content/posts/${rel}`;
      setWorkflow("published");
    } catch (e) {
      status.textContent = String(e.message || e);
    } finally {
      $("btnPublish").disabled = false;
    }
  });

  $("btnRegenerate").addEventListener("click", async () => {
    if (!lastGenerateParams) { alert("먼저 생성해 주세요."); return; }
    if (!confirm("다시 생성합니다. 편집 내용이 덮어씌워집니다.")) return;
    $("topic").value = lastGenerateParams.topic;
    $("template").value = lastGenerateParams.template;
    $("withImages").checked = lastGenerateParams.with_images;
    $("maxImages").value = String(lastGenerateParams.max_images);
    $("withSvg").checked = lastGenerateParams.with_svg;
    $("maxSvg").value = String(lastGenerateParams.max_svg);
    if ($("lengthTier")) $("lengthTier").value = lastGenerateParams.length;
    if ($("imageHints")) $("imageHints").value = lastGenerateParams.image_hints || "";
    await runGenerate();
  });

  // ── 헬스 / 콘텐트 타깃 ──
  async function checkHealth() {
    const el = $("healthLine");
    if (window.location.protocol === "file:") {
      el.className = "health bad";
      el.innerHTML = "이 페이지를 <strong>파일로 연 상태</strong>입니다. <code>http://127.0.0.1:8765</code>로 여세요.";
      return;
    }
    try {
      const r = await fetch(apiUrl("/api/health"), { cache: "no-store" });
      const j = await r.json();
      const url = window.location.origin;
      if (j.gemini_configured) {
        el.className = "health ok";
        el.innerHTML = `<code>GEMINI_API_KEY</code> 로드됨 · 서버: <code>${url}</code>`;
      } else {
        el.className = "health bad";
        el.innerHTML = `<code>GEMINI_API_KEY</code> 없음 · .env에 키를 넣으세요 · 서버: <code>${url}</code>`;
      }
      if (j.models) renderModelsPanel(j.models);
    } catch (e) {
      el.className = "health bad";
      el.innerHTML = `서버 연결 불가 (${e.message || e})`;
    }
  }

  async function fetchContentTarget() {
    const line = $("contentTargetLine");
    if (!line || window.location.protocol === "file:") return;
    try {
      const r = await fetch(apiUrl("/api/content-target"), { cache: "no-store" });
      const j = await r.json();
      const dir = escapeHtml(j.posts_dir || "");
      const subs = Array.isArray(j.subfolders) ? j.subfolders : [];
      line.hidden = false;
      line.className = "content-target meta" + (j.writable ? "" : " warn");
      line.innerHTML = j.writable
        ? `저장 위치: <code>${dir}</code> · 카테고리 ${subs.length}개`
        : `저장 위치: <code>${dir || "—"}</code> — <strong>쓰기 불가</strong>`;

      const sel = $("publishSubfolder");
      if (sel) {
        bindPublishSubfolderOnce();
        const saved = localStorage.getItem(SUBFOLDER_LS) || "";
        sel.innerHTML = '<option value="">(루트 — posts 바로 아래)</option>';
        subs.forEach(name => {
          const o = document.createElement("option");
          o.value = name; o.textContent = name;
          sel.appendChild(o);
        });
        if (saved && [...sel.options].some(o => o.value === saved)) sel.value = saved;
        updatePublishCategoryRecap();
      }
    } catch { line.hidden = true; }
  }

  // ── 카테고리 추천 ──
  $("btnSuggestCategory").addEventListener("click", async () => {
    const topic = $("topic").value.trim() || getMarkdown().slice(0, 2000);
    if (!topic) { alert("주제를 먼저 입력하세요."); return; }

    const btn = $("btnSuggestCategory");
    btn.disabled = true;
    btn.textContent = "분석 중…";

    try {
      const r = await fetch(apiUrl("/api/suggest-category"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "추천 실패");

      const sel = $("publishSubfolder");
      const match = [...sel.options].find(o => o.value === j.category);
      if (match) {
        sel.value = j.category;
        localStorage.setItem(SUBFOLDER_LS, j.category);
        updatePublishCategoryRecap();
      } else {
        alert(`추천: ${j.category} (목록에 없음)`);
      }
    } catch (e) {
      alert("추천 실패: " + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "추천";
    }
  });

  // ── 기존 글 열기 ──
  async function loadPostCategories() {
    const sel = $("openPostCategory");
    if (!sel) return;
    try {
      const r = await fetch(apiUrl("/api/content-target"), { cache: "no-store" });
      const j = await r.json();
      const subs = Array.isArray(j.subfolders) ? j.subfolders : [];
      sel.innerHTML = '<option value="">카테고리 선택</option><option value="__root__">(루트)</option>';
      subs.forEach(name => {
        const o = document.createElement("option");
        o.value = name; o.textContent = name;
        sel.appendChild(o);
      });
    } catch {}
  }

  $("openPostCategory").addEventListener("change", async () => {
    const cat = $("openPostCategory").value;
    const fileSel = $("openPostFile");
    const btn = $("btnOpenPost");
    fileSel.innerHTML = '<option value="">파일 선택</option>';
    fileSel.disabled = true;
    btn.disabled = true;
    if (!cat) return;

    const subfolder = cat === "__root__" ? "" : cat;
    try {
      const r = await fetch(apiUrl(`/api/posts?subfolder=${encodeURIComponent(subfolder)}`));
      const j = await r.json();
      const posts = j.posts || [];
      if (!posts.length) {
        fileSel.innerHTML = '<option value="">포스트 없음</option>';
        return;
      }
      posts.slice(0, 50).forEach(p => {
        const o = document.createElement("option");
        o.value = p.path; o.textContent = p.name;
        fileSel.appendChild(o);
      });
      fileSel.disabled = false;
    } catch {}
  });

  $("openPostFile").addEventListener("change", () => {
    $("btnOpenPost").disabled = !$("openPostFile").value;
  });

  $("btnOpenPost").addEventListener("click", async () => {
    const path = $("openPostFile").value;
    if (!path) return;
    const err = $("error");
    const load = $("loading");
    const res = $("result");
    err.hidden = true;
    res.hidden = true;
    load.hidden = false;
    $("loadingText").textContent = "포스트 불러오는 중…";
    $("btnOpenPost").disabled = true;

    try {
      const r = await fetch(apiUrl(`/api/post?path=${encodeURIComponent(path)}`));
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "불러오기 실패");

      lastSlug = j.slug || "post";
      lastGenerateParams = null;

      // 에디터에 마크다운 설정
      $("mdEditor").value = j.markdown || "";
      $("publishFilename").value = j.filename || "";
      if (j.subfolder && $("publishSubfolder")) {
        $("publishSubfolder").value = j.subfolder;
        localStorage.setItem(SUBFOLDER_LS, j.subfolder);
      }

      // 이미지 로드
      currentImages = (j.images || []).map((img, i) => ({
        index: i,
        prompt: img.url || "",
        model: "저장된 이미지",
        mime: img.mime,
        data_base64: img.data_base64,
      }));
      // SVG 로드
      currentSvgs = (j.svgs || []).map((svg, i) => ({
        index: i,
        type: svg.type || "architecture",
        style: svg.style || "modern",
        description: svg.description || svg.filename || "",
        svg: svg.svg || "",
      }));
      renderAssetGrid();

      $("meta").textContent = `기존 포스트: ${path}`;
      renderPreviewHtml(getMarkdown());
      setWorkflow("review");
      updatePublishCategoryRecap();
      res.hidden = false;
      setActiveTab("split");
    } catch (ex) {
      err.textContent = String(ex.message || ex);
      err.hidden = false;
    } finally {
      load.hidden = true;
      $("loadingText").textContent = "생성 중… 잠시만 기다려 주세요.";
      $("btnOpenPost").disabled = false;
    }
  });

  // ── URL 임포트 ──
  $("importForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = $("importUrl").value.trim();
    if (!url) return;

    const err = $("error");
    const load = $("loading");
    const res = $("result");
    err.hidden = true;
    res.hidden = true;
    load.hidden = false;
    $("loadingText").textContent = "URL 가져오는 중… 글 다듬는 중…";
    $("importBtn").disabled = true;

    try {
      const r = await fetch(apiUrl("/api/import-url"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const j = await r.json();
      if (!r.ok) {
        let msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j);
        throw new Error(msg || "가져오기 실패");
      }
      if (j.models) renderModelsPanel(j.models);
      lastGenerateParams = { topic: url, template: "blog", with_images: false, max_images: 0, with_svg: false, max_svg: 0, length: "medium", image_hints: null };
      applyPayload(j);
      res.hidden = false;
      setActiveTab("split");
    } catch (ex) {
      err.textContent = String(ex.message || ex);
      err.hidden = false;
    } finally {
      load.hidden = true;
      $("loadingText").textContent = "생성 중… 잠시만 기다려 주세요.";
      $("importBtn").disabled = false;
    }
  });

  // ── 초기화 ──
  checkHealth();
  fetchContentTarget();
  loadPostCategories();

  document.querySelectorAll("a[data-app-edit]").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      location.assign(new URL("edit", window.location.href).href);
    });
  });
})();

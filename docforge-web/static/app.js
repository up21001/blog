(() => {
  const $ = (id) => document.getElementById(id);

  let lastPayload = null;
  let lastSlug = "document";
  let lastGenerateParams = null;
  let previewTimer = null;
  let currentMarkdownKo = "";
  let currentMarkdownEn = "";
  let currentLang = "ko"; // "ko" | "en"

  // ── 유틸리티 ──
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function apiUrl(path) {
    const p = path.startsWith("/") ? path : `/${path}`;
    const raw = (typeof localStorage !== "undefined" && localStorage.getItem("docforge_api_base")) || "";
    const stored = raw.trim();
    if (stored && /^https?:\/\//i.test(stored)) {
      const base = stored.replace(/\/$/, "");
      return new URL(p, `${base}/`).href;
    }
    const proto = window.location.protocol;
    const origin = window.location.origin;
    if (proto === "http:" || proto === "https:") {
      if (origin && origin !== "null") {
        return new URL(p, `${origin}/`).href;
      }
    }
    return new URL(p, "http://127.0.0.1:8765/").href;
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

  function getMarkdownForLang(lang) {
    if (lang === "en") return currentMarkdownEn;
    // KO: 현재 편집 중이면 에디터에서, 아니면 저장된 변수에서
    if (currentLang === "ko") {
      const live = getMarkdown();
      if (live) return live;
    }
    return currentMarkdownKo;
  }

  function setMarkdownForLang(lang, md) {
    if (lang === "en") {
      currentMarkdownEn = md;
    } else {
      currentMarkdownKo = md;
      const ed = $("mdEditor");
      if (ed) ed.value = md;
      const split = $("mdEditorSplit");
      if (split) split.value = md;
    }
  }

  // ── 언어 전환 ──
  function switchLang(lang) {
    if (lang === currentLang) return;
    // 현재 편집 내용을 해당 언어 변수에 저장
    const currentContent = getMarkdown();
    if (currentLang === "ko") currentMarkdownKo = currentContent;
    else currentMarkdownEn = currentContent;
    currentLang = lang;
    // 새 언어 내용 로드
    const md = (lang === "en" ? currentMarkdownEn : currentMarkdownKo) || "";
    const ed = $("mdEditor");
    if (ed) ed.value = md;
    const split = $("mdEditorSplit");
    if (split) split.value = md;
    // 모든 미리보기 패널 갱신
    renderPreviewHtml(md);
    if (typeof renderSplitPreview === "function") renderSplitPreview();
    // 탭 활성화
    document.querySelectorAll(".lang-tab").forEach(b => {
      b.classList.toggle("active", b.dataset.lang === lang);
    });
  }

  // 언어 탭 이벤트
  document.querySelectorAll(".lang-tab").forEach(btn => {
    btn.addEventListener("click", () => switchLang(btn.dataset.lang));
  });

  // 영문 재번역 버튼
  $("btnRetranslate").addEventListener("click", async () => {
    const btn = $("btnRetranslate");
    // 현재 편집 내용 저장
    setMarkdownForLang(currentLang, getMarkdown());
    const koMd = getMarkdownForLang("ko");
    if (!koMd.trim()) { alert("한글 본문이 없습니다."); return; }

    btn.disabled = true;
    btn.textContent = "번역 중…";
    try {
      const r = await fetch(apiUrl("/api/translate-en"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown: koMd }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "번역 실패");
      currentMarkdownEn = j.markdown_en || "";
      // 영문 탭으로 전환해서 결과 보여주기
      switchLang("en");
      alert("영문 재번역 완료!");
    } catch (e) {
      alert("번역 실패: " + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "🔄 영문 재번역";
    }
  });

  // ── 글 다듬기 (Polish) ──
  if ($("btnPolish")) {
    $("btnPolish").addEventListener("click", async () => {
      const btn = $("btnPolish");
      const md = getMarkdown();
      if (!md.trim()) { alert("다듬을 마크다운이 없습니다."); return; }
      const style = ($("polishStyle") && $("polishStyle").value) || "engaging";
      if (style === "none") { alert("다듬기 스타일을 선택해주세요."); return; }

      btn.disabled = true;
      btn.textContent = "다듬는 중…";
      try {
        const r = await fetch(apiUrl("/api/polish"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ markdown: md, style }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || "다듬기 실패");

        const polished = j.markdown || "";
        if (polished) {
          setMarkdownForLang(currentLang, polished);
          $("mdEditor").value = polished;
          const split = $("mdEditorSplit");
          if (split) split.value = polished;
          renderPreviewHtml(polished);
          if (typeof renderSplitPreview === "function") renderSplitPreview();
        }
      } catch (e) {
        alert("다듬기 실패: " + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = "✨ 글 다듬기";
      }
    });
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

  /** SVG 문자열을 안전하게 미리보기 (innerHTML에 직접 넣지 않음 — </div> 등으로 카드 DOM이 깨지는 것 방지) */
  function svgToDataUri(svgStr) {
    const s = String(svgStr || "").trim();
    if (!s) return "";
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(s)}`;
  }

  function syncSvgPreviewBody(bodyEl, code) {
    if (!bodyEl) return;
    const uri = svgToDataUri(code);
    let img = bodyEl.querySelector(".svg-preview-img");
    let empty = bodyEl.querySelector(".svg-empty-preview");
    if (uri) {
      if (empty) empty.hidden = true;
      if (!img) {
        img = document.createElement("img");
        img.className = "svg-preview-img";
        img.alt = "";
        bodyEl.appendChild(img);
      }
      img.hidden = false;
      img.src = uri;
    } else {
      if (img) {
        img.hidden = true;
        img.removeAttribute("src");
      }
      if (!empty) {
        empty = document.createElement("span");
        empty.className = "svg-empty-preview";
        bodyEl.appendChild(empty);
      }
      empty.hidden = false;
      empty.textContent = "SVG 코드 없음 — 재생성을 눌러 주세요";
    }
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
        <span class="asset-model-label">${escapeHtml(img.model || "")}</span>
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
      <div class="asset-card-body svg-body"></div>
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
      currentSvgs[idx].svg = editor.value;
      syncSvgPreviewBody(body, editor.value);
    }, 300);
    editor.addEventListener("input", debouncedSvg);
    syncSvgPreviewBody(body, svg.svg || "");

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
          language: svg.language || ($("addSvgLang") ? $("addSvgLang").value : "ko"),
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
          language: $("addSvgLang") ? $("addSvgLang").value : "ko",
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

  async function applyPayload(j) {
    lastPayload = j;
    lastSlug = (j.manifest && j.manifest.slug) || "document";

    const imgCount = (j.images || []).length;
    const svgCount = (j.svgs || []).length;
    $("meta").textContent = `소요 ${j.manifest.elapsed_ms}ms · 이미지 ${imgCount}장 · SVG ${svgCount}개 · 템플릿 ${j.template}`;

    const fn = $("publishFilename");
    if (fn && j.suggested_filename) fn.value = j.suggested_filename;

    currentMarkdownKo = j.markdown || "";
    const editor = $("mdEditor");
    if (editor) editor.value = currentMarkdownKo;
    const splitEditor = $("mdEditorSplit");
    if (splitEditor) splitEditor.value = currentMarkdownKo;

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

    // 영문 SVG 저장 (있으면)
    window._currentSvgsEn = (j.svgs_en || []).map((svg, i) => ({
      index: i,
      type: svg.type || "architecture",
      style: svg.style || "modern",
      description: svg.description || "",
      svg: svg.svg || "",
    }));
    renderAssetGrid();

    // 영문 마크다운 저장 및 언어 탭 표시
    currentMarkdownEn = j.markdown_en || "";
    currentLang = "ko";
    const langTabs = $("langTabs");
    if (langTabs) {
      langTabs.hidden = !currentMarkdownEn;
      document.querySelectorAll(".lang-tab").forEach(b => {
        b.classList.toggle("active", b.dataset.lang === "ko");
      });
    }

    renderPreviewHtml(getMarkdown());
    setWorkflow("review");
    const ps = $("publishStatus");
    if (ps) ps.textContent = "";
    updatePublishCategoryRecap();

    // 생성 후 자동 다듬기 (polishStyle이 "none"이 아닌 경우)
    const autoPolishStyle = ($("polishStyle") && $("polishStyle").value) || "none";
    if (autoPolishStyle !== "none" && currentMarkdownKo.trim()) {
      const polishBtn = $("btnPolish");
      if (polishBtn) {
        polishBtn.disabled = true;
        polishBtn.textContent = "자동 다듬기 중…";
      }
      try {
        const pr = await fetch(apiUrl("/api/polish"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ markdown: currentMarkdownKo, style: autoPolishStyle }),
        });
        const pj = await pr.json();
        if (pr.ok && pj.markdown) {
          currentMarkdownKo = pj.markdown;
          const ed = $("mdEditor");
          if (ed) ed.value = currentMarkdownKo;
          const sp = $("mdEditorSplit");
          if (sp) sp.value = currentMarkdownKo;
          renderPreviewHtml(currentMarkdownKo);
          if (typeof renderSplitPreview === "function") renderSplitPreview();
          $("meta").textContent += ` · ✨ 다듬기(${autoPolishStyle}) 적용`;
        }
      } catch (e) {
        console.warn("자동 다듬기 실패:", e);
      } finally {
        if (polishBtn) {
          polishBtn.disabled = false;
          polishBtn.textContent = "✨ 글 다듬기";
        }
      }
    }
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

    const with_english = $("withEnglish") ? $("withEnglish").checked : false;
    const model_preset = ($("modelPreset") && $("modelPreset").value) || "fast";

    // 참고 양식 파일 읽기
    let reference_doc = null;
    let reference_file_b64 = null;
    let reference_file_name = null;
    const refInput = $("referenceDoc");
    if (refInput && refInput.files && refInput.files.length > 0) {
      const file = refInput.files[0];
      reference_file_name = file.name;
      const ext = file.name.split(".").pop().toLowerCase();
      if (["md", "txt", "markdown", "html", "htm"].includes(ext)) {
        reference_doc = await file.text();
      } else {
        // docx, pdf → base64
        const buf = await file.arrayBuffer();
        reference_file_b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
      }
    }

    // 코드베이스 경로 읽기 및 기본 검증
    const codebasePathEl = $("codebasePath");
    const codebase_path = (codebasePathEl && codebasePathEl.value.trim()) || "";
    if (codebase_path) {
      const statusEl = $("codebasePathStatus");
      // 보안 경고: 민감 경로 패턴 체크 (로컬 도구이므로 경고만)
      const suspiciousPaths = ["/etc", "/sys", "/proc", "C:\\Windows", "C:\\Program Files"];
      const looksRisky = suspiciousPaths.some(p => codebase_path.startsWith(p));
      if (looksRisky && statusEl) {
        statusEl.textContent = "⚠ 시스템 경로가 포함될 수 있습니다.";
        statusEl.className = "codebase-path-status warn";
      } else if (statusEl) {
        statusEl.textContent = "";
        statusEl.className = "codebase-path-status";
      }
    }

    lastGenerateParams = { topic, template, with_images, max_images: with_images ? max_images : 0, with_svg, max_svg: with_svg ? max_svg : 0, length, image_hints, with_english, model_preset };

    try {
      const r = await fetch(apiUrl("/api/generate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic, template, with_images,
          max_images: with_images ? max_images : 0,
          with_svg, max_svg: with_svg ? max_svg : 0,
          length, image_hints, with_english, model_preset,
          reference_doc, reference_file_b64, reference_file_name,
          reference_url: ($("referenceUrl") && $("referenceUrl").value.trim()) || null,
          codebase_path: codebase_path || "",
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

  // ── 빌드 & 배포 ──
  $("btnHugoBuild").addEventListener("click", async () => {
    const btn = $("btnHugoBuild");
    btn.disabled = true; btn.textContent = "빌드 중…";
    try {
      const r = await fetch(apiUrl("/api/hugo-build"), { method: "POST" });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "빌드 실패");
      alert("Hugo 빌드 완료! localhost:1313에서 확인하세요.");
    } catch (e) { alert("빌드 실패: " + e.message); }
    finally { btn.disabled = false; btn.textContent = "빌드"; }
  });

  $("btnGitPush").addEventListener("click", async () => {
    if (!confirm("변경사항을 커밋하고 GitHub에 푸시합니다. 진행할까요?")) return;
    const btn = $("btnGitPush");
    btn.disabled = true; btn.textContent = "배포 중…";
    try {
      const r = await fetch(apiUrl("/api/git-push"), { method: "POST" });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "배포 실패");
      alert(j.message || "배포 완료!");
    } catch (e) { alert("배포 실패: " + e.message); }
    finally { btn.disabled = false; btn.textContent = "배포"; }
  });

  // ── 에셋 자동 삽입 (Gemini가 본문 분석 후 적절한 위치에 배치) ──
  async function autoInsertAssets() {
    let md = getMarkdown();
    const missing = [];

    currentImages.forEach((img, i) => {
      const ext = img.mime.includes("png") ? "png" : "jpg";
      const fname = `image-${i + 1}.${ext}`;
      const path = `/images/posts/${lastSlug}/${fname}`;
      if (!md.includes(path)) missing.push({ path, description: fname });
    });

    currentSvgs.forEach((svg, i) => {
      const fname = `svg-${i + 1}.svg`;
      const path = `/images/posts/${lastSlug}/${fname}`;
      if (!md.includes(path)) missing.push({ path, description: svg.description || fname });
    });

    if (missing.length === 0) return md;

    try {
      const r = await fetch(apiUrl("/api/auto-insert-assets"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown: md, assets: missing }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || "삽입 실패");

      md = j.markdown;
      $("mdEditor").value = md;
      const split = $("mdEditorSplit");
      if (split) split.value = md;
    } catch (e) {
      console.warn("에셋 자동 삽입 실패, 끝에 추가:", e);
      missing.forEach(a => { md += `\n\n![${a.description}](${a.path})`; });
      $("mdEditor").value = md;
      const split = $("mdEditorSplit");
      if (split) split.value = md;
    }
    return md;
  }

  // ── 바로 저장 (블로그에 저장) ──
  $("btnQuickPublish").addEventListener("click", async () => {
    const btn = $("btnQuickPublish");
    btn.disabled = true;
    btn.textContent = "에셋 배치 중…";

    const md = (await autoInsertAssets()).trim();
    if (!md) { alert("저장할 마크다운이 없습니다."); btn.disabled = false; btn.textContent = "블로그에 저장"; return; }

    btn.textContent = "저장 중…";
    const sub = ($("publishSubfolder") && $("publishSubfolder").value.trim()) || null;
    const fname = ($("publishFilename") && $("publishFilename").value.trim()) || null;
    if (!sub) {
      alert("카테고리를 선택해주세요 (하단 저장 영역 또는 상단 폼).");
      btn.disabled = false;
      btn.textContent = "블로그에 저장";
      $("publishSubfolder").focus();
      return;
    }

    try {
      const imagesToSave = currentImages.map((img, i) => {
        const ext = img.mime.includes("png") ? "png" : "jpg";
        return { filename: `image-${i + 1}.${ext}`, mime: img.mime, data_base64: img.data_base64 };
      });
      currentSvgs.forEach((svg, i) => {
        const svgContent = svg.svg || "";
        // 빈 SVG 또는 플레이스홀더(240x56) 필터링
        if (!svgContent || svgContent.length < 200 || svgContent.includes('viewBox="0 0 240 56"')) {
          console.warn(`SVG ${i + 1} 건너뜀 (빈/플레이스홀더)`);
          return;
        }
        const svgB64 = btoa(unescape(encodeURIComponent(svgContent)));
        imagesToSave.push({ filename: `svg-${i + 1}.svg`, mime: "image/svg+xml", data_base64: svgB64 });
      });
      // 영문 SVG도 저장
      if (window._currentSvgsEn && window._currentSvgsEn.length) {
        window._currentSvgsEn.forEach((svg, i) => {
          const svgContent = svg.svg || "";
          if (!svgContent || svgContent.length < 200 || svgContent.includes('viewBox="0 0 240 56"')) {
            console.warn(`SVG-EN ${i + 1} 건너뜀 (빈/플레이스홀더)`);
            return;
          }
          const svgB64 = btoa(unescape(encodeURIComponent(svgContent)));
          imagesToSave.push({ filename: `svg-${i + 1}-en.svg`, mime: "image/svg+xml", data_base64: svgB64 });
        });
      }

      // 현재 언어가 en이면 영문 내용 동기화
      if (currentLang === "en") currentMarkdownEn = md;
      const enMd = currentLang === "ko" ? currentMarkdownEn : md;
      const koMd = currentLang === "ko" ? md : getMarkdownForLang("ko");

      const r = await fetch(apiUrl("/api/publish-post"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdown: koMd, markdown_en: enMd || null,
          filename: fname || null, slug_hint: lastSlug,
          subfolder: sub, images: imagesToSave.length ? imagesToSave : null,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j));

      if ($("publishSubfolder")) localStorage.setItem(SUBFOLDER_LS, $("publishSubfolder").value);
      const rel = j.relative_path || j.filename;
      const savedImgs = j.saved_images || [];
      const enInfo = j.en_filename ? `\n🇺🇸 ${j.en_filename}` : "";
      alert(`저장 완료!\n\n📄 content/posts/${rel}${enInfo}\n🖼 이미지 ${savedImgs.length}개 저장됨`);
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
    const md = (await autoInsertAssets()).trim();
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
      if (currentLang === "en") currentMarkdownEn = md;
      const enMd2 = currentLang === "ko" ? currentMarkdownEn : md;
      const koMd2 = currentLang === "ko" ? md : getMarkdownForLang("ko");

      const r = await fetch(apiUrl("/api/publish-post"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdown: koMd2, markdown_en: enMd2 || null,
          filename: fname || null, slug_hint: lastSlug,
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

  async function appendTrending404Diagnosis() {
    const lines = ["", "── 자동 진단 ──"];
    try {
      const hr = await fetch(apiUrl("/api/health"), { cache: "no-store" });
      const hj = await hr.json().catch(() => ({}));
      if (hr.ok) {
        lines.push(`GET /api/health → OK, version=${hj.version != null ? hj.version : "?"}`);
        if (!hj.capabilities || !hj.capabilities.trending_topics) {
          lines.push("→ capabilities.trending_topics 없음: 구버전 DocForge가 8765에서 돌고 있을 수 있습니다.");
        }
      } else {
        lines.push(`GET /api/health → HTTP ${hr.status} (이 주소에 DocForge API가 아닐 수 있음)`);
      }
    } catch (e) {
      lines.push(`GET /api/health 실패: ${e.message || e}`);
    }
    try {
      const orr = await fetch(apiUrl("/openapi.json"), { cache: "no-store" });
      const spec = await orr.json();
      const has = spec.paths && Object.prototype.hasOwnProperty.call(spec.paths, "/api/trending-topics");
      lines.push(
        has
          ? "OpenAPI: /api/trending-topics 등록됨 (URL/프록시 불일치 가능)"
          : "OpenAPI: /api/trending-topics 없음 → 실행 중인 app.py가 트렌드 이전 버전입니다.",
      );
    } catch (e) {
      lines.push(`OpenAPI 조회 실패: ${e.message || e}`);
    }
    lines.push("", "포트 점유 확인(PowerShell): netstat -ano | findstr :8765");
    return lines.join("\n");
  }

  // ── 트렌드 주제 (Hacker News + DEV Community 공개 API) ──
  const btnTrend = $("btnTrendingTopics");
  if (btnTrend) {
    btnTrend.addEventListener("click", async () => {
      const panel = $("trendingPanel");
      const list = $("trendingList");
      const errEl = $("trendingError");
      const meta = $("trendingMeta");
      const loc = $("trendingLocalize");
      const localize = !!(loc && loc.checked);
      if (panel) panel.hidden = false;
      if (errEl) {
        errEl.hidden = true;
        errEl.textContent = "";
      }
      if (meta) meta.textContent = "";
      if (list) list.innerHTML = "<li class=\"trending-loading\">불러오는 중…</li>";
      btnTrend.disabled = true;
      try {
        const r = await fetch(
          apiUrl(`/api/trending-topics?limit=18&localize=${localize ? "true" : "false"}`),
          { cache: "no-store" },
        );
        const j = await r.json().catch(() => ({}));
        if (!r.ok) {
          const d = j.detail;
          let msg = typeof d === "string" ? d : (Array.isArray(d) ? d.map((x) => x.msg || x).join(" ") : JSON.stringify(d || {}));
          if (r.status === 404 || msg === "Not Found") {
            msg = [
              "API를 찾을 수 없습니다(404).",
              "",
              "① docforge-web 폴더에서 서버를 다시 켜 보세요.",
              "   .\\run.ps1",
              "   또는: python -m uvicorn app:app --host 127.0.0.1 --reload --port 8765",
              "② 8765를 이미 쓰는 다른 프로그램이 있으면 끄거나 DocForge를 다른 포트로 띄운 뒤",
              "   localStorage.setItem(\"docforge_api_base\", \"http://127.0.0.1:새포트\")",
              "③ Live Server로 HTML만 연 경우에도 위와 같이 docforge_api_base를 맞추세요.",
            ].join("\n");
            msg += await appendTrending404Diagnosis();
          }
          throw new Error(msg || "불러오기 실패");
        }
        const items = Array.isArray(j.items) ? j.items : [];
        if (meta) {
          meta.textContent = `갱신(UTC): ${j.fetched_at || "—"} · HN + DEV${localize ? " · 한글 주제 변환" : ""}`;
        }
        if (!list) return;
        list.innerHTML = "";
        if (!items.length) {
          list.innerHTML = "<li class=\"trending-loading\">항목이 없습니다.</li>";
          return;
        }
        items.forEach((it) => {
          const topicLine = (it.topic_ko != null && String(it.topic_ko).trim())
            ? String(it.topic_ko).trim()
            : String(it.title || "").trim();
          const li = document.createElement("li");
          const left = document.createElement("div");
          left.className = "trend-title";
          const srcEl = document.createElement("div");
          srcEl.className = "trend-src";
          srcEl.textContent = String(it.source || "").replace(/_/g, " ");
          left.appendChild(srcEl);
          const t1 = document.createElement("div");
          t1.textContent = it.title || "";
          left.appendChild(t1);
          if (it.topic_ko && String(it.topic_ko).trim() && it.topic_ko !== it.title) {
            const tk = document.createElement("div");
            tk.className = "trend-ko";
            tk.textContent = it.topic_ko;
            left.appendChild(tk);
          }
          const btns = document.createElement("div");
          btns.className = "trend-btns";
          const a = document.createElement("a");
          a.className = "trend-link";
          a.textContent = "원문";
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          if (it.url) a.href = it.url;
          const use = document.createElement("button");
          use.type = "button";
          use.className = "trend-use";
          use.textContent = "적용";
          use.addEventListener("click", () => {
            const ta = $("topic");
            if (ta) {
              ta.value = topicLine;
              ta.focus();
            }
          });
          btns.appendChild(a);
          btns.appendChild(use);
          li.appendChild(left);
          li.appendChild(btns);
          list.appendChild(li);
        });
      } catch (e) {
        if (errEl) {
          errEl.hidden = false;
          errEl.textContent = e.message || String(e);
        }
        if (list) list.innerHTML = "";
      } finally {
        btnTrend.disabled = false;
      }
    });
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

      // 영문 마크다운 로드
      currentMarkdownEn = j.markdown_en || "";
      currentLang = "ko";
      const langTabs = $("langTabs");
      if (langTabs) {
        langTabs.hidden = !currentMarkdownEn;
        document.querySelectorAll(".lang-tab").forEach(b => {
          b.classList.toggle("active", b.dataset.lang === "ko");
        });
      }

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

  // ── 서버 상태/재시작 버튼 ──
  $("btnHealthCheck").addEventListener("click", () => checkHealth());

  $("btnServerRestart").addEventListener("click", async () => {
    if (!confirm("서버를 재시작합니다. 진행할까요?")) return;
    $("btnServerRestart").disabled = true;
    $("btnServerRestart").textContent = "재시작 중…";
    try {
      await fetch(apiUrl("/api/restart"), { method: "POST" });
    } catch {}
    // 서버가 죽었다가 살아나므로 폴링
    let ok = false;
    for (let i = 0; i < 10; i++) {
      await new Promise(r => setTimeout(r, 2000));
      try {
        const r = await fetch(apiUrl("/api/health"), { cache: "no-store" });
        if (r.ok) { ok = true; break; }
      } catch {}
    }
    if (ok) {
      checkHealth();
      alert("서버 재시작 완료");
    } else {
      alert("서버 재시작 실패 — 터미널에서 수동으로 시작하세요.");
    }
    $("btnServerRestart").disabled = false;
    $("btnServerRestart").textContent = "재시작";
  });

  // ════════════════════════════════════════════
  // ── 시리즈 기획 (Series Planning) ──
  // ════════════════════════════════════════════
  let currentSeriesPlan = null;   // { series_name, parts: [...] }
  let currentGlossary = {};       // { "한글": "English", ... }
  // parts 별 번역 결과 캐시: index → translated markdown
  const partTranslations = {};

  function renderSeriesPlan(plan) {
    currentSeriesPlan = plan;
    $("seriesPlanName").textContent = plan.series_name || "시리즈";
    const list = $("seriesPartsList");
    list.innerHTML = "";
    (plan.parts || []).forEach((part, idx) => {
      const card = document.createElement("div");
      card.className = "series-part-card";
      card.id = `seriesPartCard-${idx}`;
      const svgHints = (part.suggested_svgs || []).map(s => escapeHtml(s)).join(", ");
      card.innerHTML = `
        <div class="series-part-card-header">
          <span class="series-part-order">파트 ${part.order || idx + 1}</span>
          <span class="series-part-title">${escapeHtml(part.title || "")}</span>
        </div>
        <div class="series-part-slug"><code>${escapeHtml(part.slug || "")}</code></div>
        <div class="series-part-desc">${escapeHtml(part.description || "")}</div>
        <div class="series-part-scope">✔ ${escapeHtml(part.scope || "")}</div>
        ${svgHints ? `<div class="series-part-svgs">SVG 제안: ${svgHints}</div>` : ""}
        <div class="series-part-actions">
          <button type="button" class="btn btn-sm btn-use-part" data-idx="${idx}">이 파트로 생성</button>
        </div>
        <div class="series-part-translated" id="partTranslated-${idx}" hidden></div>`;
      list.appendChild(card);
    });

    // "이 파트로 생성" 버튼 이벤트
    list.querySelectorAll(".btn-use-part").forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.idx, 10);
        const part = plan.parts[idx];
        if (!part) return;
        // 메인 폼에 파트 정보 채우기
        const topicEl = $("topic");
        if (topicEl) {
          topicEl.value = `[${plan.series_name}] 파트 ${part.order || idx + 1}: ${part.title}\n\n${part.description || ""}\n\n범위: ${part.scope || ""}`;
        }
        // 스크롤 to 메인 폼
        $("form") && $("form").scrollIntoView({ behavior: "smooth" });
        // 상태 표시
        $("seriesPlanStatus").textContent = `파트 ${part.order || idx + 1} 정보를 주제 칸에 넣었습니다.`;
      });
    });

    $("seriesPlanResult").hidden = false;
  }

  // 기획 생성 버튼
  $("btnPlanSeries").addEventListener("click", async () => {
    const topic = ($("seriesTopic") && $("seriesTopic").value.trim()) || "";
    if (!topic) { alert("시리즈 주제를 입력해 주세요."); return; }
    const partCount = parseInt(($("seriesPartCount") && $("seriesPartCount").value) || "5", 10);
    const seriesName = ($("seriesNameHint") && $("seriesNameHint").value.trim()) || "";

    $("btnPlanSeries").disabled = true;
    $("seriesPlanStatus").textContent = "기획 생성 중…";
    $("seriesPlanResult").hidden = true;

    try {
      const resp = await fetch(apiUrl("/api/plan-series"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, part_count: partCount, series_name: seriesName, language: "ko" }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || resp.statusText);
      renderSeriesPlan(data.plan);
      $("seriesPlanStatus").textContent = `${(data.plan.parts || []).length}개 파트 기획 완료`;
      // 용어집 초기화
      currentGlossary = {};
      $("glossaryDetails").hidden = true;
    } catch (e) {
      $("seriesPlanStatus").textContent = `오류: ${e.message}`;
    } finally {
      $("btnPlanSeries").disabled = false;
    }
  });

  // 일괄 번역 버튼
  $("btnTranslateSeries").addEventListener("click", async () => {
    if (!currentSeriesPlan) return;
    // parts에서 마크다운 수집 — 파트 카드에 마크다운이 없으면 description을 플레이스홀더로 사용
    // 실제로는 이미 생성된 파트 마크다운이 있어야 유용하지만,
    // 여기서는 lastPayload.markdown을 포함해 생성된 글이 있으면 번역 대상에 포함
    const markdowns = [];
    const plan = currentSeriesPlan;
    // 이미 생성된 현재 마크다운을 첫 번째로 포함 (있을 경우)
    const curMd = getMarkdown();
    if (curMd && curMd.trim()) {
      markdowns.push(curMd);
    } else {
      // 각 파트의 description을 임시 마크다운으로
      (plan.parts || []).forEach(p => {
        markdowns.push(`# ${p.title}\n\n${p.description || ""}\n\n## 범위\n${p.scope || ""}`);
      });
    }
    if (!markdowns.length) {
      alert("번역할 마크다운이 없습니다. 먼저 파트를 생성해 주세요.");
      return;
    }

    $("btnTranslateSeries").disabled = true;
    $("seriesTranslateStatus").textContent = "번역 중…";
    $("glossaryDetails").hidden = true;

    try {
      const resp = await fetch(apiUrl("/api/translate-series"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          markdowns,
          series_name_en: plan.series_name,
          glossary: currentGlossary && Object.keys(currentGlossary).length ? currentGlossary : {},
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || resp.statusText);

      currentGlossary = data.glossary || {};
      const translations = data.translations || [];

      // 번역 결과를 영문 에디터에 적용 (첫 번째)
      if (translations[0]) {
        currentMarkdownEn = translations[0];
        const langTabs = $("langTabs");
        if (langTabs) langTabs.hidden = false;
        // 영문 탭으로 전환
        switchLang("en");
      }

      // 각 파트 카드에 번역 완료 표시
      translations.forEach((tr, idx) => {
        partTranslations[idx] = tr;
        const el = $(`partTranslated-${idx}`);
        if (el) {
          el.textContent = "번역 완료";
          el.hidden = false;
        }
      });

      // 용어집 표시
      const glossaryKeys = Object.keys(currentGlossary);
      if (glossaryKeys.length) {
        $("glossaryCount").textContent = `(${glossaryKeys.length}개 용어)`;
        const table = $("glossaryTable");
        table.innerHTML = glossaryKeys.map(k =>
          `<span class="g-ko">${escapeHtml(k)}</span><span class="g-en">${escapeHtml(currentGlossary[k])}</span>`
        ).join("");
        $("glossaryDetails").hidden = false;
      }

      $("seriesTranslateStatus").textContent = `번역 완료 (${translations.length}개)`;
    } catch (e) {
      $("seriesTranslateStatus").textContent = `오류: ${e.message}`;
    } finally {
      $("btnTranslateSeries").disabled = false;
    }
  });

  // ── 확장 생성 ──
  if ($("btnExpand")) {
    $("btnExpand").addEventListener("click", async () => {
      const source = $("expandSource") ? $("expandSource").value.trim() : "";
      const instructions = $("expandInstructions") ? $("expandInstructions").value.trim() : "";
      const withEn = $("expandWithEnglish") ? $("expandWithEnglish").checked : false;
      if (!source) { alert("원본 소재를 입력하세요."); return; }

      const btn = $("btnExpand");
      const status = $("expandStatus");
      btn.disabled = true;
      btn.textContent = "확장 중…";
      if (status) status.textContent = "생성 중…";

      try {
        const r = await fetch(apiUrl("/api/expand"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_text: source,
            instructions: instructions || "10라운드로 확장, 더 깊고 극적으로",
            with_english: withEn,
          }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j));

        // Apply to main editor
        const koMd = j.ko || "";
        const enMd = j.en || "";
        $("mdEditor").value = koMd;
        const split = $("mdEditorSplit");
        if (split) split.value = koMd;
        currentMarkdownEn = enMd;
        currentLang = "ko";

        const langTabs = $("langTabs");
        if (langTabs) {
          langTabs.hidden = !enMd;
          document.querySelectorAll(".lang-tab").forEach(b => {
            b.classList.toggle("active", b.dataset.lang === "ko");
          });
        }

        renderPreviewHtml(koMd);
        const res = $("result");
        if (res) res.hidden = false;
        setActiveTab("split");
        setWorkflow("review");
        if (status) status.textContent = "확장 완료!";
        // Close the expand details panel
        const det = $("expandDetails");
        if (det) det.open = false;
      } catch (e) {
        if (status) status.textContent = "오류: " + e.message;
        else alert("확장 실패: " + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = "확장 생성";
      }
    });
  }

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

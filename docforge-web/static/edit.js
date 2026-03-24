(() => {
  if (window.location.protocol === "file:") {
    const warn = document.getElementById("editProtoWarn");
    if (warn) warn.style.display = "block";
  }

  /** API 키 → DOM id (blog 등 단순 id는 광고 차단기에 걸릴 수 있어 df* 사용) */
  const PROMPT_FIELDS = [
    ["blog", "dfTmplBlog"],
    ["philosophy", "dfTmplPhilosophy"],
    ["plain", "dfTmplPlain"],
    ["document_user", "dfDocumentUser"],
    ["image_prompt_generator", "dfImagePrompt"],
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function apiUrl(path) {
    return new URL(path, window.location.origin).href;
  }

  function setStatus(msg, ok) {
    const el = $("editStatus");
    el.className = ok ? "health ok" : "health bad";
    el.textContent = msg;
  }

  function fillForm(prompts) {
    if (!prompts || typeof prompts !== "object") return;
    PROMPT_FIELDS.forEach(([key, domId]) => {
      const el = $(domId);
      if (el && prompts[key] != null) el.value = prompts[key];
    });
  }

  function collectPayload() {
    const o = {};
    PROMPT_FIELDS.forEach(([key, domId]) => {
      const el = $(domId);
      o[key] = el ? el.value : "";
    });
    return o;
  }

  async function loadPrompts() {
    const fileHint = $("editFileHint");
    if (window.location.protocol === "file:") {
      fileHint.hidden = false;
      fileHint.className = "health bad";
      fileHint.textContent =
        "이 페이지를 파일로 연 상태입니다. uvicorn으로 서버를 켠 뒤 http://127.0.0.1:8765/edit 로 여세요.";
      setStatus("API에 연결할 수 없습니다.", false);
      return;
    }
    fileHint.hidden = true;
    try {
      const r = await fetch(apiUrl("/api/prompts"), { cache: "no-store" });
      const j = await r.json();
      if (!r.ok) {
        let msg = "로드 실패";
        if (typeof j.detail === "string") msg = j.detail;
        else if (Array.isArray(j.detail)) {
          msg = j.detail
            .map((x) => {
              if (typeof x === "string") return x;
              if (x && typeof x.msg === "string") {
                const loc = Array.isArray(x.loc) ? x.loc.filter(Boolean).join(".") : "";
                return loc ? `${loc}: ${x.msg}` : x.msg;
              }
              return JSON.stringify(x);
            })
            .join("; ");
        } else if (j.detail != null) msg = JSON.stringify(j.detail);
        throw new Error(msg);
      }
      if (!j.prompts || typeof j.prompts !== "object") {
        throw new Error("응답에 prompts가 없습니다. 같은 주소(포트)의 DocForge 서버인지 확인하세요.");
      }
      fillForm(j.prompts);
      setStatus("불러왔습니다. 수정 후 저장하세요.", true);
    } catch (e) {
      setStatus(String(e.message || e), false);
    }
  }

  $("btnSave").addEventListener("click", async () => {
    try {
      const r = await fetch(apiUrl("/api/prompts"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectPayload()),
      });
      const j = await r.json();
      if (!r.ok) {
        const d = j.detail;
        throw new Error(typeof d === "string" ? d : JSON.stringify(d));
      }
      fillForm(j.prompts);
      setStatus("저장되었습니다 (data/user_prompts.json).", true);
    } catch (e) {
      setStatus(String(e.message || e), false);
    }
  });

  $("btnBuiltin").addEventListener("click", async () => {
    try {
      const r = await fetch(apiUrl("/api/prompts/builtins"), { cache: "no-store" });
      const j = await r.json();
      if (!r.ok) throw new Error("불러오기 실패");
      fillForm(j.prompts);
      setStatus("코드 기본값을 폼에 채웠습니다. 반영하려면 저장을 누르세요.", true);
    } catch (e) {
      setStatus(String(e.message || e), false);
    }
  });

  $("btnReset").addEventListener("click", async () => {
    if (
      !confirm(
        "저장된 user_prompts.json을 삭제하고 모든 프롬프트를 코드 기본값으로 되돌립니다. 계속할까요?"
      )
    ) {
      return;
    }
    try {
      const r = await fetch(apiUrl("/api/prompts/reset"), { method: "POST" });
      const j = await r.json();
      if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : "실패");
      fillForm(j.prompts);
      setStatus("초기화됨. 기본 프롬프트가 적용됩니다.", true);
    } catch (e) {
      setStatus(String(e.message || e), false);
    }
  });

  $("btnSave").disabled = true;
  loadPrompts().finally(() => {
    $("btnSave").disabled = false;
  });
})();

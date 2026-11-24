const USE_SAMPLE = true;   // TODO: false, когда появится эндпоинт с findings.json

const SAMPLE = [
  { id: "F1", verdict: "real", confidence: "high", rule: "py/sql-injection", file: "introduction/views.py:142", cwe: "CWE-89",
    why: "User input from request.POST reaches cursor.execute without parameterization.",
    advice: "Use a parameterized query: cursor.execute(\"... WHERE name = %s\", [name]).",
    code: "[SOURCE 1]\nname = request.POST.get('name')\n\n[SINK 2]\ncursor.execute(query)",
    salieri: "64 s, 2100 tokens in / 512 out", amadeus: "11 s, 1900 tokens in / 240 out" },
  { id: "F2", verdict: "unknown", confidence: "low", rule: "py/path-injection", file: "introduction/utils.py:58", cwe: "CWE-22",
    why: "Context was expanded 5 -> 10 -> 40 lines, the model stayed unsure.",
    advice: "Normalize and validate the path. Please verify manually.",
    code: "[SOURCE 1]\nfname = request.GET['file']\n\n[SINK 2]\nopen(path)",
    salieri: "3 rounds, 190 s", amadeus: "10 s" },
  { id: "F3", verdict: "false_positive", rule: "py/sql-injection", file: "introduction/views.py:77", cwe: "CWE-89",
    reason: "The value is replaced by a constant before the query.",
    code: "valuesList.remove(0)\nbar = valuesList.get(1)", salieri: "58 s, 1800 tokens in / 500 out" },
];

const LABEL = { high: "high confidence", medium: "medium confidence", low: "low confidence" };
const ICON = { real: "✖", unknown: "?", false_positive: "✔" };
const STATUS = { real: "real", unknown: "undetermined", false_positive: "false positive" };
const $ = id => document.getElementById(id);

let findings = [];

function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
}

function rowOf(f) {
    const r = el("div", "row " + f.verdict);
    r.dataset.id = f.id;
    const info = el("div", "info");
    info.append(el("div", "title", f.rule), el("div", "where", f.file));
    r.append(el("div", "icon", ICON[f.verdict]), info,
             el("span", "conf", f.confidence ? LABEL[f.confidence] : ""),
             el("span", "status", STATUS[f.verdict]));
    if (f.verdict === "false_positive") r.append(el("div", "reason", f.reason || ""));
    r.onclick = () => openDrawer(f.id);
    return r;
}

function render() {
    const q = $("search").value.toLowerCase(), flt = $("filter").value;
    const main = findings.filter(f => f.verdict !== "false_positive" &&
        (flt === "all" || f.verdict === flt) && (f.file + f.rule).toLowerCase().includes(q));
    const fps = findings.filter(f => f.verdict === "false_positive");

    $("n-total").textContent = findings.length;
    $("n-real").textContent = findings.filter(f => f.verdict === "real").length;
    $("n-unknown").textContent = findings.filter(f => f.verdict === "unknown").length;
    $("n-fp").textContent = fps.length;

    $("findings").replaceChildren(...main.map(rowOf));
    $("fp-findings").replaceChildren(...fps.map(rowOf));
    $("fp-summary").textContent = `Probably false positives (${fps.length}): kept for review, not deleted`;
}

function openDrawer(id) {
    const f = findings.find(x => x.id === id), fp = f.verdict === "false_positive";
    document.querySelectorAll(".row").forEach(r => r.classList.toggle("sel", r.dataset.id === id));
    $("d-rule").textContent = f.rule;
    $("d-file").textContent = f.file;
    $("d-cwe").textContent = f.cwe || "";
    $("d-why").textContent = fp ? f.reason : f.why;
    $("d-advice").textContent = f.advice || "";
    $("d-code").textContent = f.code || "";
    $("d-salieri").textContent = f.salieri || "";
    $("d-amadeus").textContent = f.amadeus || "";
    // у ложных срабатываний нет совета: прячем совет, пометку и блок Amadeus
    $("d-advice").closest("details").hidden = fp;
    $("d-amadeus").closest("details").hidden = fp;
    document.querySelector(".note").hidden = fp;
    $("drawer").hidden = false;
    $("layout").classList.add("open");
}

function closeDrawer() {
    $("drawer").hidden = true;
    $("layout").classList.remove("open");
    document.querySelectorAll(".row.sel").forEach(r => r.classList.remove("sel"));
}

async function load() {
    if (USE_SAMPLE) return SAMPLE;
    const scanId = new URLSearchParams(location.search).get("scan_id");
    if (!scanId) return [];
    const r = await fetch(`/api/results/${encodeURIComponent(scanId)}`);   // TODO: эндпоинт
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
}

(async function init() {
    try {
        findings = await load();
    } catch (e) {
        $("empty").textContent = "Could not load results: " + e.message;
        return;
    }
    if (!findings.length) return;                 // остаётся пустое состояние
    if (USE_SAMPLE) $("empty").textContent = "Sample data (no scan connected yet)";
    $("empty").hidden = USE_SAMPLE ? false : true;
    $("layout").hidden = false;
    $("search").oninput = render;
    $("filter").onchange = render;
    $("drawer-close").onclick = closeDrawer;
    render();
})();
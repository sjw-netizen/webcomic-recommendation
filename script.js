// 상단 우측 날짜/시간을 현재 시각으로 표시하고 1초마다 갱신
const nowEl = document.getElementById("now");
const days = ["일", "월", "화", "수", "목", "금", "토"];

function pad(n) {
  return String(n).padStart(2, "0");
}

function updateNow() {
  const d = new Date();
  const date = `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`;

  nowEl.textContent = `${date} (${days[d.getDay()]}) ${time}`;
  nowEl.dateTime = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${time}`;
}

updateNow();
setInterval(updateNow, 1000);

// 새로고침 버튼: 각 플랫폼 실시간 순위 상위 5개로 웹툰 목록을 바꾸고 안내 문장 표시
const refreshBtn = document.getElementById("refresh");
const messageEl = document.getElementById("message");

// 기존 HTML과 같은 구조(<a><img><p>제목</p></a>)로 웹툰 하나를 만든다
function createItem(item) {
  const a = document.createElement("a");
  a.href = item.url;
  a.target = "_blank";
  a.rel = "noopener";

  const img = document.createElement("img");
  img.src = item.cover;
  img.alt = `${item.title} 표지`;
  img.width = 200;

  const p = document.createElement("p");
  p.textContent = item.title;

  a.append(img, p);
  return a;
}

// 섹션의 가로 스크롤 행(.row) 안 웹툰 목록만 교체한다
function renderSection(id, items) {
  const row = document.querySelector(`#${id} .row`);
  row.replaceChildren(...items.map(createItem));
}

// ranking.json(update_ranking.py가 만든 순위 파일)을 읽어 각 섹션을 상위 10개로 바꾼다
async function loadRanking() {
  // 브라우저가 예전 파일을 재사용하지 않도록 주소 뒤에 시각을 붙인다
  const res = await fetch(`ranking.json?t=${Date.now()}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();

  for (const id of ["naver", "kakao", "ridi", "lezhin"]) {
    if (Array.isArray(data[id])) renderSection(id, data[id]);
  }
}

// 페이지를 열 때 최신 순위로 표시 (실패하면 HTML에 적힌 목록을 그대로 보여준다)
loadRanking().catch(() => {});

// 버튼 아래에 문장을 띄우고, 1초 뒤 서서히 사라지게 한다
let hideTimer;

function showMessage(text, autoHide = true) {
  clearTimeout(hideTimer);
  messageEl.textContent = text;
  messageEl.classList.add("show");
  if (autoHide) {
    hideTimer = setTimeout(() => messageEl.classList.remove("show"), 1000);
  }
}

refreshBtn.addEventListener("click", async function () {
  refreshBtn.disabled = true;
  showMessage("불러오는 중...", false);

  try {
    await loadRanking();
    showMessage("실시간 정보를 반영했습니다.");
  } catch (e) {
    showMessage("실시간 정보를 불러오지 못했습니다.");
  } finally {
    refreshBtn.disabled = false;
  }
});

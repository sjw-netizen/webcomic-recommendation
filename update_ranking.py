"""네 플랫폼의 웹툰 순위 상위 10개를 받아 ranking.json으로 저장한다.

실행: python update_ranking.py
GitHub에 올리면 GitHub Actions가 1시간마다 자동으로 실행한다.
(브라우저는 CORS 때문에 다른 사이트 데이터를 직접 받을 수 없어서 미리 받아 둔다.)
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

TOP_N = 10
KST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking.json")


def fetch(url, referer=None):
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.read().decode("utf-8")


def naver_top():
    """네이버웹툰: 오늘 요일 웹툰 인기순"""
    weekday = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    today = weekday[datetime.now(KST).weekday()]
    data = json.loads(fetch("https://comic.naver.com/api/webtoon/titlelist/weekday?order=user"))
    items = [t for t in data["titleListMap"][today] if not t["adult"]][:TOP_N]
    return [
        {
            "title": t["titleName"],
            "url": f"https://comic.naver.com/webtoon/list?titleId={t['titleId']}",
            # image-comic 주소는 외부 사이트에서 막혀 있어 공유용 주소로 바꾼다
            "cover": t["thumbnailUrl"].replace(
                "https://image-comic.pstatic.net/webtoon/",
                "https://shared-comic.pstatic.net/thumb/webtoon/",
            ),
        }
        for t in items
    ]


def kakao_top():
    """카카오페이지: 웹툰 실시간 랭킹"""
    url = ("https://bff-page.kakao.com/api/gateway/view/v1/landing/ranking"
           "?category_uid=10&ranking_type=hourly&page=0")
    data = json.loads(fetch(url, referer="https://page.kakao.com/"))["result"]
    items = [t for t in data["list"] if t["age_grade"] < 19][:TOP_N]
    return [
        {
            "title": t["title"],
            "url": f"https://page.kakao.com/content/{t['series_id']}",
            "cover": f"https://page-images.kakaoentcdn.com/download/resource?kid={t['thumbnail']}&filename=th3",
        }
        for t in items
    ]


def ridi_top():
    """리디: 웹툰 오늘의 베스트 (성인 제외)"""
    html = fetch("https://ridibooks.com/bestsellers/webtoon?adult_exclude=y")
    raw = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1)
    queries = json.loads(raw)["props"]["pageProps"]["dehydratedState"]["queries"]
    best = next(q for q in queries if q["queryKey"][0] == "BestSellers")
    items = best["state"]["data"]["bestsellers"]["items"][:TOP_N]
    return [
        {
            "title": it["book"]["series"]["title"],
            "url": f"https://ridibooks.com/books/{it['book']['series']['id']}",
            "cover": it["book"]["series"]["thumbnail"]["xxlarge"].split("#")[0],
        }
        for it in items
    ]


def lezhin_top():
    """레진: 실시간 랭킹 (비로그인 기본 모드라 성인 작품 제외)"""
    html = fetch("https://www.lezhin.com/ko/ranking")
    # 페이지에 조각조각 나뉘어 들어 있는 데이터(self.__next_f.push)를 이어 붙여 해석한다
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    text = "".join(json.loads(f'"{c}"') for c in chunks)
    start = text.find('{"state":{"mutations"')
    state, _ = json.JSONDecoder().raw_decode(text[start:])
    ranking = next(q for q in state["state"]["queries"]
                   if q["queryKey"][0] == "/v2/content-list/ranking"
                   and q["queryKey"][2]["rankType"] == "realtime")
    items = ranking["state"]["data"]["data"]["data"][:TOP_N]
    return [
        {
            "title": t["title"],
            "url": f"https://www.lezhin.com/ko/comic/{t['alias']}",
            "cover": f"https://ccdn.lezhin.com/v2/comics/{t['id']}/images/tall.jpg",
        }
        for t in items
    ]


def main():
    # 이전 결과가 있으면 불러온다 (한 플랫폼이 실패하면 그 플랫폼은 이전 순위를 유지)
    try:
        with open(OUTPUT, encoding="utf-8") as f:
            result = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        result = {}

    platforms = [("naver", naver_top), ("kakao", kakao_top), ("ridi", ridi_top), ("lezhin", lezhin_top)]
    for name, func in platforms:
        try:
            result[name] = func()
            print(f"{name}: {len(result[name])}개")
        except Exception as e:
            print(f"{name}: 실패 ({e}) - 이전 순위 유지")

    result["updated_at"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {OUTPUT}")


if __name__ == "__main__":
    main()

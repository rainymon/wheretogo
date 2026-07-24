import html
import math
import random
from urllib.parse import quote, urlencode

import requests
import streamlit as st


APP_VERSION = "VWORLD-MARKERS-ADDRESS-PHOTOS-20260724"

st.set_page_config(
    page_title="어디갈까? 서울",
    page_icon="🧭",
    layout="centered",
)

START_POINTS = {
    "서울역": (37.5547, 126.9707),
    "용산역": (37.5298, 126.9648),
    "청량리역": (37.5802, 127.0473),
    "홍대입구역": (37.5572, 126.9254),
    "강남역": (37.4979, 127.0276),
    "잠실역": (37.5133, 127.1002),
    "서울고속버스터미널": (37.5048, 127.0049),
    "동서울터미널": (37.5349, 127.0958),
    "남부터미널": (37.4850, 127.0162),
}

PLACES = [
    {
        "name": "망원동", "arrival": "망원역", "lat": 37.5561, "lon": 126.9100,
        "category": ["시장", "골목", "한강"],
        "intro": "시장과 낮은 골목, 한강 산책을 한 번에 즐길 수 있는 생활형 여행지입니다.",
        "things": ["망원시장 한 바퀴", "골목 산책", "망원한강공원까지 걷기"],
        "photo_query": "Mangwon Market Seoul",
        "food_query": "망원동 맛집", "cafe_query": "망원동 카페",
    },
    {
        "name": "연희동", "arrival": "연희동 주민센터", "lat": 37.5687, "lon": 126.9304,
        "category": ["골목", "카페", "책"],
        "intro": "조용한 주택가 골목과 작은 식당, 독립서점과 카페를 발견하기 좋은 동네입니다.",
        "things": ["주택가 골목 걷기", "독립서점 찾기", "처음 보는 카페 들어가기"],
        "photo_query": "Yeonhui-dong Seoul",
        "food_query": "연희동 맛집", "cafe_query": "연희동 카페",
    },
    {
        "name": "후암동", "arrival": "후암시장", "lat": 37.5507, "lon": 126.9772,
        "category": ["언덕", "시장", "전망"],
        "intro": "서울역 뒤편의 언덕길과 오래된 시장, 남산 아래 풍경이 매력적인 동네입니다.",
        "things": ["후암시장 둘러보기", "언덕길 산책", "남산 방향 전망 찾기"],
        "photo_query": "Huam-dong Seoul",
        "food_query": "후암동 맛집", "cafe_query": "후암동 카페",
    },
    {
        "name": "신당동", "arrival": "신당역", "lat": 37.5657, "lon": 127.0194,
        "category": ["시장", "골목", "음식"],
        "intro": "중앙시장과 오래된 상가, 새로운 공간이 뒤섞인 서울 도심의 생활 여행지입니다.",
        "things": ["서울중앙시장 걷기", "오래된 가게 찾기", "골목 식당 한 곳 고르기"],
        "photo_query": "Sindang-dong Seoul Central Market",
        "food_query": "신당동 맛집", "cafe_query": "신당동 카페",
    },
    {
        "name": "창신동", "arrival": "창신역", "lat": 37.5795, "lon": 127.0122,
        "category": ["언덕", "봉제", "전망"],
        "intro": "봉제 골목과 언덕 위 주택가, 서울 도심 전망을 함께 볼 수 있는 동네입니다.",
        "things": ["봉제 골목 걷기", "전망대 방향 오르기", "골목 계단 사진 찍기"],
        "photo_query": "Changsin-dong Seoul",
        "food_query": "창신동 맛집", "cafe_query": "창신동 카페",
    },
    {
        "name": "부암동", "arrival": "부암동 주민센터", "lat": 37.5927, "lon": 126.9640,
        "category": ["산책", "미술", "산"],
        "intro": "인왕산 자락의 조용한 주택가와 미술관, 작은 카페가 어우러진 동네입니다.",
        "things": ["언덕 산책", "작은 미술관 찾기", "산자락 카페 쉬어가기"],
        "photo_query": "Buam-dong Seoul",
        "food_query": "부암동 맛집", "cafe_query": "부암동 카페",
    },
    {
        "name": "홍제동", "arrival": "홍제역", "lat": 37.5890, "lon": 126.9436,
        "category": ["하천", "시장", "동네"],
        "intro": "홍제천과 오래된 시장, 산 아래 생활 골목을 천천히 둘러보기 좋습니다.",
        "things": ["홍제천 걷기", "인왕시장 둘러보기", "동네 빵집 찾기"],
        "photo_query": "Hongjecheon Seoul",
        "food_query": "홍제역 맛집", "cafe_query": "홍제동 카페",
    },
    {
        "name": "중곡동", "arrival": "중곡역", "lat": 37.5658, "lon": 127.0841,
        "category": ["시장", "골목", "공원"],
        "intro": "관광지보다 생활 동네의 분위기를 느끼며 시장과 골목을 탐색하기 좋은 곳입니다.",
        "things": ["중곡제일시장 걷기", "작은 공원 찾기", "프랜차이즈 아닌 카페 고르기"],
        "photo_query": "Junggok-dong Seoul",
        "food_query": "중곡역 맛집", "cafe_query": "중곡동 카페",
    },
    {
        "name": "문래동", "arrival": "문래역", "lat": 37.5170, "lon": 126.8957,
        "category": ["공장", "예술", "골목"],
        "intro": "철공소 골목과 작업실, 작은 전시 공간이 섞인 독특한 서울 여행지입니다.",
        "things": ["철공소 골목 걷기", "벽화 찾기", "작은 전시 공간 들어가기"],
        "photo_query": "Mullae Art Village Seoul",
        "food_query": "문래동 맛집", "cafe_query": "문래동 카페",
    },
    {
        "name": "암사동", "arrival": "암사역", "lat": 37.5508, "lon": 127.1271,
        "category": ["시장", "한강", "역사"],
        "intro": "시장과 한강, 선사 유적이 가까워 생활과 역사를 함께 경험할 수 있습니다.",
        "things": ["암사시장 걷기", "한강 산책", "선사 유적 주변 둘러보기"],
        "photo_query": "Amsa-dong Prehistoric Settlement Seoul",
        "food_query": "암사역 맛집", "cafe_query": "암사동 카페",
    },
    {
        "name": "마천동", "arrival": "마천역", "lat": 37.4949, "lon": 127.1528,
        "category": ["시장", "산", "종점"],
        "intro": "지하철 종점과 남한산성 자락의 시장, 주택가를 탐색하는 재미가 있습니다.",
        "things": ["마천시장 걷기", "종점 주변 둘러보기", "산자락 방향 산책"],
        "photo_query": "Macheon-dong Seoul",
        "food_query": "마천역 맛집", "cafe_query": "마천동 카페",
    },
    {
        "name": "오류동", "arrival": "오류동역", "lat": 37.4944, "lon": 126.8448,
        "category": ["시장", "철길", "동네"],
        "intro": "철길 주변 시장과 오래된 주택가를 따라 서울 서남쪽의 생활 풍경을 볼 수 있습니다.",
        "things": ["오류시장 둘러보기", "철길 주변 걷기", "동네 빵집 찾기"],
        "photo_query": "Oryu-dong Seoul",
        "food_query": "오류동역 맛집", "cafe_query": "오류동 카페",
    },
]

MISSIONS = [
    "프랜차이즈가 아닌 가게 한 곳에 들어가기",
    "처음 보는 간판 사진 찍기",
    "시장이나 골목을 20분 이상 천천히 걷기",
    "지도 앱을 닫고 10분 동안 마음 가는 방향으로 걷기",
    "동네에서 가장 오래돼 보이는 식당 찾기",
    "작은 공원이나 쉼터 한 곳 발견하기",
]


def get_secret(name):
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    value = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def estimated_minutes(distance_km):
    return max(15, round(14 + distance_km * 4.2))


def clean_title(text):
    return html.unescape(text.replace("<b>", "").replace("</b>", ""))


def naver_map_url(query):
    return "https://map.naver.com/p/search/" + quote(query)


def google_transit_url(origin, destination):
    return "https://www.google.com/maps/dir/?" + urlencode({
        "api": "1", "origin": origin, "destination": destination, "travelmode": "transit"
    })


def make_vworld_map_url(api_key, domain, start_lat, start_lon, end_lat, end_lon):
    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    distance = haversine_km(start_lat, start_lon, end_lat, end_lon)
    zoom = 15 if distance < 3 else 13 if distance < 7 else 12 if distance < 15 else 11

    # 브이월드 공식 형식: label:문구|color:색상|point:경도 위도
    pairs = [
        ("service", "image"),
        ("request", "getmap"),
        ("version", "2.0"),
        ("key", api_key),
        ("domain", domain),
        ("format", "png"),
        ("errorformat", "json"),
        ("basemap", "GRAPHIC"),
        ("center", f"{center_lon},{center_lat}"),
        ("crs", "EPSG:4326"),
        ("zoom", str(zoom)),
        ("size", "800,520"),
        ("marker", f"label:출발|color:blue|point:{start_lon} {start_lat}"),
        ("marker", f"label:도착|color:red|point:{end_lon} {end_lat}"),
        ("route", f"style:dash|color:purple|width:4|point:{start_lon} {start_lat},{end_lon} {end_lat}"),
    ]
    return "https://api.vworld.kr/req/image?" + urlencode(pairs)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def vworld_geocode(address, api_key, domain):
    if not address.strip():
        return None, "주소를 입력해 주세요."
    if not api_key:
        return None, "VWORLD_API_KEY가 설정되지 않았습니다."

    base_url = "https://api.vworld.kr/req/address"
    common = {
        "service": "address",
        "request": "getCoord",
        "version": "2.0",
        "crs": "EPSG:4326",
        "address": address.strip(),
        "refine": "true",
        "simple": "false",
        "format": "json",
        "key": api_key,
        "domain": domain,
    }

    for address_type in ("road", "parcel"):
        params = dict(common)
        params["type"] = address_type
        try:
            response = requests.get(base_url, params=params, timeout=12)
            if response.status_code != 200:
                continue
            payload = response.json().get("response", {})
            if payload.get("status") != "OK":
                continue
            result = payload.get("result", {})
            point = result.get("point", {})
            x, y = point.get("x"), point.get("y")
            if x is None or y is None:
                continue
            refined = result.get("refined", {})
            name = refined.get("text") or address.strip()
            return {"name": name, "lat": float(y), "lon": float(x)}, ""
        except (requests.RequestException, ValueError, TypeError):
            continue

    return None, "주소를 찾지 못했습니다. 도로명 주소나 건물명을 더 구체적으로 입력해 주세요."


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def commons_image(search_term, fallback_term="Seoul street"):
    url = "https://commons.wikimedia.org/w/api.php"
    headers = {"User-Agent": "WhereToGoSeoul/1.0 educational-streamlit-app"}

    for term in (search_term, fallback_term):
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": term,
            "gsrnamespace": 6,
            "gsrlimit": 1,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": 900,
            "format": "json",
            "origin": "*",
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
            if not pages:
                continue
            page = next(iter(pages.values()))
            info = (page.get("imageinfo") or [{}])[0]
            image_url = info.get("thumburl") or info.get("url")
            if image_url:
                metadata = info.get("extmetadata", {})
                return {
                    "url": image_url,
                    "title": page.get("title", "Wikimedia Commons 이미지"),
                    "license": (metadata.get("LicenseShortName") or {}).get("value", ""),
                    "artist": clean_title((metadata.get("Artist") or {}).get("value", "")),
                }
        except requests.RequestException:
            continue
    return None


@st.cache_data(ttl=60 * 30, show_spinner=False)
def naver_local_search(query, client_id, client_secret):
    if not client_id or not client_secret:
        return [], "네이버 API 키가 설정되지 않았습니다."

    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": query, "display": 5, "start": 1, "sort": "comment"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return [], f"네이버 API 오류 {response.status_code}: {response.text[:200]}"
        results = []
        for item in response.json().get("items", []):
            name = clean_title(item.get("title", "이름 없음"))
            results.append({
                "name": name,
                "category": item.get("category", ""),
                "address": item.get("roadAddress") or item.get("address", ""),
                "url": item.get("link") or naver_map_url(name),
            })
        return (results, "") if results else ([], "검색 결과가 없습니다.")
    except requests.RequestException as exc:
        return [], f"네이버 API 연결 오류: {exc}"


def choose_three(items):
    if len(items) <= 3:
        return list(items)
    chosen, pool, weights = [], list(items), [5, 4, 3, 2, 1][:len(items)]
    while pool and len(chosen) < 3:
        index = random.choices(range(len(pool)), weights=weights, k=1)[0]
        chosen.append(pool.pop(index))
        weights.pop(index)
    return chosen


def show_three_places(items, kind, neighborhood):
    emoji = "🍽️" if kind == "식당" else "☕"
    fallback = "Korean food restaurant" if kind == "식당" else "Cafe coffee interior"
    for index, item in enumerate(items, start=1):
        st.markdown(f"### {emoji} {index}. {item['name']}")
        image = commons_image(f"{item['name']} {neighborhood} Seoul", fallback)
        if image:
            st.image(image["url"], use_container_width=True)
            credit = " · ".join(part for part in [image.get("artist"), image.get("license")] if part)
            if credit:
                st.caption(f"관련 공개 이미지: Wikimedia Commons · {credit}")
        else:
            st.caption("업체 대표 공개 이미지를 찾지 못했습니다.")
        if item.get("category"):
            st.write(item["category"])
        if item.get("address"):
            st.write(item["address"])
        st.link_button("네이버 지도에서 확인", item["url"], use_container_width=True)
        if index < len(items):
            st.divider()


st.title("🧭 어디갈까? 서울")
st.caption(f"앱 버전: {APP_VERSION}")
st.write("평소 갈 이유가 없었던 서울의 동네를 랜덤으로 발견하는 여행 앱입니다.")

vworld_api_key = get_secret("VWORLD_API_KEY")
vworld_domain = get_secret("VWORLD_DOMAIN") or "https://localhost"
naver_client_id = get_secret("NAVER_CLIENT_ID")
naver_client_secret = get_secret("NAVER_CLIENT_SECRET")

with st.sidebar:
    st.header("📍 출발지 설정")
    start_mode = st.radio("입력 방법", ["주요 장소 선택", "주소 직접 검색"])

    if start_mode == "주요 장소 선택":
        start_name = st.selectbox("출발 장소", list(START_POINTS.keys()))
        start_lat, start_lon = START_POINTS[start_name]
        start_ready = True
    else:
        address_query = st.text_input(
            "서울 주소·건물·역 이름",
            placeholder="예: 서울특별시 마포구 월드컵북로 400",
        )
        if st.button("🔎 출발지 검색", use_container_width=True):
            result, error = vworld_geocode(address_query, vworld_api_key, vworld_domain)
            st.session_state["custom_start"] = result
            st.session_state["custom_start_error"] = error

        custom_start = st.session_state.get("custom_start")
        custom_error = st.session_state.get("custom_start_error", "")
        if custom_start:
            start_name = custom_start["name"]
            start_lat = custom_start["lat"]
            start_lon = custom_start["lon"]
            start_ready = True
            st.success("출발지를 지정했습니다.")
            st.caption(start_name)
        else:
            start_name, start_lat, start_lon, start_ready = "", 0.0, 0.0, False
            if custom_error:
                st.error(custom_error)

    st.header("🎒 여행 조건")
    distance_style = st.select_slider(
        "얼마나 낯선 곳으로 갈까요?",
        options=["가까운 동네", "적당히 낯선 동네", "멀리 떠나는 느낌"],
        value="적당히 낯선 동네",
    )

if not start_ready:
    st.info("왼쪽에서 출발지를 검색하고 지정해 주세요.")
    st.stop()

distance_ranges = {"가까운 동네": (0, 6), "적당히 낯선 동네": (4, 13), "멀리 떠나는 느낌": (9, 30)}
min_km, max_km = distance_ranges[distance_style]

candidates = []
for place in PLACES:
    distance = haversine_km(start_lat, start_lon, place["lat"], place["lon"])
    if min_km <= distance <= max_km:
        candidate = dict(place)
        candidate["distance_km"] = distance
        candidate["estimated_minutes"] = estimated_minutes(distance)
        candidates.append(candidate)

condition_key = (round(start_lat, 5), round(start_lon, 5), distance_style)
if st.session_state.get("condition_key") != condition_key:
    st.session_state["condition_key"] = condition_key
    st.session_state["selected_place"] = None
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)

if st.button("🎲 오늘의 서울 동네 뽑기", type="primary", use_container_width=True, disabled=not candidates):
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)

if not candidates:
    st.warning("현재 출발지와 조건에 맞는 동네가 없습니다. 거리 조건을 바꿔보세요.")
    st.stop()

place = st.session_state.get("selected_place")
if not place:
    st.info("버튼을 눌러 오늘의 서울 동네를 뽑아보세요.")
    st.stop()

st.header(f"오늘의 서울 여행: {place['name']}")
st.caption(" · ".join(place["category"]))
st.write(place["intro"])

col1, col2, col3 = st.columns(3)
col1.metric("도착 기준", place["arrival"])
col2.metric("직선거리", f"{place['distance_km']:.1f}km")
col3.metric("이동시간 참고", f"약 {place['estimated_minutes']}분")

st.link_button(
    "🚌 실시간 대중교통 경로 보기",
    google_transit_url(start_name, place["arrival"]),
    type="primary",
    use_container_width=True,
)

st.subheader("🗺️ 브이월드 지도")
if not vworld_api_key:
    st.error("VWORLD_API_KEY가 설정되지 않았습니다.")
else:
    vworld_url = make_vworld_map_url(
        vworld_api_key, vworld_domain, start_lat, start_lon, place["lat"], place["lon"]
    )
    st.image(vworld_url, caption="🔵 출발 · 🔴 도착", use_container_width=True)
    st.caption(f"🔵 출발: {start_name}  →  🔴 도착: {place['arrival']}")
    with st.expander("지도 요청이 정상인지 확인"):
        st.link_button("브이월드 지도 원본 열기", vworld_url, use_container_width=True)
        st.code(vworld_url)

st.subheader("📸 이 동네에서 해볼 일")
area_image = commons_image(place["photo_query"], f"{place['name']} Seoul")
if area_image:
    st.image(area_image["url"], caption=f"{place['name']} 대표 공개 이미지", use_container_width=True)
    credit = " · ".join(part for part in [area_image.get("artist"), area_image.get("license")] if part)
    if credit:
        st.caption(f"Wikimedia Commons · {credit}")

for item in place["things"]:
    st.markdown(f"- {item}")
for mission in random.sample(MISSIONS, k=2):
    st.markdown(f"- 미션: **{mission}**")

st.subheader("🍽️ 오늘의 식당")
food_items, food_error = naver_local_search(place["food_query"], naver_client_id, naver_client_secret)
if food_error:
    st.error(food_error)
    st.link_button("네이버 지도에서 맛집 직접 검색", naver_map_url(place["food_query"]), use_container_width=True)
else:
    if "food_picks" not in st.session_state:
        st.session_state["food_picks"] = choose_three(food_items)
    show_three_places(st.session_state["food_picks"], "식당", place["name"])
    if st.button("🍴 식당 3곳 다시 뽑기", use_container_width=True):
        st.session_state["food_picks"] = choose_three(food_items)
        st.rerun()

st.subheader("☕ 오늘의 카페")
cafe_items, cafe_error = naver_local_search(place["cafe_query"], naver_client_id, naver_client_secret)
if cafe_error:
    st.error(cafe_error)
    st.link_button("네이버 지도에서 카페 직접 검색", naver_map_url(place["cafe_query"]), use_container_width=True)
else:
    if "cafe_picks" not in st.session_state:
        st.session_state["cafe_picks"] = choose_three(cafe_items)
    show_three_places(st.session_state["cafe_picks"], "카페", place["name"])
    if st.button("🥤 카페 3곳 다시 뽑기", use_container_width=True):
        st.session_state["cafe_picks"] = choose_three(cafe_items)
        st.rerun()

st.markdown("---")
if st.button("🔄 다른 서울 동네 뽑기", use_container_width=True):
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)
    st.rerun()

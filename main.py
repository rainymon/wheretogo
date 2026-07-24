import csv
import html
import io
import math
import random
import zipfile
from urllib.parse import quote, urlencode

import requests
import streamlit as st


APP_VERSION = "ALL-SEOUL-DONGS-NO-IMAGES-20260724"
ADMIN_DONG_ZIP_URL = (
    "https://github.com/pknujsp/Korea_Administrative_Neighborhood_List/"
    "raw/refs/heads/main/korea.zip"
)

st.set_page_config(
    page_title="어디갈까? 서울",
    page_icon="🧭",
    layout="wide",
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

EXCLUDED_BRANDS = {
    "스타벅스", "투썸플레이스", "이디야", "메가커피", "메가엠지씨커피",
    "컴포즈커피", "빽다방", "더벤티", "할리스", "엔제리너스", "폴바셋",
    "커피빈", "탐앤탐스", "파스쿠찌", "파리바게뜨", "파리바게트",
    "뚜레쥬르", "배스킨라빈스", "베스킨라빈스", "던킨", "설빙",
    "맥도날드", "롯데리아", "버거킹", "맘스터치", "써브웨이", "서브웨이",
    "KFC", "본죽", "한솥", "김가네", "역전우동", "홍콩반점",
}

MISSIONS = [
    "프랜차이즈가 아닌 가게 한 곳에 들어가기",
    "처음 보는 간판 사진 찍기",
    "시장이나 골목을 20분 이상 천천히 걷기",
    "지도 앱을 닫고 10분 동안 마음 가는 방향으로 걷기",
    "동네에서 가장 오래돼 보이는 식당 찾기",
    "작은 공원이나 쉼터 한 곳 발견하기",
    "만원 이하의 동네 음식을 먹어보기",
    "동네 이름이 적힌 표지판을 찾아보기",
]


def get_secret(name):
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def normalize_text(value):
    return "".join(ch for ch in value.lower() if ch.isalnum())


def is_excluded_brand(name):
    normalized = normalize_text(name)
    return any(normalize_text(brand) in normalized for brand in EXCLUDED_BRANDS)


def clean_title(text):
    return html.unescape(text.replace("<b>", "").replace("</b>", ""))


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    value = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def estimated_minutes(distance_km):
    return max(15, round(14 + distance_km * 4.2))


def naver_map_url(query):
    return "https://map.naver.com/p/search/" + quote(query)


def google_transit_url(origin, destination):
    return "https://www.google.com/maps/dir/?" + urlencode(
        {
            "api": "1",
            "origin": origin,
            "destination": destination,
            "travelmode": "transit",
        }
    )


@st.cache_data(ttl=60 * 60 * 24 * 7, show_spinner=False)
def load_seoul_admin_dongs():
    response = requests.get(
        ADMIN_DONG_ZIP_URL,
        headers={"User-Agent": "WhereToGoSeoul/1.0 educational-streamlit-app"},
        timeout=25,
    )
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("행정동 CSV 파일을 찾지 못했습니다.")

        raw = archive.read(csv_names[0])
        text = None
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise RuntimeError("행정동 CSV 인코딩을 읽지 못했습니다.")

    rows = csv.DictReader(io.StringIO(text))
    places = []
    seen = set()

    for row in rows:
        province = (row.get("province") or "").strip()
        if province != "서울특별시":
            continue

        gu = (row.get("city") or "").strip()
        dong = (row.get("district") or "").strip()
        code = (row.get("district_code") or "").strip()

        try:
            lat = float(row.get("latitude", ""))
            lon = float(row.get("longitude", ""))
        except (TypeError, ValueError):
            continue

        key = (gu, dong)
        if not gu or not dong or key in seen:
            continue
        seen.add(key)

        places.append(
            {
                "code": code,
                "name": dong,
                "gu": gu,
                "full_name": f"{gu} {dong}",
                "arrival": f"서울특별시 {gu} {dong}",
                "lat": lat,
                "lon": lon,
                "intro": f"서울 {gu}의 {dong}을 목적지로 삼아 골목과 생활 공간을 자유롭게 발견해 보세요.",
                "things": [
                    f"{dong} 중심 골목을 20분 이상 걸어보기",
                    "동네 시장이나 작은 상점 찾아보기",
                    "프랜차이즈가 아닌 식당 또는 카페 이용하기",
                ],
                "food_queries": [
                    f"{gu} {dong} 현지인 맛집",
                    f"{gu} {dong} 노포",
                    f"{gu} {dong} 동네 맛집",
                ],
                "cafe_queries": [
                    f"{gu} {dong} 개인카페",
                    f"{gu} {dong} 로스터리 카페",
                    f"{gu} {dong} 디저트 카페",
                ],
            }
        )

    if not places:
        raise RuntimeError("서울 행정동 자료가 비어 있습니다.")

    return sorted(places, key=lambda item: (item["gu"], item["name"]))


# 서울의 모든 행정동을 PLACES로 구성합니다.
try:
    PLACES = load_seoul_admin_dongs()
    PLACES_ERROR = ""
except Exception as exc:
    PLACES = []
    PLACES_ERROR = str(exc)


def make_vworld_map_url(api_key, domain, start_lat, start_lon, end_lat, end_lon):
    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    distance = haversine_km(start_lat, start_lon, end_lat, end_lon)
    zoom = 15 if distance < 3 else 13 if distance < 7 else 12 if distance < 15 else 11

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
        ("size", "900,520"),
        ("marker", f"label:출발|color:blue|point:{start_lon} {start_lat}"),
        ("marker", f"label:도착|color:red|point:{end_lon} {end_lat}"),
        (
            "route",
            f"style:dash|color:purple|width:4|point:{start_lon} {start_lat},{end_lon} {end_lat}",
        ),
    ]
    return "https://api.vworld.kr/req/image?" + urlencode(pairs)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def vworld_geocode(address, api_key, domain):
    if not address.strip():
        return None, "주소를 입력해 주세요."
    if not api_key:
        return None, "VWORLD_API_KEY가 설정되지 않았습니다."

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
            response = requests.get(
                "https://api.vworld.kr/req/address",
                params=params,
                timeout=12,
            )
            response.raise_for_status()
            payload = response.json().get("response", {})
            if payload.get("status") != "OK":
                continue
            result = payload.get("result", {})
            point = result.get("point", {})
            refined = result.get("refined", {})
            return {
                "name": refined.get("text") or address.strip(),
                "lat": float(point["y"]),
                "lon": float(point["x"]),
            }, ""
        except (requests.RequestException, ValueError, KeyError, TypeError):
            continue

    return None, "주소를 찾지 못했습니다. 도로명 주소나 건물명을 더 구체적으로 입력해 주세요."


@st.cache_data(ttl=60 * 30, show_spinner=False)
def naver_local_search(query, client_id, client_secret):
    if not client_id or not client_secret:
        return [], "네이버 API 키가 설정되지 않았습니다."

    try:
        response = requests.get(
            "https://openapi.naver.com/v1/search/local.json",
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            params={"query": query, "display": 5, "start": 1, "sort": "comment"},
            timeout=10,
        )
        if response.status_code != 200:
            return [], f"네이버 API 오류 {response.status_code}: {response.text[:160]}"

        results = []
        for item in response.json().get("items", []):
            name = clean_title(item.get("title", "이름 없음"))
            if is_excluded_brand(name):
                continue
            results.append(
                {
                    "name": name,
                    "category": item.get("category", ""),
                    "address": item.get("roadAddress") or item.get("address", ""),
                    "url": item.get("link") or naver_map_url(name),
                }
            )
        return results, ""
    except requests.RequestException as exc:
        return [], f"네이버 API 연결 오류: {exc}"


def merge_unique_places(place_lists):
    merged = []
    seen = set()
    for items in place_lists:
        for item in items:
            key = normalize_text(item["name"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def search_multiple_queries(queries, client_id, client_secret):
    groups = []
    errors = []
    for query in queries:
        items, error = naver_local_search(query, client_id, client_secret)
        groups.append(items)
        if error:
            errors.append(error)
    merged = merge_unique_places(groups)
    return merged, errors[0] if not merged and errors else ""


def choose_three(items):
    if len(items) <= 3:
        return list(items)
    weights = list(range(len(items), 0, -1))
    pool = list(items)
    picks = []
    while pool and len(picks) < 3:
        idx = random.choices(range(len(pool)), weights=weights, k=1)[0]
        picks.append(pool.pop(idx))
        weights.pop(idx)
    return picks


def show_place_card(item, index):
    with st.container(border=True):
        title_col, link_col = st.columns([8, 1])
        with title_col:
            st.markdown(f"**{index}. {item['name']}**")
        with link_col:
            st.link_button("🔗", item["url"], help="네이버 지도에서 확인")
        if item.get("category"):
            st.caption(item["category"])
        if item.get("address"):
            st.write(item["address"])


st.title("🧭 어디갈까? 서울")
st.caption(f"앱 버전: {APP_VERSION}")
st.write("서울의 모든 행정동 중 평소 갈 이유가 없었던 동네를 랜덤으로 발견해 보세요.")

if PLACES_ERROR:
    st.error(f"서울 행정동 자료를 불러오지 못했습니다: {PLACES_ERROR}")
    st.stop()

vworld_api_key = get_secret("VWORLD_API_KEY")
vworld_domain = get_secret("VWORLD_DOMAIN") or "https://localhost"
naver_client_id = get_secret("NAVER_CLIENT_ID")
naver_client_secret = get_secret("NAVER_CLIENT_SECRET")

with st.sidebar:
    st.header("출발지 설정")
    start_mode = st.radio(
        "입력 방법",
        ["주요 장소에서 선택", "주소·건물명 직접 검색"],
    )

    if start_mode == "주요 장소에서 선택":
        start_name = st.selectbox("출발 장소", list(START_POINTS.keys()))
        start_lat, start_lon = START_POINTS[start_name]
        start_ready = True
    else:
        address_input = st.text_input(
            "서울 주소 또는 건물명",
            placeholder="예: 서울시청, 성수역, 마포구 월드컵북로 400",
        )
        if st.button("🔎 출발지 검색", use_container_width=True):
            result, error = vworld_geocode(
                address_input,
                vworld_api_key,
                vworld_domain,
            )
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
            start_name = ""
            start_lat = 0.0
            start_lon = 0.0
            start_ready = False
            if custom_error:
                st.error(custom_error)

    st.markdown("---")
    distance_style = st.select_slider(
        "얼마나 낯선 곳으로 갈까요?",
        options=["가까운 동네", "적당히 낯선 동네", "멀리 떠나는 느낌"],
        value="적당히 낯선 동네",
    )

if not start_ready:
    st.info("왼쪽에서 출발지를 검색해 지정해 주세요.")
    st.stop()

distance_ranges = {
    "가까운 동네": (1.5, 6),
    "적당히 낯선 동네": (4, 13),
    "멀리 떠나는 느낌": (9, 30),
}
min_km, max_km = distance_ranges[distance_style]

candidates = []
for item in PLACES:
    distance = haversine_km(start_lat, start_lon, item["lat"], item["lon"])
    if min_km <= distance <= max_km:
        candidate = dict(item)
        candidate["distance_km"] = distance
        candidate["estimated_minutes"] = estimated_minutes(distance)
        candidates.append(candidate)

condition_key = (
    round(start_lat, 4),
    round(start_lon, 4),
    distance_style,
)
if st.session_state.get("condition_key") != condition_key:
    st.session_state["condition_key"] = condition_key
    st.session_state["selected_place"] = None
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)

header_col, button_col = st.columns([3, 1])
with header_col:
    st.info(f"현재 조건에 맞는 행정동: **{len(candidates)}곳** / 전체 **{len(PLACES)}곳**")
with button_col:
    draw_clicked = st.button(
        "🎲 오늘의 동네 뽑기",
        type="primary",
        use_container_width=True,
        disabled=not candidates,
    )

if draw_clicked:
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)

if not candidates:
    st.warning("현재 조건에 맞는 행정동이 없습니다. 거리 조건을 바꿔 주세요.")
    st.stop()

place = st.session_state.get("selected_place")
if not place:
    st.info("버튼을 눌러 오늘의 서울 행정동을 뽑아보세요.")
    st.stop()

st.header(f"오늘의 서울 여행: {place['gu']} {place['name']}")
st.write(place["intro"])

metric1, metric2, metric3 = st.columns(3)
metric1.metric("행정동", place["name"])
metric2.metric("직선거리", f"{place['distance_km']:.1f}km")
metric3.metric("이동시간 참고", f"약 {place['estimated_minutes']}분")

st.link_button(
    "🚌 실시간 대중교통 경로 보기",
    google_transit_url(start_name, place["arrival"]),
    type="primary",
    use_container_width=True,
)

st.subheader("브이월드 지도")
if not vworld_api_key:
    st.error("VWORLD_API_KEY가 설정되지 않았습니다.")
else:
    map_url = make_vworld_map_url(
        vworld_api_key,
        vworld_domain,
        start_lat,
        start_lon,
        place["lat"],
        place["lon"],
    )
    st.image(
        map_url,
        caption="브이월드 지도 · 파란색은 출발, 빨간색은 도착",
        use_container_width=True,
    )

st.subheader("이 동네에서 해볼 일")
for thing in place["things"]:
    st.markdown(f"- {thing}")
for mission in random.sample(MISSIONS, k=2):
    st.markdown(f"- 오늘의 미션: **{mission}**")

food_items, food_error = search_multiple_queries(
    place["food_queries"],
    naver_client_id,
    naver_client_secret,
)
cafe_items, cafe_error = search_multiple_queries(
    place["cafe_queries"],
    naver_client_id,
    naver_client_secret,
)

if "food_picks" not in st.session_state:
    st.session_state["food_picks"] = choose_three(food_items)
if "cafe_picks" not in st.session_state:
    st.session_state["cafe_picks"] = choose_three(cafe_items)

restaurant_col, cafe_col = st.columns(2, gap="large")

with restaurant_col:
    st.subheader("🍚 오늘의 식당")
    if food_error:
        st.error(food_error)
    elif not st.session_state["food_picks"]:
        st.info("조건에 맞는 식당을 찾지 못했습니다.")
    else:
        for index, item in enumerate(st.session_state["food_picks"], start=1):
            show_place_card(item, index)
        if st.button("🔄 식당 3곳 다시 뽑기", use_container_width=True):
            st.session_state["food_picks"] = choose_three(food_items)
            st.rerun()

with cafe_col:
    st.subheader("☕ 오늘의 카페")
    if cafe_error:
        st.error(cafe_error)
    elif not st.session_state["cafe_picks"]:
        st.info("조건에 맞는 카페를 찾지 못했습니다.")
    else:
        for index, item in enumerate(st.session_state["cafe_picks"], start=1):
            show_place_card(item, index)
        if st.button("🔄 카페 3곳 다시 뽑기", use_container_width=True):
            st.session_state["cafe_picks"] = choose_three(cafe_items)
            st.rerun()

st.markdown("---")
if st.button("🎲 다른 서울 행정동 뽑기", use_container_width=True):
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)
    st.rerun()

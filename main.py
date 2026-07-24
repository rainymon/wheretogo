import html
import math
import random
from urllib.parse import quote, urlencode

import requests
import streamlit as st


st.set_page_config(
    page_title="어디갈까? 서울",
    page_icon="🧭",
    layout="centered",
)

# ------------------------------------------------------------
# 기본 데이터
# ------------------------------------------------------------
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
        "name": "망원동",
        "arrival": "망원역",
        "lat": 37.5561,
        "lon": 126.9100,
        "category": ["시장", "골목", "한강"],
        "intro": "시장과 낮은 골목, 한강 산책을 한 번에 즐길 수 있는 생활형 여행지입니다.",
        "things": ["망원시장 한 바퀴", "골목 산책", "망원한강공원까지 걷기"],
        "food_query": "망원동 맛집",
        "cafe_query": "망원동 카페",
    },
    {
        "name": "연희동",
        "arrival": "연희동 주민센터 인근",
        "lat": 37.5687,
        "lon": 126.9304,
        "category": ["골목", "카페", "책"],
        "intro": "조용한 주택가 골목과 작은 식당, 독립서점과 카페를 발견하기 좋은 동네입니다.",
        "things": ["주택가 골목 걷기", "독립서점 찾기", "처음 보는 카페 들어가기"],
        "food_query": "연희동 맛집",
        "cafe_query": "연희동 카페",
    },
    {
        "name": "염리동",
        "arrival": "대흥역",
        "lat": 37.5472,
        "lon": 126.9457,
        "category": ["골목", "산책", "동네"],
        "intro": "오래된 주택가와 새로 생긴 공간이 섞여 있어 천천히 걸으며 변화를 관찰하기 좋습니다.",
        "things": ["골목 끝까지 걸어보기", "오래된 간판 찾기", "동네 공원 쉬어가기"],
        "food_query": "대흥역 맛집",
        "cafe_query": "염리동 카페",
    },
    {
        "name": "후암동",
        "arrival": "후암시장 인근",
        "lat": 37.5507,
        "lon": 126.9772,
        "category": ["언덕", "시장", "전망"],
        "intro": "서울역 뒤편의 언덕길과 오래된 시장, 남산 아래 풍경이 매력적인 동네입니다.",
        "things": ["후암시장 둘러보기", "언덕길 산책", "남산 방향 전망 찾기"],
        "food_query": "후암동 맛집",
        "cafe_query": "후암동 카페",
    },
    {
        "name": "해방촌",
        "arrival": "용산02 마을버스 해방촌 정류장",
        "lat": 37.5424,
        "lon": 126.9870,
        "category": ["언덕", "전망", "다문화"],
        "intro": "가파른 골목과 다양한 음식점, 남산 아래 전망이 어우러진 개성 강한 동네입니다.",
        "things": ["신흥시장 걷기", "전망 좋은 골목 찾기", "낯선 나라 음식 먹기"],
        "food_query": "해방촌 맛집",
        "cafe_query": "해방촌 카페",
    },
    {
        "name": "신당동",
        "arrival": "신당역",
        "lat": 37.5657,
        "lon": 127.0194,
        "category": ["시장", "골목", "음식"],
        "intro": "중앙시장과 오래된 상가, 새로운 공간이 뒤섞인 서울 도심의 생활 여행지입니다.",
        "things": ["서울중앙시장 걷기", "오래된 가게 찾기", "골목 식당 한 곳 고르기"],
        "food_query": "신당동 맛집",
        "cafe_query": "신당동 카페",
    },
    {
        "name": "황학동",
        "arrival": "신당역 또는 동묘앞역",
        "lat": 37.5703,
        "lon": 127.0214,
        "category": ["벼룩시장", "골목", "구제"],
        "intro": "중고 물건과 오래된 상점이 모여 있어 예상하지 못한 물건을 구경하는 재미가 있습니다.",
        "things": ["벼룩시장 구경", "만원 이하 물건 찾기", "오래된 간판 사진 찍기"],
        "food_query": "황학동 맛집",
        "cafe_query": "황학동 카페",
    },
    {
        "name": "창신동",
        "arrival": "창신역",
        "lat": 37.5795,
        "lon": 127.0122,
        "category": ["언덕", "봉제", "전망"],
        "intro": "봉제 골목과 언덕 위 주택가, 서울 도심 전망을 함께 볼 수 있는 동네입니다.",
        "things": ["봉제 골목 걷기", "전망대 방향 오르기", "골목 계단 사진 찍기"],
        "food_query": "창신동 맛집",
        "cafe_query": "창신동 카페",
    },
    {
        "name": "부암동",
        "arrival": "부암동 주민센터 인근",
        "lat": 37.5927,
        "lon": 126.9640,
        "category": ["산책", "미술", "산"],
        "intro": "인왕산 자락의 조용한 주택가와 미술관, 작은 카페가 어우러진 동네입니다.",
        "things": ["언덕 산책", "작은 미술관 찾기", "산자락 카페 쉬어가기"],
        "food_query": "부암동 맛집",
        "cafe_query": "부암동 카페",
    },
    {
        "name": "홍제동",
        "arrival": "홍제역",
        "lat": 37.5890,
        "lon": 126.9436,
        "category": ["하천", "시장", "동네"],
        "intro": "홍제천과 오래된 시장, 산 아래 생활 골목을 천천히 둘러보기 좋습니다.",
        "things": ["홍제천 걷기", "인왕시장 둘러보기", "동네 빵집 찾기"],
        "food_query": "홍제역 맛집",
        "cafe_query": "홍제동 카페",
    },
    {
        "name": "정릉동",
        "arrival": "정릉시장 인근",
        "lat": 37.6067,
        "lon": 127.0101,
        "category": ["시장", "산", "골목"],
        "intro": "북한산 자락의 시장과 골목이 이어지는 서울 북쪽의 생활 여행지입니다.",
        "things": ["정릉시장 둘러보기", "산자락 방향 걷기", "동네 분식 먹기"],
        "food_query": "정릉시장 맛집",
        "cafe_query": "정릉동 카페",
    },
    {
        "name": "성북동",
        "arrival": "한성대입구역",
        "lat": 37.5946,
        "lon": 126.9961,
        "category": ["역사", "산책", "주택가"],
        "intro": "성곽과 오래된 주택, 작은 박물관이 이어지는 차분한 산책 동네입니다.",
        "things": ["성북동 골목 걷기", "성곽 방향 산책", "작은 박물관 찾기"],
        "food_query": "성북동 맛집",
        "cafe_query": "성북동 카페",
    },
    {
        "name": "중곡동",
        "arrival": "중곡역",
        "lat": 37.5658,
        "lon": 127.0841,
        "category": ["시장", "골목", "공원"],
        "intro": "관광지보다 생활 동네의 분위기를 느끼며 시장과 골목을 탐색하기 좋은 곳입니다.",
        "things": ["중곡제일시장 걷기", "작은 공원 찾기", "프랜차이즈 아닌 카페 고르기"],
        "food_query": "중곡역 맛집",
        "cafe_query": "중곡동 카페",
    },
    {
        "name": "자양동",
        "arrival": "뚝섬유원지역",
        "lat": 37.5315,
        "lon": 127.0667,
        "category": ["한강", "시장", "골목"],
        "intro": "한강과 시장, 주택가 골목이 가까워 여러 분위기를 한 번에 경험할 수 있습니다.",
        "things": ["자양시장 둘러보기", "한강까지 걷기", "골목 식당 고르기"],
        "food_query": "자양동 맛집",
        "cafe_query": "자양동 카페",
    },
    {
        "name": "면목동",
        "arrival": "사가정역",
        "lat": 37.5809,
        "lon": 127.0885,
        "category": ["시장", "하천", "동네"],
        "intro": "전통시장과 중랑천, 주거 골목이 이어져 서울 동북부의 생활 풍경을 보기 좋습니다.",
        "things": ["사가정시장 걷기", "중랑천 산책", "동네 반찬가게 구경"],
        "food_query": "사가정역 맛집",
        "cafe_query": "면목동 카페",
    },
    {
        "name": "방학동",
        "arrival": "방학역",
        "lat": 37.6675,
        "lon": 127.0443,
        "category": ["시장", "주택가", "산"],
        "intro": "도봉산 아래 시장과 주택가가 이어지는 서울 북쪽의 낯선 일상 여행지입니다.",
        "things": ["도깨비시장 둘러보기", "산 방향으로 걷기", "처음 보는 식당 들어가기"],
        "food_query": "방학역 맛집",
        "cafe_query": "방학동 카페",
    },
    {
        "name": "불광동",
        "arrival": "불광역",
        "lat": 37.6100,
        "lon": 126.9298,
        "category": ["시장", "산", "골목"],
        "intro": "연신내와 북한산 사이의 시장과 생활 골목을 경험하기 좋은 지역입니다.",
        "things": ["불광시장 걷기", "북한산 방향 산책", "오래된 분식집 찾기"],
        "food_query": "불광역 맛집",
        "cafe_query": "불광동 카페",
    },
    {
        "name": "독산동",
        "arrival": "독산역",
        "lat": 37.4661,
        "lon": 126.8895,
        "category": ["시장", "공장지대", "골목"],
        "intro": "산업지역과 주거 골목, 시장이 섞여 있어 서울 서남부의 다른 표정을 볼 수 있습니다.",
        "things": ["우시장 주변 걷기", "오래된 상가 찾기", "동네 식당 한 곳 고르기"],
        "food_query": "독산동 맛집",
        "cafe_query": "독산동 카페",
    },
    {
        "name": "문래동",
        "arrival": "문래역",
        "lat": 37.5170,
        "lon": 126.8957,
        "category": ["공장", "예술", "골목"],
        "intro": "철공소 골목과 작업실, 작은 전시 공간이 섞인 독특한 서울 여행지입니다.",
        "things": ["철공소 골목 걷기", "벽화 찾기", "작은 전시 공간 들어가기"],
        "food_query": "문래동 맛집",
        "cafe_query": "문래동 카페",
    },
    {
        "name": "양평동",
        "arrival": "선유도역",
        "lat": 37.5387,
        "lon": 126.8935,
        "category": ["한강", "산책", "공장"],
        "intro": "낮은 공장 지대와 한강 산책로, 선유도공원이 가까운 의외의 산책 동네입니다.",
        "things": ["양평동 골목 걷기", "선유도공원 이동", "한강 노을 보기"],
        "food_query": "양평동 맛집",
        "cafe_query": "양평동 카페",
    },
    {
        "name": "오류동",
        "arrival": "오류동역",
        "lat": 37.4944,
        "lon": 126.8448,
        "category": ["시장", "철길", "동네"],
        "intro": "철길 주변 시장과 오래된 주택가를 따라 서울 서남쪽의 생활 풍경을 볼 수 있습니다.",
        "things": ["오류시장 둘러보기", "철길 주변 걷기", "동네 빵집 찾기"],
        "food_query": "오류동역 맛집",
        "cafe_query": "오류동 카페",
    },
    {
        "name": "암사동",
        "arrival": "암사역",
        "lat": 37.5508,
        "lon": 127.1271,
        "category": ["시장", "한강", "역사"],
        "intro": "시장과 한강, 선사 유적이 가까워 생활과 역사를 함께 경험할 수 있습니다.",
        "things": ["암사시장 걷기", "한강 산책", "선사 유적 주변 둘러보기"],
        "food_query": "암사역 맛집",
        "cafe_query": "암사동 카페",
    },
    {
        "name": "천호동",
        "arrival": "천호역",
        "lat": 37.5387,
        "lon": 127.1238,
        "category": ["시장", "한강", "골목"],
        "intro": "큰 시장과 로데오 골목, 한강공원이 가까워 활기찬 동네 여행을 즐길 수 있습니다.",
        "things": ["천호시장 둘러보기", "골목 식당 찾기", "광나루 한강공원 걷기"],
        "food_query": "천호동 맛집",
        "cafe_query": "천호동 카페",
    },
    {
        "name": "마천동",
        "arrival": "마천역",
        "lat": 37.4949,
        "lon": 127.1528,
        "category": ["시장", "산", "종점"],
        "intro": "지하철 종점과 남한산성 자락의 시장, 주택가를 탐색하는 재미가 있습니다.",
        "things": ["마천시장 걷기", "종점 주변 둘러보기", "산자락 방향 산책"],
        "food_query": "마천역 맛집",
        "cafe_query": "마천동 카페",
    },
    {
        "name": "세곡동",
        "arrival": "세곡동사거리",
        "lat": 37.4666,
        "lon": 127.1067,
        "category": ["천변", "신도시", "산책"],
        "intro": "서울 남동쪽 끝의 탄천과 새 주거지, 낮은 산책길을 발견할 수 있는 지역입니다.",
        "things": ["탄천 방향 걷기", "동네 공원 찾기", "주택가 카페 들어가기"],
        "food_query": "세곡동 맛집",
        "cafe_query": "세곡동 카페",
    },
]

MISSIONS = [
    "프랜차이즈가 아닌 가게 한 곳에 들어가기",
    "처음 보는 간판 사진 찍기",
    "시장이나 골목을 20분 이상 천천히 걷기",
    "지도 앱을 닫고 10분 동안 마음 가는 방향으로 걷기",
    "동네에서 가장 오래돼 보이는 식당 찾기",
    "작은 공원이나 쉼터 한 곳 발견하기",
    "만원 이하의 동네 음식을 먹어보기",
    "오늘의 색을 하나 정하고 같은 색 풍경 세 장 찍기",
]


# ------------------------------------------------------------
# 공통 함수
# ------------------------------------------------------------
def get_secret(name):
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


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
    # 실시간 경로가 아닌 서울 시내 대중교통 참고값
    return max(15, round(14 + distance_km * 4.2))


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def geocode_seoul(query):
    search_text = query.strip()
    if not search_text:
        return None

    if "서울" not in search_text:
        search_text = f"서울 {search_text}"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": search_text,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "kr",
        "accept-language": "ko",
    }
    headers = {
        "User-Agent": "WhereToGoSeoul/1.0 educational-streamlit-app"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None

        row = rows[0]
        lat = float(row["lat"])
        lon = float(row["lon"])

        # 서울 주변의 엉뚱한 결과를 줄이기 위한 범위 검사
        if not (37.40 <= lat <= 37.72 and 126.76 <= lon <= 127.20):
            return None

        return {
            "name": row.get("display_name", search_text),
            "lat": lat,
            "lon": lon,
        }
    except (requests.RequestException, ValueError, KeyError):
        return None


def clean_title(text):
    return html.unescape(text.replace("<b>", "").replace("</b>", ""))


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


@st.cache_data(ttl=60 * 30, show_spinner=False)
def naver_local_search(query, client_id, client_secret):
    if not client_id or not client_secret:
        return []

    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": 5,
        "start": 1,
        "sort": "comment",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=8,
        )
        response.raise_for_status()

        results = []
        for item in response.json().get("items", []):
            name = clean_title(item.get("title", "이름 없음"))
            results.append(
                {
                    "name": name,
                    "category": item.get("category", ""),
                    "address": item.get("roadAddress") or item.get("address", ""),
                    "url": item.get("link") or naver_map_url(name),
                }
            )
        return results
    except requests.RequestException:
        return []


def weighted_pick(items):
    if not items:
        return None
    weights = [5, 4, 3, 2, 1][: len(items)]
    return random.choices(items, weights=weights, k=1)[0]


def show_business(place, label):
    if not place:
        st.info(f"{label} 검색 결과가 없습니다.")
        return

    st.markdown(f"### {place['name']}")
    if place.get("category"):
        st.write(place["category"])
    if place.get("address"):
        st.write(place["address"])
    st.link_button(
        "네이버 지도에서 확인",
        place["url"],
        use_container_width=True,
    )


# ------------------------------------------------------------
# 화면
# ------------------------------------------------------------
st.title("🧭 어디갈까? 서울")
st.write(
    "유명 관광지보다 평소 갈 이유가 없었던 서울의 동네를 발견하는 랜덤 여행 앱입니다."
)

with st.sidebar:
    st.header("출발지 설정")

    start_mode = st.radio(
        "출발지 입력 방법",
        ["주요 장소에서 선택", "주소·건물·역 이름 검색"],
    )

    if start_mode == "주요 장소에서 선택":
        selected_start = st.selectbox("출발지", list(START_POINTS.keys()))
        start_name = selected_start
        start_lat, start_lon = START_POINTS[selected_start]
        start_ready = True
    else:
        custom_query = st.text_input(
            "출발지 검색",
            placeholder="예: 서울시청, 성수역, 마포구 월드컵북로 400",
        )
        search_clicked = st.button(
            "주소 찾기",
            use_container_width=True,
        )

        if search_clicked:
            result = geocode_seoul(custom_query)
            st.session_state["custom_start"] = result

        custom_start = st.session_state.get("custom_start")
        if custom_start:
            start_name = custom_start["name"]
            start_lat = custom_start["lat"]
            start_lon = custom_start["lon"]
            start_ready = True
            st.success("출발지를 찾았습니다.")
            st.caption(start_name)
        else:
            start_name = ""
            start_lat = 0.0
            start_lon = 0.0
            start_ready = False

    st.markdown("---")
    st.header("여행 조건")

    distance_style = st.select_slider(
        "얼마나 낯선 곳으로 갈까요?",
        options=["가까운 동네", "적당히 낯선 동네", "멀리 떠나는 느낌"],
        value="적당히 낯선 동네",
    )

    all_categories = sorted(
        {category for place in PLACES for category in place["category"]}
    )
    categories = st.multiselect(
        "관심 분위기",
        all_categories,
        placeholder="선택하지 않으면 전체",
    )

    avoid_same_area = st.checkbox(
        "출발지와 너무 가까운 장소 제외",
        value=True,
    )

naver_client_id = get_secret("NAVER_CLIENT_ID")
naver_client_secret = get_secret("NAVER_CLIENT_SECRET")

if not start_ready:
    st.info("왼쪽에서 출발지를 검색해 주세요.")
    st.stop()

distance_ranges = {
    "가까운 동네": (0, 6),
    "적당히 낯선 동네": (4, 13),
    "멀리 떠나는 느낌": (9, 30),
}
min_km, max_km = distance_ranges[distance_style]

candidates = []
for place in PLACES:
    distance = haversine_km(
        start_lat,
        start_lon,
        place["lat"],
        place["lon"],
    )

    if avoid_same_area and distance < 1.8:
        continue
    if not (min_km <= distance <= max_km):
        continue
    if categories and not any(
        category in place["category"] for category in categories
    ):
        continue

    candidate = dict(place)
    candidate["distance_km"] = distance
    candidate["estimated_minutes"] = estimated_minutes(distance)
    candidates.append(candidate)

condition_key = (
    round(start_lat, 4),
    round(start_lon, 4),
    distance_style,
    tuple(sorted(categories)),
    avoid_same_area,
)

if st.session_state.get("condition_key") != condition_key:
    st.session_state["condition_key"] = condition_key
    st.session_state["selected_place"] = None
    st.session_state.pop("food_pick", None)
    st.session_state.pop("cafe_pick", None)

top_left, top_right = st.columns([2, 1])
with top_left:
    st.info(f"현재 조건에 맞는 서울 동네: **{len(candidates)}곳**")
with top_right:
    draw_clicked = st.button(
        "🎲 오늘의 동네 뽑기",
        type="primary",
        use_container_width=True,
        disabled=not candidates,
    )

if draw_clicked:
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_pick", None)
    st.session_state.pop("cafe_pick", None)

if not candidates:
    st.warning("현재 조건에 맞는 동네가 없습니다. 거리 또는 분위기 조건을 바꿔보세요.")
    st.stop()

place = st.session_state.get("selected_place")
if not place:
    st.subheader("오늘은 서울 어디로 가볼까요?")
    st.write("조건을 고른 뒤 **오늘의 동네 뽑기**를 눌러보세요.")
    st.stop()

st.markdown("---")
st.header(f"오늘의 서울 여행: {place['name']}")
st.caption(" · ".join(place["category"]))

metric1, metric2, metric3 = st.columns(3)
metric1.metric("도착 기준", place["arrival"])
metric2.metric("직선거리", f"{place['distance_km']:.1f}km")
metric3.metric("이동시간 참고", f"약 {place['estimated_minutes']}분")

st.write(place["intro"])

st.subheader("가는 방법 확인")
st.link_button(
    "실시간 대중교통 경로 보기",
    google_transit_url(start_name, place["arrival"]),
    type="primary",
    use_container_width=True,
)
st.caption(
    "이동시간은 직선거리를 활용한 참고값입니다. 실제 지하철·버스 경로와 시간은 위 버튼에서 확인하세요."
)

st.subheader("지도")
st.map(
    [
        {"lat": start_lat, "lon": start_lon},
        {"lat": place["lat"], "lon": place["lon"]},
    ],
    latitude="lat",
    longitude="lon",
    zoom=11,
    use_container_width=True,
)

map_col1, map_col2 = st.columns(2)
map_col1.link_button(
    "네이버 지도에서 동네 보기",
    naver_map_url(place["name"]),
    use_container_width=True,
)
map_col2.link_button(
    "네이버 지도에서 도착 지점 보기",
    naver_map_url(place["arrival"]),
    use_container_width=True,
)

st.subheader("이 동네에서 해볼 일")
for item in place["things"]:
    st.markdown(f"- {item}")

random_missions = random.sample(MISSIONS, k=2)
for item in random_missions:
    st.markdown(f"- 미션: **{item}**")

st.markdown("---")
st.subheader("동네 맛집과 카페")

if naver_client_id and naver_client_secret:
    food_items = naver_local_search(
        place["food_query"],
        naver_client_id,
        naver_client_secret,
    )
    cafe_items = naver_local_search(
        place["cafe_query"],
        naver_client_id,
        naver_client_secret,
    )

    if "food_pick" not in st.session_state:
        st.session_state["food_pick"] = weighted_pick(food_items)
    if "cafe_pick" not in st.session_state:
        st.session_state["cafe_pick"] = weighted_pick(cafe_items)

    food_tab, cafe_tab = st.tabs(["🍚 오늘의 식당", "☕ 오늘의 카페"])

    with food_tab:
        show_business(st.session_state.get("food_pick"), "식당")
        if st.button("식당 다시 뽑기", use_container_width=True):
            st.session_state["food_pick"] = weighted_pick(food_items)
            st.rerun()

    with cafe_tab:
        show_business(st.session_state.get("cafe_pick"), "카페")
        if st.button("카페 다시 뽑기", use_container_width=True):
            st.session_state["cafe_pick"] = weighted_pick(cafe_items)
            st.rerun()
else:
    st.write("네이버 지도에서 이 동네의 식당과 카페를 바로 찾아볼 수 있습니다.")
    search_col1, search_col2 = st.columns(2)
    search_col1.link_button(
        "맛집 검색",
        naver_map_url(place["food_query"]),
        use_container_width=True,
    )
    search_col2.link_button(
        "카페 검색",
        naver_map_url(place["cafe_query"]),
        use_container_width=True,
    )

st.markdown("---")
if st.button("🔄 다른 서울 동네 뽑기", use_container_width=True):
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_pick", None)
    st.session_state.pop("cafe_pick", None)
    st.rerun()

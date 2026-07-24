import csv
import html
import io
import math
import random
import re
import zipfile
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
import streamlit as st


ADMIN_DONG_ZIP_URL = (
    "https://github.com/pknujsp/Korea_Administrative_Neighborhood_List/"
    "raw/refs/heads/main/korea.zip"
)

DATA_DIR = Path(__file__).parent / "data"
MARKET_DATA_PATH = DATA_DIR / "seoul_markets.tsv"
HERITAGE_DATA_PATH = DATA_DIR / "seoul_heritage.tsv"
CULTURE_DATA_PATH = DATA_DIR / "seoul_culture.tsv"
PARK_DATA_PATH = DATA_DIR / "seoul_parks.tsv"

st.set_page_config(
    page_title="서울마실",
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
                "intro": f"서울 {gu}의 {dong}을 목적지로 삼아 이 동네에 실제로 있는 장소와 생활 문화를 발견해 보세요.",
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



def normalize_dong_stem(value):
    value = re.sub(r"서울특별시|서울시|서울", "", str(value))
    value = re.sub(r"제(?=\d)", "", value)
    value = re.sub(r"\d+", "", value)
    value = value.replace("동", "").replace("가", "")
    return normalize_text(value)


def decode_data_file(path):
    """업로드 방식과 관계없이 텍스트 데이터 파일을 최대한 안전하게 해석한다."""
    raw = path.read_bytes()
    if not raw:
        return ""

    # BOM이 있으면 해당 인코딩을 가장 먼저 사용한다.
    if raw.startswith(b"\xef\xbb\xbf"):
        candidates = ("utf-8-sig", "utf-8", "cp949", "euc-kr", "utf-16")
    elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        candidates = ("utf-16", "utf-8-sig", "cp949", "euc-kr")
    else:
        candidates = ("utf-8-sig", "utf-8", "cp949", "euc-kr", "utf-16-le", "utf-16-be")

    for encoding in candidates:
        try:
            text = raw.decode(encoding)
            # 잘못된 UTF-16 해석은 NUL 문자가 과도하게 생기므로 제외한다.
            if text and text.count("\x00") > max(2, len(text) // 20):
                continue
            return text.lstrip("\ufeff").replace("\x00", "")
        except (UnicodeDecodeError, LookupError):
            continue

    # 마지막 안전장치: 앱 전체가 중단되지 않도록 깨진 바이트만 치환한다.
    return raw.decode("utf-8", errors="replace").lstrip("\ufeff").replace("\x00", "")


def detect_delimiter(text):
    """첫 번째 유효 행을 보고 탭을 우선으로 구분자를 판단한다."""
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if "\t" in first_line:
        return "\t"
    if "," in first_line:
        return ","
    if ";" in first_line:
        return ";"
    return "\t"


@st.cache_data(show_spinner=False)
def load_seoul_markets():
    if not MARKET_DATA_PATH.exists():
        return []

    text = decode_data_file(MARKET_DATA_PATH)
    delimiter = detect_delimiter(text)
    rows = []
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    for cols in reader:
        if len(cols) < 5 or not cols[0].strip().isdigit():
            continue
        rows.append({
            "number": int(cols[0].strip()),
            "gu": cols[1].strip(),
            "name": cols[2].strip(),
            "road_address": cols[3].strip(),
            "lot_address": cols[4].strip(),
            "market_type": cols[5].strip() if len(cols) > 5 else "",
            "form": cols[6].strip() if len(cols) > 6 else "",
        })
    return rows


SEOUL_MARKETS = load_seoul_markets()

ADMIN_DONG_MARKET_ALIASES = {
    "청룡동": ["봉천동"], "은천동": ["봉천동"], "성현동": ["봉천동"],
    "중앙동": ["봉천동"], "청림동": ["봉천동"], "행운동": ["봉천동"],
    "낙성대동": ["봉천동"], "인헌동": ["봉천동"], "보라매동": ["봉천동"],
    "서원동": ["신림동"], "신원동": ["신림동"], "서림동": ["신림동"],
    "삼성동": ["신림동"], "대학동": ["신림동"], "난곡동": ["신림동"],
    "난향동": ["신림동"], "조원동": ["신림동"], "미성동": ["신림동"],
    "신사동": ["신림동"],
}


def get_markets_for_place(place):
    gu = place.get("gu", "").strip()
    dong = place.get("name", "").strip()
    target_stems = {normalize_dong_stem(dong)}
    target_stems.update(normalize_dong_stem(alias) for alias in ADMIN_DONG_MARKET_ALIASES.get(dong, []))
    target_stems.discard("")

    matches = []
    for market in SEOUL_MARKETS:
        if market["gu"] != gu:
            continue
        address_text = f"{market['road_address']} {market['lot_address']}"
        address_tokens = re.findall(r"[가-힣]+(?:\d+가|\d*동)", address_text)
        address_stems = {normalize_dong_stem(token) for token in address_tokens}
        name_stem = normalize_dong_stem(market["name"])
        if target_stems & address_stems or any(stem and stem in name_stem for stem in target_stems):
            matches.append(market)

    unique, seen = [], set()
    for market in matches:
        key = normalize_text(market["name"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(market)
    return unique


def build_market_experience(place):
    markets = get_markets_for_place(place)
    if not markets:
        return "", []
    if len(markets) == 1:
        market = markets[0]
        activity = (
            f"{market['name']}에 들러 대표 먹거리나 생활 상품 한 가지를 골라보고, "
            f"{market['form'] or '시장'} 공간의 분위기를 관찰하기"
        )
    else:
        names = "와 ".join(item["name"] for item in markets[:2])
        activity = f"{names}을 차례로 둘러보며 판매 품목과 골목 분위기의 차이를 비교해 보기"
    return activity, markets

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


LOCAL_SIGNATURES = {
    "종로구": [
        "오래된 골목의 한옥·석축·계단 같은 도시 흔적을 찾아보기",
        "작은 공방이나 오래된 전문 상점의 간판을 관찰하기",
        "큰길보다 안쪽 골목을 연결해 도심의 옛 구조를 느껴보기",
    ],
    "중구": [
        "인쇄·봉제·공구 등 도심 산업 상점이 남은 거리를 찾아보기",
        "근대 건축과 새 상업공간이 맞닿는 지점을 비교해 보기",
        "오래된 시장에서 이 동네만의 점심 메뉴를 하나 골라보기",
    ],
    "용산구": [
        "언덕과 철길, 오래된 주택가가 만드는 높낮이를 따라 걸어보기",
        "서로 다른 나라의 음식이나 생활문화가 섞인 가게를 찾아보기",
        "남산·한강·철도 중 하나가 보이는 전망 지점을 찾아보기",
    ],
    "성동구": [
        "공장·창고를 고쳐 만든 공간과 현재 운영 중인 작업장을 비교해 보기",
        "중랑천이나 한강으로 이어지는 길을 따라 동네의 경계를 확인하기",
        "수제화·금속·인쇄 등 지역 산업의 흔적이 남은 간판을 찾아보기",
    ],
    "광진구": [
        "한강과 아차산 사이에서 지형이 바뀌는 지점을 따라 걸어보기",
        "재래시장 또는 대학가에서 이 동네의 대표 간식을 골라보기",
        "큰길 뒤편의 낮은 주택가와 상업 골목을 비교해 보기",
    ],
    "동대문구": [
        "시장·약령·철도 주변에 남은 오래된 상업 흔적을 찾아보기",
        "청계천 또는 중랑천으로 이어지는 생활 산책길을 걸어보기",
        "대학가와 전통시장이 만나는 지점에서 서로 다른 분위기를 관찰하기",
    ],
    "중랑구": [
        "중랑천으로 이어지는 골목을 따라 동네의 물길을 찾아보기",
        "봉화산·용마산 자락이 보이는 방향으로 걸으며 지형을 느껴보기",
        "시장 안에서 지역 주민이 많이 고르는 간식 한 가지를 맛보기",
    ],
    "성북구": [
        "성곽·구릉·주택가가 만나는 계단길을 따라 걸어보기",
        "문인·예술가·대학 문화의 흔적이 남은 작은 공간을 찾아보기",
        "동네의 오래된 빵집이나 분식집에서 대표 메뉴를 골라보기",
    ],
    "강북구": [
        "북한산 자락으로 이어지는 골목의 경사와 풍경 변화를 느껴보기",
        "전통시장과 산행 입구 주변의 생활 상권을 비교해 보기",
        "4·19 또는 근현대사와 연결되는 장소를 한 곳 찾아보기",
    ],
    "도봉구": [
        "도봉산 방향으로 시야가 열리는 골목이나 하천길을 찾아보기",
        "철도역 주변의 오래된 상권과 새 주거지를 비교해 보기",
        "시장 안에서 산행객과 주민이 함께 찾는 메뉴를 골라보기",
    ],
    "노원구": [
        "아파트 단지 사이의 녹지축과 하천 산책로를 연결해 걸어보기",
        "불암산·수락산이 보이는 지점을 찾아 동네의 방향감을 익혀보기",
        "대학가 또는 역세권에서 오래된 지역 상점을 찾아보기",
    ],
    "은평구": [
        "북한산 자락과 주택가가 만나는 경계의 풍경을 따라 걸어보기",
        "불광천 또는 작은 물길을 따라 인접 동네까지 이동해 보기",
        "한옥·시장·오래된 주택 중 이 동네의 대표 생활 풍경을 찾아보기",
    ],
    "서대문구": [
        "안산 자락과 경의선 주변의 높낮이가 다른 길을 비교해 보기",
        "대학가·시장·주택가가 맞닿는 경계에서 분위기 변화를 관찰하기",
        "독립운동 또는 근현대사와 연결되는 흔적을 한 곳 찾아보기",
    ],
    "마포구": [
        "경의선 철길·한강·옛 주택가 중 하나를 축으로 동네를 걸어보기",
        "공연·출판·디자인 문화가 남은 작은 가게나 작업실을 찾아보기",
        "유명 상권을 벗어나 주민이 이용하는 시장이나 골목 식당을 찾아보기",
    ],
    "양천구": [
        "안양천과 주거단지를 잇는 산책 경로를 만들어 걸어보기",
        "계획도시의 넓은 길과 오래된 골목이 만나는 지점을 찾아보기",
        "동네 시장에서 주민들이 많이 사는 먹거리를 하나 골라보기",
    ],
    "강서구": [
        "한강·습지·공항 중 이 동네의 성격을 만든 요소를 찾아보기",
        "오래된 자연마을과 새 주거지의 거리 구조를 비교해 보기",
        "시장이나 골목에서 강서 지역의 생활형 맛집을 찾아보기",
    ],
    "구로구": [
        "철도·공단·주거지가 겹치는 풍경을 관찰하며 걸어보기",
        "디지털 산업단지와 오래된 공업 골목의 차이를 비교해 보기",
        "다문화 식당가에서 평소 먹지 않던 메뉴를 하나 선택해 보기",
    ],
    "금천구": [
        "옛 공단 건물과 새 지식산업센터가 나란히 보이는 지점을 찾아보기",
        "안양천 또는 철길을 따라 산업도시의 경계를 걸어보기",
        "독산동 우시장처럼 지역 산업과 연결된 먹거리 흔적을 찾아보기",
    ],
    "영등포구": [
        "공장·철도·한강이 만든 도시 풍경을 한 번에 볼 수 있는 길을 찾아보기",
        "오래된 시장과 초고층 업무지구의 대비를 관찰해 보기",
        "문래·대림·영등포 중 지역 산업문화가 드러나는 장소를 찾아보기",
    ],
    "동작구": [
        "한강과 언덕을 연결하는 계단길이나 전망 지점을 찾아보기",
        "시장·대학가·주택가가 만나는 생활 골목을 따라 걸어보기",
        "근현대사 또는 현충 문화와 연결되는 장소를 한 곳 확인해 보기",
    ],
    "관악구": [
        "관악산 자락에서 대학가·고시촌·주택가로 분위기가 바뀌는 길을 걸어보기",
        "도림천을 따라 동네 중심과 외곽을 연결해 보기",
        "학생과 주민이 함께 찾는 오래된 식당의 대표 메뉴를 골라보기",
    ],
    "서초구": [
        "한강·우면산·양재천 중 가까운 자연축을 따라 걸어보기",
        "대형 상업지 뒤편에 남은 오래된 주택가나 시장을 찾아보기",
        "법조·예술·교통 거점 중 이 동네를 특징짓는 공간을 관찰하기",
    ],
    "강남구": [
        "대로변의 고층 건물과 뒤편 저층 골목의 대비를 비교해 보기",
        "양재천·탄천·선릉 중 가까운 녹지 또는 역사 공간을 찾아보기",
        "유명 프랜차이즈 대신 오래 운영된 동네 가게를 한 곳 찾아보기",
    ],
    "송파구": [
        "석촌호수·탄천·한강 중 가까운 물길을 따라 동네를 읽어보기",
        "백제 유적과 현대 대단지 사이의 시간 차이를 관찰해 보기",
        "시장 또는 오래된 상가에서 송파 주민이 즐겨 찾는 간식을 골라보기",
    ],
    "강동구": [
        "한강·고덕산·일자산 중 가까운 자연 지형을 따라 걸어보기",
        "선사 유적과 새 주거지가 공존하는 풍경을 비교해 보기",
        "전통시장 또는 골목 상권에서 지역 대표 먹거리를 찾아보기",
    ],
}

SPECIAL_AREA_RULES = [
    {
        "aliases": ["망원"],
        "title": "망원동",
        "things": [
            "망원시장에서 한 가지씩 포장해 망원한강공원 잔디밭에서 작은 피크닉 해보기",
            "망원시장과 월드컵시장을 차례로 둘러보고 먹거리와 손님 분위기를 비교해 보기",
            "망원정에서 한강공원까지 걸으며 옛 정자·주택가·강변 풍경이 바뀌는 지점 기록하기",
        ],
    },
    {
        "aliases": ["성수"],
        "title": "성수동",
        "things": [
            "성수 수제화 거리에서 구두골목의 공방·부자재 상점·완제품 매장을 구분해 찾아보기",
            "붉은 벽돌 옛 공장과 현재 운영 중인 제조 작업장을 비교하며 산업 골목 한 바퀴 걷기",
            "서울숲에서 성수동 공업 골목을 거쳐 한강 쪽으로 이동하며 녹지·산업·수변 풍경 변화를 기록하기",
        ],
    },
    {
        "aliases": ["문래"],
        "title": "문래동",
        "things": [
            "문래 철공소 골목에서 절단·용접·금속 가공 작업이 이루어지는 모습을 방해하지 않고 관찰하기",
            "문래창작촌의 설치작품과 실제 공업 간판을 각각 세 개씩 찾아 차이를 비교해 보기",
            "문래역에서 도림천 방향으로 걸으며 철공소·창작공간·주택가가 바뀌는 경계를 찾아보기",
        ],
    },
    {
        "aliases": ["창신"],
        "title": "창신동",
        "things": [
            "봉제 골목에서 원단·재단·재봉·부자재와 관련된 가게를 하나씩 찾아 의류 생산 흐름 그려보기",
            "채석장 절벽과 빽빽한 주택가가 함께 보이는 전망 지점을 찾아 창신동 지형 관찰하기",
            "동대문 의류상가 방향에서 창신동 봉제 골목까지 걸으며 판매 공간과 생산 공간의 연결을 확인하기",
        ],
    },
    {
        "aliases": ["부암"],
        "title": "부암동",
        "things": [
            "윤동주문학관을 기준점으로 시인의 언덕과 인왕산 자락을 잇는 짧은 문학 산책 해보기",
            "창의문 주변에서 한양도성의 옛 출입구와 현재 도로가 만나는 모습을 관찰하기",
            "인왕산 바위·한양도성·저층 주택이 한 화면에 들어오는 부암동 전망 지점 찾아보기",
        ],
    },
    {
        "aliases": ["해방촌", "용산2가"],
        "title": "해방촌",
        "things": [
            "신흥시장에서 여러 나라의 음식 간판과 오래된 생활 상점을 함께 찾아보기",
            "108계단과 언덕 골목을 오르며 남산과 도심 조망이 달라지는 지점 세 곳 기록하기",
            "오래된 주택을 개조한 공간과 여전히 주거용으로 쓰이는 건물을 비교해 보기",
        ],
    },
    {
        "aliases": ["암사"],
        "title": "암사동",
        "things": [
            "암사종합시장에서 간식을 골라 광나루한강공원 방향으로 산책하기",
            "암사동 선사유적 주변에서 선사시대 생활터와 현재 주거지를 비교해 보기",
            "암사생태공원 쪽으로 이동하며 자연형 한강변과 도시형 한강공원의 차이 찾아보기",
        ],
    },
]


def get_special_area_things(place):
    haystack = normalize_text(
        f"{place.get('gu', '')} {place.get('name', '')} {place.get('full_name', '')}"
    )
    for rule in SPECIAL_AREA_RULES:
        if any(normalize_text(alias) in haystack for alias in rule["aliases"]):
            return list(rule["things"])
    return []


def fallback_local_things(place):
    dong = place["name"]
    gu = place["gu"]
    special = get_special_area_things(place)
    if special:
        return special
    return LOCAL_SIGNATURES.get(
        gu,
        [
            f"{dong}의 지명 유래를 보여주는 표지판이나 오래된 상호를 찾아보기",
            f"{dong}의 공원·하천·생활 골목을 연결해 동네만의 산책 경로 만들기",
            "같은 동네 안에서 오래된 건물과 새 건물을 한 장씩 사진으로 남기기",
        ],
    )




@st.cache_data(show_spinner=False)
def load_facility_tsv(path):
    """시설 파일을 읽는다. 탭 구분 TSV를 우선하며 잘못 저장된 CSV도 복구한다."""
    if not path.exists():
        return []

    text = decode_data_file(path)
    if not text.strip():
        return []

    delimiter = detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    if not reader.fieldnames:
        return []

    fieldnames = [str(name or "").strip().lstrip("\ufeff") for name in reader.fieldnames]
    required = {"gu", "dong_tokens", "name", "address"}
    if not required.issubset(set(fieldnames)):
        return []

    rows = []
    for raw_row in reader:
        row = {}
        for key, value in raw_row.items():
            if key is None:
                continue
            clean_key = str(key).strip().lstrip("\ufeff")
            clean_value = value.strip() if isinstance(value, str) else value
            row[clean_key] = clean_value
        if row.get("name"):
            rows.append(row)
    return rows


SEOUL_HERITAGE = load_facility_tsv(HERITAGE_DATA_PATH)
SEOUL_CULTURE = load_facility_tsv(CULTURE_DATA_PATH)
SEOUL_PARKS = load_facility_tsv(PARK_DATA_PATH)


def get_target_dong_stems(place):
    dong = place.get("name", "").strip()
    stems = {normalize_dong_stem(dong)}
    stems.update(
        normalize_dong_stem(alias)
        for alias in ADMIN_DONG_MARKET_ALIASES.get(dong, [])
    )
    stems.discard("")
    return stems


def extract_dong_stems_from_text(value):
    """TSV 행 안의 동 표기를 정규화한다. 외부 검색 결과는 사용하지 않는다."""
    text = str(value or "")
    tokens = re.findall(r"[가-힣]+(?:\d+가|\d*동)", text)
    stems = {normalize_dong_stem(token) for token in tokens}
    stems.discard("")
    return stems


def match_facilities_to_place(rows, place):
    """해당 TSV 안의 gu/dong_tokens/address 값만으로 행정동을 연결한다."""
    gu = place.get("gu", "").strip()
    target_stems = get_target_dong_stems(place)
    matched = []

    for row in rows:
        if row.get("gu", "").strip() != gu:
            continue

        row_stems = {
            normalize_dong_stem(token)
            for token in row.get("dong_tokens", "").split("|")
            if token.strip()
        }
        row_stems.update(extract_dong_stems_from_text(row.get("address", "")))
        row_stems.discard("")

        if target_stems & row_stems:
            matched.append(row)

    unique = []
    seen = set()
    for row in matched:
        key = normalize_text(row.get("name", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def random_three(items):
    items = list(items)
    if len(items) <= 3:
        return items
    return random.sample(items, 3)


def facility_link(item):
    """링크는 TSV의 url을 우선 사용하고, 없을 때도 같은 TSV의 이름·주소로만 만든다."""
    url = str(item.get("url", "") or "").strip()
    if url:
        return url
    query = " ".join(
        value for value in (
            str(item.get("name", "")).strip(),
            str(item.get("address", "")).strip(),
        )
        if value
    )
    return naver_map_url(query) if query else ""


def build_local_experiences(full_name, gu, dong):
    """각 분류는 지정된 로컬 TSV에서만 읽는다."""
    place = {"full_name": full_name, "gu": gu, "name": dong}
    results = []

    # 1. 역사유적: data/seoul_heritage.tsv만 사용
    heritage_items = random_three(match_facilities_to_place(SEOUL_HERITAGE, place))
    if heritage_items:
        results.append({
            "type": "역사유적",
            "icon": "🏛️",
            "facilities": [
                {"name": item.get("name", ""), "url": facility_link(item)}
                for item in heritage_items
            ],
        })

    # 2. 문화시설: data/seoul_culture.tsv만 사용
    culture_items = random_three(match_facilities_to_place(SEOUL_CULTURE, place))
    if culture_items:
        results.append({
            "type": "문화시설",
            "icon": "🎭",
            "facilities": [
                {"name": item.get("name", ""), "url": facility_link(item)}
                for item in culture_items
            ],
        })

    # 3. 시장: data/seoul_markets.tsv만 사용
    market_rows = get_markets_for_place(place)
    market_items = random_three(market_rows)
    if market_items:
        results.append({
            "type": "시장",
            "icon": "🛍️",
            "facilities": [
                {
                    "name": item.get("name", ""),
                    "url": naver_map_url(
                        " ".join(
                            value for value in (
                                item.get("name", ""),
                                item.get("road_address", "") or item.get("lot_address", ""),
                            )
                            if value
                        )
                    ),
                }
                for item in market_items
            ],
        })

    # 4. 공원: data/seoul_parks.tsv만 사용
    park_items = random_three(match_facilities_to_place(SEOUL_PARKS, place))
    if park_items:
        results.append({
            "type": "공원",
            "icon": "🌳",
            "facilities": [
                {"name": item.get("name", ""), "url": facility_link(item)}
                for item in park_items
            ],
        })

    return results

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


st.title("🧭서울마실")
st.write("이 동네는 어때요?")

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
    st.info(f"**{len(candidates)}곳**이 기다려요")
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
    st.info("버튼을 눌러 오늘의 서울 동네를 뽑아보세요.")
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
        use_container_width=True,
    )

st.subheader("이 동네에서 해볼 일")
local_experiences = build_local_experiences(
    place["full_name"],
    place["gu"],
    place["name"],
)
for index, item in enumerate(local_experiences, start=1):
    st.markdown(f"### {index}. {item['icon']} {item['type']}")
    for facility_index, facility in enumerate(item.get("facilities", []), start=1):
        name = facility.get("name", "").strip()
        url = facility.get("url", "").strip()
        if not name:
            continue
        col_name, col_link = st.columns([8, 1])
        with col_name:
            st.write(name)
        with col_link:
            if url:
                st.link_button(
                    "🔗",
                    url,
                    key=f"activity_link_{index}_{facility_index}",
                    help="지도 또는 공식 페이지에서 확인",
                )

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
if st.button("🎲 다른 동네 가기", use_container_width=True):
    st.session_state["selected_place"] = random.choice(candidates)
    st.session_state.pop("food_picks", None)
    st.session_state.pop("cafe_picks", None)
    st.rerun()

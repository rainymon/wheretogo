import html
import random
from urllib.parse import quote, urlencode

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="서울에서 두 시간",
    page_icon="🚆",
    layout="wide",
)

# -------------------------------------------------------------------
# 기본 설정
# -------------------------------------------------------------------
APP_TITLE = "서울에서 두 시간"
WIKI_TIMEOUT = 8
API_TIMEOUT = 10

ORIGIN_COORDS = {
    "서울역": (37.5547, 126.9706),
    "용산역": (37.5298, 126.9648),
    "청량리역": (37.5802, 127.0473),
    "서울고속터미널": (37.5048, 127.0049),
    "동서울터미널": (37.5349, 127.0958),
    "남부터미널": (37.4850, 127.0162),
}

# 이동시간은 일반적인 평시 기준의 대략적인 편도 최소~평균 시간입니다.
# 날짜, 출발 시각, 환승 대기, 도로 상황에 따라 2시간을 넘을 수 있습니다.
TRIPS = [
    {
        "origin": "서울역",
        "city": "수원",
        "province": "경기도",
        "minutes": 45,
        "transport": "수도권 1호선 또는 일반열차로 수원역 이동",
        "category": ["역사", "산책", "카페"],
        "intro": "정조가 건설한 수원화성과 행궁동을 함께 즐길 수 있는 대표적인 역사 근교 여행지입니다.",
        "lat": 37.2636,
        "lon": 127.0286,
        "sights": ["수원 화성", "화성행궁", "행궁동"],
        "food_queries": ["수원 왕갈비", "수원 통닭거리", "행궁동 카페"],
    },
    {
        "origin": "서울역",
        "city": "인천 개항장",
        "province": "인천광역시",
        "minutes": 70,
        "transport": "수도권 1호선으로 인천역 이동",
        "category": ["역사", "바다", "카페"],
        "intro": "근대 개항기의 건축과 차이나타운, 월미도 바다 풍경을 한 번에 만날 수 있습니다.",
        "lat": 37.4738,
        "lon": 126.6216,
        "sights": ["인천 차이나타운", "송월동 동화마을", "월미도"],
        "food_queries": ["인천 차이나타운 맛집", "신포시장 맛집", "개항로 카페"],
    },
    {
        "origin": "서울역",
        "city": "파주",
        "province": "경기도",
        "minutes": 80,
        "transport": "경의중앙선으로 금촌·문산 방향 이동 후 지역버스 이용",
        "category": ["예술", "책", "카페"],
        "intro": "출판도시와 예술마을, 대형 카페가 모여 있어 전시와 책을 좋아하는 여행자에게 잘 맞습니다.",
        "lat": 37.7599,
        "lon": 126.7800,
        "sights": ["파주출판도시", "헤이리 예술마을", "임진각"],
        "food_queries": ["파주 출판도시 맛집", "헤이리 맛집", "파주 대형카페"],
    },
    {
        "origin": "서울역",
        "city": "천안",
        "province": "충청남도",
        "minutes": 75,
        "transport": "무궁화호·ITX-새마을 또는 수도권 1호선으로 천안역 이동",
        "category": ["역사", "공원", "빵"],
        "intro": "독립운동 역사 공간과 넓은 공원, 천안의 유명한 빵 문화를 함께 즐길 수 있습니다.",
        "lat": 36.8151,
        "lon": 127.1139,
        "sights": ["독립기념관", "천안삼거리공원", "아라리오 광장"],
        "food_queries": ["천안 호두과자", "천안역 맛집", "천안 카페"],
    },
    {
        "origin": "용산역",
        "city": "전주",
        "province": "전북특별자치도",
        "minutes": 105,
        "transport": "KTX로 전주역 이동 후 시내버스 또는 택시",
        "category": ["한옥", "음식", "문화"],
        "intro": "한옥 골목과 전통문화, 비빔밥·콩나물국밥 등 풍부한 먹거리가 강점인 도시입니다.",
        "lat": 35.8242,
        "lon": 127.1480,
        "sights": ["전주한옥마을", "경기전", "전동성당"],
        "food_queries": ["전주 비빔밥", "전주 콩나물국밥", "전주 한옥마을 카페"],
    },
    {
        "origin": "용산역",
        "city": "공주",
        "province": "충청남도",
        "minutes": 100,
        "transport": "KTX로 공주역 이동 후 시내버스 또는 택시",
        "category": ["역사", "유적", "산책"],
        "intro": "백제의 옛 수도로 공산성과 왕릉, 박물관을 중심으로 차분한 역사 여행을 즐길 수 있습니다.",
        "lat": 36.4465,
        "lon": 127.1190,
        "sights": ["공산성", "무령왕릉", "국립공주박물관"],
        "food_queries": ["공주 산성시장 맛집", "공주 알밤 디저트", "공주 카페"],
    },
    {
        "origin": "용산역",
        "city": "익산",
        "province": "전북특별자치도",
        "minutes": 75,
        "transport": "KTX로 익산역 이동",
        "category": ["역사", "유적", "정원"],
        "intro": "백제 유적과 넓은 정원, 보석 문화를 둘러보기 좋은 전북의 철도 거점 도시입니다.",
        "lat": 35.9483,
        "lon": 126.9576,
        "sights": ["미륵사지", "왕궁리 유적", "익산 보석박물관"],
        "food_queries": ["익산역 맛집", "익산 황등비빔밥", "익산 카페"],
    },
    {
        "origin": "용산역",
        "city": "아산",
        "province": "충청남도",
        "minutes": 90,
        "transport": "KTX·일반열차로 천안아산역 또는 온양온천역 이동",
        "category": ["온천", "역사", "호수"],
        "intro": "오래된 온천 문화와 현충사, 호수 풍경을 함께 즐길 수 있는 편안한 당일치기 여행지입니다.",
        "lat": 36.7898,
        "lon": 127.0018,
        "sights": ["현충사", "온양온천", "신정호"],
        "food_queries": ["온양온천 맛집", "아산 장어구이", "신정호 카페"],
    },
    {
        "origin": "청량리역",
        "city": "춘천",
        "province": "강원특별자치도",
        "minutes": 75,
        "transport": "ITX-청춘으로 남춘천역 또는 춘천역 이동",
        "category": ["호수", "산책", "음식"],
        "intro": "호수와 강변 산책, 닭갈비와 막국수를 함께 즐길 수 있는 대표적인 서울 근교 도시입니다.",
        "lat": 37.8813,
        "lon": 127.7298,
        "sights": ["소양강 스카이워크", "공지천", "삼악산 호수케이블카"],
        "food_queries": ["춘천 닭갈비", "춘천 막국수", "춘천 카페"],
    },
    {
        "origin": "청량리역",
        "city": "가평",
        "province": "경기도",
        "minutes": 55,
        "transport": "ITX-청춘 또는 경춘선으로 가평역 이동",
        "category": ["자연", "섬", "정원"],
        "intro": "북한강과 산, 섬과 정원이 어우러져 계절별 풍경을 즐기기 좋은 자연 여행지입니다.",
        "lat": 37.8315,
        "lon": 127.5096,
        "sights": ["남이섬", "자라섬", "아침고요수목원"],
        "food_queries": ["가평 잣두부", "가평 막국수", "가평 카페"],
    },
    {
        "origin": "청량리역",
        "city": "양평",
        "province": "경기도",
        "minutes": 60,
        "transport": "경의중앙선 또는 KTX-이음으로 양평역 이동",
        "category": ["강", "산책", "카페"],
        "intro": "두물머리와 세미원 등 물가 풍경이 아름답고 드라이브·산책·카페 여행에 잘 맞습니다.",
        "lat": 37.4917,
        "lon": 127.4876,
        "sights": ["두물머리", "세미원", "용문사"],
        "food_queries": ["양평 해장국", "두물머리 맛집", "양평 카페"],
    },
    {
        "origin": "청량리역",
        "city": "원주",
        "province": "강원특별자치도",
        "minutes": 50,
        "transport": "KTX-이음으로 원주역 또는 만종역 이동",
        "category": ["자연", "예술", "시장"],
        "intro": "출렁다리와 산악 풍경, 미술관과 전통시장을 함께 즐길 수 있는 강원 내륙 여행지입니다.",
        "lat": 37.3422,
        "lon": 127.9202,
        "sights": ["소금산 출렁다리", "뮤지엄 산", "원주중앙시장"],
        "food_queries": ["원주 중앙시장 맛집", "원주 추어탕", "원주 카페"],
    },
    {
        "origin": "청량리역",
        "city": "제천",
        "province": "충청북도",
        "minutes": 65,
        "transport": "KTX-이음으로 제천역 이동",
        "category": ["호수", "산", "전통시장"],
        "intro": "청풍호와 산악 풍경, 전통시장을 중심으로 자연과 먹거리를 함께 즐길 수 있습니다.",
        "lat": 37.1326,
        "lon": 128.1910,
        "sights": ["청풍호반케이블카", "의림지", "제천중앙시장"],
        "food_queries": ["제천 빨간오뎅", "제천 약채락", "제천 카페"],
    },
    {
        "origin": "서울고속터미널",
        "city": "속초",
        "province": "강원특별자치도",
        "minutes": 120,
        "transport": "고속버스로 속초고속버스터미널 이동",
        "category": ["바다", "시장", "산"],
        "intro": "동해 바다와 설악산, 중앙시장의 먹거리를 한 번에 즐길 수 있는 강원 대표 관광도시입니다.",
        "lat": 38.2070,
        "lon": 128.5918,
        "sights": ["속초해수욕장", "속초관광수산시장", "영금정"],
        "food_queries": ["속초 중앙시장 맛집", "속초 물회", "속초 오션뷰 카페"],
    },
    {
        "origin": "서울고속터미널",
        "city": "강릉",
        "province": "강원특별자치도",
        "minutes": 120,
        "transport": "고속버스로 강릉고속버스터미널 이동",
        "category": ["바다", "커피", "문화"],
        "intro": "동해 해변과 커피거리, 전통문화 공간을 함께 즐길 수 있는 인기 당일치기 도시입니다.",
        "lat": 37.7519,
        "lon": 128.8761,
        "sights": ["경포대", "안목해변", "오죽헌"],
        "food_queries": ["강릉 초당순두부", "강릉 중앙시장", "안목해변 카페"],
    },
    {
        "origin": "서울고속터미널",
        "city": "청주",
        "province": "충청북도",
        "minutes": 100,
        "transport": "고속버스로 청주고속버스터미널 이동",
        "category": ["박물관", "성곽", "시장"],
        "intro": "직지 문화와 박물관, 성곽과 전통시장을 둘러보기 좋은 충북의 중심 도시입니다.",
        "lat": 36.6424,
        "lon": 127.4890,
        "sights": ["청주고인쇄박물관", "상당산성", "육거리종합시장"],
        "food_queries": ["청주 삼겹살거리", "청주 육거리시장 맛집", "청주 카페"],
    },
    {
        "origin": "서울고속터미널",
        "city": "이천",
        "province": "경기도",
        "minutes": 70,
        "transport": "고속버스로 이천종합터미널 이동",
        "category": ["도자기", "온천", "쌀"],
        "intro": "도자기 문화와 온천, 쌀밥 한정식으로 유명해 체험과 미식 여행에 적합합니다.",
        "lat": 37.2720,
        "lon": 127.4350,
        "sights": ["이천도자예술마을", "설봉공원", "테르메덴"],
        "food_queries": ["이천 쌀밥", "이천 도자예술마을 맛집", "이천 카페"],
    },
    {
        "origin": "동서울터미널",
        "city": "충주",
        "province": "충청북도",
        "minutes": 100,
        "transport": "시외버스로 충주공용버스터미널 이동",
        "category": ["호수", "공원", "온천"],
        "intro": "충주호와 탄금대, 수안보온천 등 물과 역사, 휴식을 함께 즐길 수 있습니다.",
        "lat": 36.9910,
        "lon": 127.9259,
        "sights": ["탄금대", "중앙탑사적공원", "수안보온천"],
        "food_queries": ["충주 올갱이국", "충주 중앙시장", "충주 카페"],
    },
    {
        "origin": "동서울터미널",
        "city": "홍천",
        "province": "강원특별자치도",
        "minutes": 85,
        "transport": "시외버스로 홍천종합버스터미널 이동",
        "category": ["강", "숲", "시장"],
        "intro": "맑은 강과 숲, 지역 시장을 중심으로 조용한 자연 여행을 즐기기 좋은 곳입니다.",
        "lat": 37.6972,
        "lon": 127.8887,
        "sights": ["수타사", "홍천강", "홍천전통시장"],
        "food_queries": ["홍천 화로구이", "홍천시장 맛집", "홍천 카페"],
    },
    {
        "origin": "동서울터미널",
        "city": "양양",
        "province": "강원특별자치도",
        "minutes": 120,
        "transport": "시외버스로 양양종합여객터미널 이동",
        "category": ["바다", "서핑", "사찰"],
        "intro": "서핑 해변과 동해 전망, 낙산사 등 자연과 문화가 어우러진 해안 여행지입니다.",
        "lat": 38.0754,
        "lon": 128.6190,
        "sights": ["낙산사", "서피비치", "죽도해변"],
        "food_queries": ["양양 물회", "양양 막국수", "양양 오션뷰 카페"],
    },
    {
        "origin": "동서울터미널",
        "city": "여주",
        "province": "경기도",
        "minutes": 75,
        "transport": "시외버스로 여주종합터미널 이동",
        "category": ["역사", "강", "도자기"],
        "intro": "남한강 풍경과 세종대왕 관련 유적, 도자기 문화를 둘러볼 수 있는 차분한 여행지입니다.",
        "lat": 37.2983,
        "lon": 127.6374,
        "sights": ["영릉", "신륵사", "여주도자세상"],
        "food_queries": ["여주 쌀밥", "여주 막국수", "여주 카페"],
    },
    {
        "origin": "남부터미널",
        "city": "안성",
        "province": "경기도",
        "minutes": 75,
        "transport": "시외버스로 안성종합버스터미널 이동",
        "category": ["공연", "시장", "목장"],
        "intro": "남사당 문화와 전통시장, 목장 체험을 즐길 수 있는 경기 남부의 문화 여행지입니다.",
        "lat": 37.0079,
        "lon": 127.2797,
        "sights": ["안성맞춤랜드", "안성팜랜드", "안성중앙시장"],
        "food_queries": ["안성 국밥", "안성 중앙시장 맛집", "안성 카페"],
    },
    {
        "origin": "남부터미널",
        "city": "평택",
        "province": "경기도",
        "minutes": 80,
        "transport": "시외버스로 평택터미널 이동",
        "category": ["항구", "시장", "국제문화"],
        "intro": "항구 풍경과 국제시장 분위기, 다양한 세계 음식을 경험할 수 있는 도시입니다.",
        "lat": 36.9921,
        "lon": 127.1129,
        "sights": ["평택호관광단지", "송탄관광특구", "통복시장"],
        "food_queries": ["송탄 부대찌개", "평택 통복시장 맛집", "평택 카페"],
    },
    {
        "origin": "남부터미널",
        "city": "예산",
        "province": "충청남도",
        "minutes": 115,
        "transport": "시외버스로 예산종합터미널 이동",
        "category": ["시장", "호수", "사찰"],
        "intro": "전통시장 먹거리와 예당호, 수덕사를 연결해 즐길 수 있는 충남의 소도시 여행지입니다.",
        "lat": 36.6828,
        "lon": 126.8487,
        "sights": ["예산시장", "예당호 출렁다리", "수덕사"],
        "food_queries": ["예산시장 맛집", "예산 어죽", "예산 카페"],
    },
    {
        "origin": "남부터미널",
        "city": "태안",
        "province": "충청남도",
        "minutes": 120,
        "transport": "시외버스로 태안공용버스터미널 이동",
        "category": ["바다", "꽃", "시장"],
        "intro": "서해 해변과 해안 산책길, 꽃 정원과 해산물 시장을 즐길 수 있는 여행지입니다.",
        "lat": 36.7456,
        "lon": 126.2981,
        "sights": ["꽃지해수욕장", "안면도 자연휴양림", "태안서부시장"],
        "food_queries": ["태안 게국지", "태안 서부시장 맛집", "태안 오션뷰 카페"],
    },
]

ALL_CATEGORIES = sorted({category for trip in TRIPS for category in trip["category"]})


# -------------------------------------------------------------------
# 유틸리티
# -------------------------------------------------------------------
def secret_value(name: str) -> str:
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def clean_naver_title(text: str) -> str:
    return html.unescape(text.replace("<b>", "").replace("</b>", ""))


def google_maps_search_url(query: str) -> str:
    return "https://www.google.com/maps/search/?" + urlencode(
        {"api": "1", "query": query}
    )


def naver_map_search_url(query: str) -> str:
    return "https://map.naver.com/p/search/" + quote(query)


def google_transit_url(origin: str, destination: str) -> str:
    return "https://www.google.com/maps/dir/?" + urlencode(
        {
            "api": "1",
            "origin": origin,
            "destination": destination,
            "travelmode": "transit",
        }
    )


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def wikipedia_summary(title: str) -> dict:
    encoded = quote(title.replace(" ", "_"), safe="")
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    headers = {"User-Agent": "NearTripStreamlit/1.0 (educational project)"}
    try:
        response = requests.get(url, headers=headers, timeout=WIKI_TIMEOUT)
        if response.status_code != 200:
            return {}
        data = response.json()
        return {
            "title": data.get("title", title),
            "extract": data.get("extract", ""),
            "image": (data.get("thumbnail") or {}).get("source", ""),
            "page_url": (
                data.get("content_urls", {})
                .get("desktop", {})
                .get("page", "")
            ),
        }
    except requests.RequestException:
        return {}


@st.cache_data(ttl=60 * 30, show_spinner=False)
def google_places_search(query: str, api_key: str, max_results: int = 5) -> list:
    if not api_key:
        return []

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,places.rating,"
            "places.userRatingCount,places.googleMapsUri,places.primaryTypeDisplayName"
        ),
    }
    payload = {
        "textQuery": query,
        "languageCode": "ko",
        "regionCode": "KR",
        "maxResultCount": min(max_results, 20),
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        places = response.json().get("places", [])
        results = []
        for place in places[:max_results]:
            results.append(
                {
                    "name": (place.get("displayName") or {}).get("text", "이름 없음"),
                    "category": (
                        place.get("primaryTypeDisplayName") or {}
                    ).get("text", ""),
                    "address": place.get("formattedAddress", ""),
                    "rating": place.get("rating"),
                    "reviews": place.get("userRatingCount"),
                    "url": place.get("googleMapsUri", ""),
                    "source": "Google Places",
                }
            )
        return results
    except requests.RequestException:
        return []


@st.cache_data(ttl=60 * 30, show_spinner=False)
def naver_local_search(
    query: str,
    client_id: str,
    client_secret: str,
    max_results: int = 5,
) -> list:
    if not client_id or not client_secret:
        return []

    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": min(max_results, 5),
        "sort": "comment",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        results = []
        for rank, item in enumerate(items, start=1):
            name = clean_naver_title(item.get("title", "이름 없음"))
            results.append(
                {
                    "name": name,
                    "category": item.get("category", ""),
                    "address": item.get("roadAddress") or item.get("address", ""),
                    "rating": None,
                    "reviews": None,
                    "rank": rank,
                    "url": item.get("link") or naver_map_search_url(name),
                    "source": "네이버 지역검색",
                }
            )
        return results
    except requests.RequestException:
        return []


def choose_popular_random_place(items: list) -> dict:
    """검색 상위 업체가 더 자주 선택되도록 가중 랜덤 추천합니다."""
    if not items:
        return {}

    # sort=comment 검색 순서 기준: 1위 5, 2위 4, ... 5위 1의 가중치
    weights = list(range(len(items), 0, -1))
    return random.choices(items, weights=weights, k=1)[0]


def show_featured_naver_place(item: dict, label: str) -> None:
    if not item:
        st.info(f"추천할 {label} 검색 결과가 없습니다.")
        return

    rank = item.get("rank")
    rank_text = f"검색 상위 {rank}번째 후보" if rank else "인기 검색 후보"
    st.success(f"🎯 오늘의 랜덤 {label}: {item['name']}")
    st.caption(
        f"네이버 지역검색의 카페·블로그 리뷰 기반 정렬 결과 중 {rank_text}에서 "
        "가중 랜덤으로 선택했습니다."
    )
    st.write(item.get("category", ""))
    st.write(item.get("address", ""))
    if item.get("url"):
        st.link_button(
            "네이버 지도에서 후기 확인",
            item["url"],
            type="primary",
            use_container_width=True,
        )


def show_place_cards(items: list) -> None:
    if not items:
        st.info("검색 결과가 없습니다. 아래 지도 검색 버튼을 이용해 주세요.")
        return

    for index, item in enumerate(items, start=1):
        rating = item.get("rating")
        reviews = item.get("reviews")
        rating_text = ""
        if rating is not None:
            rating_text = f" · ⭐ {rating:.1f}"
            if reviews is not None:
                rating_text += f" ({reviews:,}개 평가)"

        st.markdown(
            f"""
            **{index}. {item['name']}**{rating_text}  
            {item.get('category', '')}  
            {item.get('address', '')}
            """
        )
        if item.get("url"):
            st.link_button(
                f"{item['source']}에서 열기",
                item["url"],
                use_container_width=True,
            )
        st.divider()


def select_random_trip(candidates: list) -> dict:
    if not candidates:
        return {}
    return random.choice(candidates)


# -------------------------------------------------------------------
# UI
# -------------------------------------------------------------------
st.title(f"🚆 {APP_TITLE}")
st.caption("서울의 주요 역·터미널에서 대중교통으로 약 2시간 안에 떠나는 랜덤 근교여행")

with st.sidebar:
    st.header("여행 조건")

    selected_origin = st.selectbox(
        "출발지",
        list(ORIGIN_COORDS.keys()),
    )

    selected_categories = st.multiselect(
        "관심 여행 유형",
        ALL_CATEGORIES,
        placeholder="선택하지 않으면 전체 유형",
    )

    max_minutes = st.slider(
        "최대 예상 이동시간",
        min_value=60,
        max_value=120,
        value=120,
        step=10,
        format="%d분",
    )

    st.markdown("---")
    st.subheader("맛집 데이터 설정")

    google_api_key = secret_value("GOOGLE_PLACES_API_KEY")
    naver_client_id = secret_value("NAVER_CLIENT_ID")
    naver_client_secret = secret_value("NAVER_CLIENT_SECRET")

    if google_api_key:
        st.success("Google Places 연결됨: 별점 표시 가능")
    elif naver_client_id and naver_client_secret:
        st.success("네이버 지역검색 연결됨")
        st.caption("네이버 지역검색 API 응답에는 지도 별점이 포함되지 않습니다.")
    else:
        st.warning("장소 API 키 없음: 지도 검색 링크로 대체됩니다.")

    st.caption(
        "API 키는 Streamlit Cloud의 Settings → Secrets에 저장하세요."
    )

candidates = [
    trip
    for trip in TRIPS
    if trip["origin"] == selected_origin
    and trip["minutes"] <= max_minutes
    and (
        not selected_categories
        or any(category in trip["category"] for category in selected_categories)
    )
]

col_count, col_action = st.columns([2, 1])
with col_count:
    st.info(f"현재 조건에 맞는 후보: **{len(candidates)}곳**")
with col_action:
    recommend_clicked = st.button(
        "🎲 여행지 랜덤 추천",
        type="primary",
        use_container_width=True,
        disabled=not candidates,
    )

condition_key = (
    selected_origin,
    tuple(sorted(selected_categories)),
    max_minutes,
)

if st.session_state.get("condition_key") != condition_key:
    st.session_state["condition_key"] = condition_key
    st.session_state["selected_trip"] = None

if recommend_clicked:
    st.session_state["selected_trip"] = select_random_trip(candidates)

trip = st.session_state.get("selected_trip")

if not candidates:
    st.error("선택한 조건에 맞는 목적지가 없습니다. 여행 유형이나 이동시간을 조정해 주세요.")
    st.stop()

if not trip:
    st.subheader("어디로 떠나볼까요?")
    st.write("왼쪽에서 조건을 선택한 뒤 **여행지 랜덤 추천** 버튼을 눌러보세요.")

    preview_df = pd.DataFrame(
        [
            {
                "목적지": item["city"],
                "지역": item["province"],
                "예상 시간": f"약 {item['minutes']}분",
                "유형": " · ".join(item["category"]),
            }
            for item in candidates
        ]
    )
    st.dataframe(preview_df, hide_index=True, use_container_width=True)
    st.stop()

# 추천 결과
st.markdown("---")
st.header(f"🎉 오늘의 여행지: {trip['city']}")
st.caption(f"{trip['province']} · {' · '.join(trip['category'])}")

metric1, metric2, metric3 = st.columns(3)
metric1.metric("출발지", trip["origin"])
metric2.metric("예상 편도 시간", f"약 {trip['minutes']}분")
metric3.metric("주요 볼거리", f"{len(trip['sights'])}곳")

st.subheader("가는 법")
st.write(trip["transport"])
st.link_button(
    "Google 지도에서 대중교통 경로 확인",
    google_transit_url(trip["origin"], trip["city"]),
    type="primary",
)

st.warning(
    "표시 시간은 일반적인 평시 기준 참고값입니다. "
    "날짜·출발 시각·교통 상황에 따라 2시간을 넘을 수 있으므로 출발 전 최신 시간표를 확인하세요."
)

st.subheader("도착지 소개")
st.write(trip["intro"])

map_df = pd.DataFrame(
    [{"lat": trip["lat"], "lon": trip["lon"], "목적지": trip["city"]}]
)
st.map(map_df, latitude="lat", longitude="lon", zoom=10, use_container_width=True)

st.subheader("주요 볼거리")
sight_columns = st.columns(3)

for index, sight in enumerate(trip["sights"]):
    info = wikipedia_summary(sight)
    with sight_columns[index % 3]:
        if info.get("image"):
            st.image(info["image"], use_container_width=True)
        else:
            st.info("Wikipedia 대표 사진 없음")

        st.markdown(f"### {sight}")

        if info.get("extract"):
            summary = info["extract"]
            if len(summary) > 180:
                summary = summary[:180].rstrip() + "…"
            st.write(summary)
        else:
            st.write(f"{trip['city']}에서 둘러보기 좋은 주요 명소입니다.")

        if info.get("page_url"):
            st.link_button(
                "Wikipedia에서 자세히",
                info["page_url"],
                use_container_width=True,
            )

st.markdown("---")
st.subheader("주요 맛집·카페")
st.caption(
    "결과는 선택한 플랫폼의 장소 검색 데이터를 기반으로 합니다. "
    "평점·영업시간·폐업 여부는 수시로 바뀔 수 있으니 방문 전 지도에서 다시 확인하세요."
)

tab_restaurant, tab_cafe = st.tabs(["🍽️ 맛집", "☕ 카페"])

restaurant_query = trip["food_queries"][0]
cafe_query = trip["food_queries"][-1]

with tab_restaurant:
    st.markdown(f"**추천 검색어:** {restaurant_query}")

    if google_api_key:
        restaurant_results = google_places_search(
            restaurant_query,
            google_api_key,
            max_results=5,
        )
        show_place_cards(restaurant_results)
    elif naver_client_id and naver_client_secret:
        restaurant_results = naver_local_search(
            restaurant_query,
            naver_client_id,
            naver_client_secret,
            max_results=5,
        )
        restaurant_state_key = f"featured_restaurant::{trip['city']}::{restaurant_query}"
        reroll_restaurant = st.button(
            "🎲 인기 맛집 다시 뽑기",
            key=f"reroll_restaurant::{trip['city']}",
            use_container_width=True,
        )
        if restaurant_state_key not in st.session_state or reroll_restaurant:
            st.session_state[restaurant_state_key] = choose_popular_random_place(
                restaurant_results
            )
        show_featured_naver_place(
            st.session_state.get(restaurant_state_key, {}),
            "맛집",
        )
        with st.expander("인기 검색 후보 전체 보기"):
            show_place_cards(restaurant_results)
        st.info(
            "네이버 지역검색은 sort='comment'로 카페·블로그 리뷰가 많은 순서의 "
            "상위 후보를 반환하지만, 실제 후기 개수와 지도 별점은 제공하지 않습니다."
        )
    else:
        st.write("API 키가 없어 실시간 업체 목록 대신 지도 검색 버튼을 제공합니다.")
        col1, col2 = st.columns(2)
        col1.link_button(
            "Google 지도에서 맛집 검색",
            google_maps_search_url(restaurant_query),
            use_container_width=True,
        )
        col2.link_button(
            "네이버 지도에서 맛집 검색",
            naver_map_search_url(restaurant_query),
            use_container_width=True,
        )

with tab_cafe:
    st.markdown(f"**추천 검색어:** {cafe_query}")

    if google_api_key:
        cafe_results = google_places_search(
            cafe_query,
            google_api_key,
            max_results=5,
        )
        show_place_cards(cafe_results)
    elif naver_client_id and naver_client_secret:
        cafe_results = naver_local_search(
            cafe_query,
            naver_client_id,
            naver_client_secret,
            max_results=5,
        )
        cafe_state_key = f"featured_cafe::{trip['city']}::{cafe_query}"
        reroll_cafe = st.button(
            "🎲 인기 카페 다시 뽑기",
            key=f"reroll_cafe::{trip['city']}",
            use_container_width=True,
        )
        if cafe_state_key not in st.session_state or reroll_cafe:
            st.session_state[cafe_state_key] = choose_popular_random_place(
                cafe_results
            )
        show_featured_naver_place(
            st.session_state.get(cafe_state_key, {}),
            "카페",
        )
        with st.expander("인기 검색 후보 전체 보기"):
            show_place_cards(cafe_results)
        st.info(
            "네이버 지역검색은 sort='comment'로 카페·블로그 리뷰가 많은 순서의 "
            "상위 후보를 반환하지만, 실제 후기 개수와 지도 별점은 제공하지 않습니다."
        )
    else:
        st.write("API 키가 없어 실시간 업체 목록 대신 지도 검색 버튼을 제공합니다.")
        col1, col2 = st.columns(2)
        col1.link_button(
            "Google 지도에서 카페 검색",
            google_maps_search_url(cafe_query),
            use_container_width=True,
        )
        col2.link_button(
            "네이버 지도에서 카페 검색",
            naver_map_search_url(cafe_query),
            use_container_width=True,
        )

with st.expander("다른 추천 후보 보기"):
    other_candidates = [
        item for item in candidates if item["city"] != trip["city"]
    ]
    if other_candidates:
        other_df = pd.DataFrame(
            [
                {
                    "목적지": item["city"],
                    "예상 편도": f"약 {item['minutes']}분",
                    "가는 법": item["transport"],
                    "유형": " · ".join(item["category"]),
                }
                for item in other_candidates
            ]
        )
        st.dataframe(other_df, hide_index=True, use_container_width=True)
    else:
        st.write("현재 조건에서는 다른 후보가 없습니다.")

st.markdown("---")
st.caption(
    "관광지 사진·요약: Wikipedia/Wikimedia · "
    "맛집·카페: Google Places 또는 네이버 지역검색 API · "
    "이 앱은 여행 아이디어 제공용이며 실시간 교통 안내 서비스가 아닙니다."
)

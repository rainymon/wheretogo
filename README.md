# 서울에서 두 시간

서울의 6개 주요 역·터미널에서 대중교통으로 약 2시간 이내에 갈 수 있는 도시를 랜덤 추천하는 Streamlit 앱입니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Streamlit Cloud

1. `main.py`와 `requirements.txt`를 GitHub 저장소에 업로드합니다.
2. Streamlit Community Cloud에서 앱을 배포합니다.
3. 맛집 API를 사용할 경우 앱의 **Settings → Secrets**에 `.streamlit/secrets.toml.example` 내용을 참고하여 키를 등록합니다.

## 맛집·카페 데이터

- Google Places API 키가 있으면 Google 별점과 평가 수를 표시합니다.
- NAVER 지역검색 API 키만 있으면 업체명, 주소, 분류를 표시합니다.
- API 키가 없으면 Google 지도와 네이버 지도 검색 링크를 제공합니다.

## 주의

이동시간은 일반적인 평시 기준의 참고값입니다. 실제 운행 시간은 날짜, 출발 시각, 교통 상황에 따라 달라집니다.

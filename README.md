# 어디갈까? 서울

`이 동네에서 해볼 일`의 데이터 출처를 네 파일로 엄격히 분리한 버전입니다.

- 역사유적: `data/seoul_heritage.tsv`
- 문화시설: `data/seoul_culture.tsv`
- 시장: `data/seoul_markets.tsv`
- 공원: `data/seoul_parks.tsv`

각 분류는 다른 API나 다른 TSV의 데이터를 섞지 않습니다. 동일 행정동에 후보가 여러 개면 최대 3개를 무작위로 표시합니다.

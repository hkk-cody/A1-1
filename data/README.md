# 데이터셋 안내 (Dataset Information)

본 과제에 사용되는 이커머스 멀티모달 데이터셋 안내입니다.

---

### 1. 기본 정보
* **데이터셋 명:** UCI Online Retail Multimodal Dataset (Sampled & Augmented)
* **파일 위치:** `data/ecommerce_data.csv`
* **이미지 디렉토리:** `data/images/` (각 상품별 32×32 썸네일 PNG)
* **행(Row) 수:** 12,000건
* **열(Column) 수:** 10개
* **라이선스:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **원문 출처:** [UCI Machine Learning Repository - Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail)
  * 논문 인용: Chen, D., Sain, S.L., & Guo, K. (2012). Data mining for the online retail industry: A case study of RFM model-based customer segmentation using data mining. *Journal of Database Marketing & Customer Strategy Management*, 19(3), 197-208.

---

### 2. 컬럼 명세서

| 컬럼명 | 데이터 유형 | 설명 | 과제 내 활용 목적 |
| :--- | :--- | :--- | :--- |
| `invoice_no` | 범주형 (String) | 주문 번호 (6자리 숫자, 'C'로 시작 시 취소 주문) | 거래 식별 |
| `product_id` | 범주형 (String) | 상품 고유 코드 (StockCode) | 상품 식별 및 이미지 매핑 |
| `product_name` | 텍스트형 (String) | 상품명 (Description) | **4-3 텍스트 피처 추출 (단어 수 / 글자 수)** |
| `category` | 범주형 (String) | 상품 카테고리 (Home & Decor, Kitchen, Fashion 등) | **4-4 GroupBy 결측치 대치 및 EDA** |
| `quantity` | 수치형 (Integer) | 주문 수량 (음수는 반품/취소) | **4-4 IQR 이상치 탐지 및 RFM 금액 계산** |
| `order_date` | 날짜형 (Datetime) | 주문 일시 (`YYYY-MM-DD HH:MM`) | **4-1 & 4-7 RFM Recency 기준 경과일 계산** |
| `unit_price` | 수치형 (Float) | 상품 단가 (파운드 £ 기준) | **4-4 IQR 이상치 탐지 및 RFM 금액 계산** |
| `customer_id` | 범주/수치 (Float) | 고객 고유 번호 (5자리) | **4-7 RFM 고객 단위 세분화 (단골 찾기)** |
| `country` | 범주형 (String) | 고객 거주 국가 | EDA 범주형 분포 분석 |
| `image_path` | 경로/이미지 (String) | 상품 썸네일 PNG 파일 경로 (`data/images/...`) | **4-3 NumPy 벡터 연산 (이미지 평균/표준편차 피처)** |

---

### 3. 과제 요구조건 충족 현황
* **1,000건 이상**: 12,000건 만족
* **8개 이상 컬럼**: 10개 컬럼 만족
* **멀티모달 3종 이상**: 수치형 + 범주형 + 날짜형 + 텍스트 + 이미지 (5종 모두 포함)
* **결측치 포함 여부**: `customer_id`(3,502건), `product_name`(42건) 결측치 포함 (결측치 정제 실습 가능)

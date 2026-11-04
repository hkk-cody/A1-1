class DataAnalyzer:
    """이커머스 데이터 전처리, 피처 엔지니어링, 요약 통계, RFM을 수행한다."""

    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None

    def load_data(self, date_cols=None):
        # TODO: 읽기, 날짜 변환, self.df 저장
        pass

    def add_image_features(self, image_col):  # 이름 자유
        pass

    def add_text_features(self, text_col):  # 이름 자유
        pass

    def handle_missing_values(
        self, strategy="group_median", group_col=None, columns=None
    ):
        pass

    def detect_outliers(self, column, threshold=1.5):
        pass

    def calculate_rfm(self, customer_col, date_col, amount_col, reference_date=None):
        pass

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# pipeline.py 위치(src/)의 상위 폴더를 프로젝트 루트로 고정
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DataAnalyzer:
    """이커머스 데이터 전처리, 피처 엔지니어링, 요약 통계, RFM을 수행한다."""

    def __init__(self, data_path):
        self.data_path = data_path
        self._df: pd.DataFrame | None = None

    @property
    def df(self) -> pd.DataFrame:
        """데이터가 로드되었는지 자동으로 검사하고 DataFrame을 반환합니다."""
        if self._df is None:
            raise ValueError(
                "데이터가 로드되지 않았습니다. load_data()를 먼저 호출하세요."
            )
        return self._df

    @df.setter
    def df(self, value: pd.DataFrame | None):
        self._df = value

    def load_data(self, date_cols=None):
        """CSV 파일을 읽어 DataFrame으로 로드합니다. date_cols를 지정하면 해당 컬럼을 datetime으로 변환합니다."""
        if date_cols is None:
            date_cols = ["order_date"]
        elif isinstance(date_cols, str):
            date_cols = [date_cols]
        self.df = pd.read_csv(self.data_path, parse_dates=date_cols)

        if "amount" not in self.df.columns and {"unit_price", "quantity"}.issubset(
            self.df.columns
        ):
            self.df["amount"] = self.df["unit_price"] * self.df["quantity"]

        return self.df

    def add_image_features(self, image_col="image_path", base_dir=None):
        """상품 이미지의 평균(img_mean)과 표준편차(img_std)를 NumPy 벡터 연산으로 계산하여 추가합니다."""
        root = Path(base_dir) if base_dir else PROJECT_ROOT

        unique_paths = self.df[image_col].dropna().unique()
        img_list = [plt.imread(root / p)[:, :, :3] for p in unique_paths]
        imgs = np.stack(img_list)  # shape: (N, H, W, 3)

        means = imgs.mean(axis=(1, 2, 3))  # 이미지 밝기
        stds = imgs.std(axis=(1, 2, 3))  # 이미지 대비

        mean_map = dict(zip(unique_paths, means))
        std_map = dict(zip(unique_paths, stds))

        self.df["img_mean"] = self.df[image_col].map(mean_map.get)
        self.df["img_std"] = self.df[image_col].map(std_map.get)

        return self.df

    def add_text_features(self, text_col="product_name"):
        """상품명에서 글자 수와 단어 수를 추출하여 파생 컬럼을 추가합니다."""
        text_series = self.df[text_col].fillna("").astype(str)
        self.df["name_len"] = text_series.str.len()
        self.df["name_word_count"] = text_series.str.split().str.len()

        return self.df

    def handle_missing_values(
        self,
        strategy: Literal[
            "group_median", "group_mean", "median", "mean"
        ] = "group_median",
        group_col="category",
        columns="unit_price",
    ):
        """결측치를 처리합니다. strategy에 따라 'group_median', 'group_mean', 'median', 'mean'을 선택할 수 있습니다."""
        cols = [columns] if isinstance(columns, str) else list(columns)
        stat = strategy.removeprefix("group_")

        if strategy.startswith("group_"):
            fill_val: pd.DataFrame | pd.Series = self.df.groupby(group_col)[
                cols
            ].transform(stat)
        else:
            fill_val = self.df[cols].agg(stat)
        self.df[cols] = self.df[cols].fillna(fill_val)

        if {"unit_price", "quantity"}.issubset(self.df.columns):
            self.df["amount"] = self.df["unit_price"] * self.df["quantity"]

        return self.df

    def detect_outliers(self, column, threshold=1.5):
        """IQR(사분위수 범위) 방식으로 지정한 수치형 컬럼의 이상치를 탐지하여 반환합니다."""
        q1 = self.df[column].quantile(0.25)
        q3 = self.df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr

        return self.df.loc[(self.df[column] < lower) | (self.df[column] > upper)]

    def calculate_rfm(
        self,
        customer_col="customer_id",
        date_col="order_date",
        amount_col="amount",
        reference_date=None,
    ):
        """고객별 Recency, Frequency, Monetary 지표와 세그먼트를 계산하여 반환합니다."""
        # 1. 데이터 정제 및 순수 날짜(연-월-일) 추출
        valid_df: pd.DataFrame = self.df.dropna(
            subset=[customer_col, date_col, amount_col]
        ).copy()
        valid_df = valid_df.loc[valid_df[amount_col] > 0]
        valid_df[date_col] = pd.to_datetime(valid_df[date_col]).dt.normalize()

        # 2. 분석 기준일(reference_date) 설정 및 해당 시점까지의 거래 필터링
        if reference_date is None:
            ref_date = valid_df[date_col].max() + pd.Timedelta(days=1)
        else:
            try:
                ref_date = pd.to_datetime(reference_date).normalize()
            except Exception as e:
                raise ValueError(
                    f"올바른 날짜 형식이 아닙니다: {reference_date}"
                ) from e

            valid_df = valid_df.loc[valid_df[date_col] <= ref_date]
            if valid_df.empty:
                raise ValueError(
                    f"지정한 기준일({reference_date}) 이전에 발생한 거래 내역이 없습니다."
                )

        # 3. 고객별 R, F, M 집계
        freq_col = "invoice_no" if "invoice_no" in valid_df.columns else date_col
        freq_func = "nunique" if "invoice_no" in valid_df.columns else "count"

        rfm = (
            valid_df.groupby(customer_col)
            .agg(
                recency=(date_col, "max"),
                frequency=(freq_col, freq_func),
                monetary=(amount_col, "sum"),
            )
            .reset_index()
        )
        rfm["recency"] = (ref_date - rfm["recency"]).dt.days

        # 4. 동점자에게 동일한 점수를 부여하는 백분위 기반 4분위 점수(1~4점) 계산
        r_pct = rfm["recency"].rank(method="max", ascending=False, pct=True)
        f_pct = rfm["frequency"].rank(method="min", ascending=True, pct=True)
        m_pct = rfm["monetary"].rank(method="min", ascending=True, pct=True)

        bins = [0, 0.25, 0.5, 0.75, 1.0]
        rfm["r_score"] = pd.cut(r_pct, bins=bins, labels=[1, 2, 3, 4])
        rfm["f_score"] = pd.cut(f_pct, bins=bins, labels=[1, 2, 3, 4])
        rfm["m_score"] = pd.cut(m_pct, bins=bins, labels=[1, 2, 3, 4])

        score_cols = ["r_score", "f_score", "m_score"]
        rfm[score_cols] = rfm[score_cols].astype(int)
        rfm["rfm_score"] = rfm[score_cols].sum(axis=1)

        # 5. 고객 세그먼트 분류 (VIP, Loyal, New, Churned)
        conditions = [
            # 1. VIP : 총점 10점 이상이면서 반드시 2회 이상 재구매한 최상위 핵심 단골
            (rfm["rfm_score"] >= 10) & (rfm["frequency"] >= 2),
            # 2. Loyal : 2회 이상 재구매했거나 총점 8점 이상인 우수 충성 고객
            (rfm["frequency"] >= 2) | (rfm["rfm_score"] >= 8),
            # 3. New : 최근성 점수(r_score) 3점 이상이면서 첫 구매(1회)인 신규 고객
            (rfm["frequency"] == 1) & (rfm["r_score"] >= 3),
        ]
        choices = ["VIP", "Loyal", "New"]
        rfm["segment"] = np.select(conditions, choices, default="Churned")

        return rfm

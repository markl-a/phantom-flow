"""RFM (Recency, Frequency, Monetary) analysis for customer segmentation."""

from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
from loguru import logger


class RFMAnalyzer:
    """Perform RFM analysis on customer transaction data."""

    def __init__(
        self,
        df: pd.DataFrame,
        customer_id_col: str,
        date_col: str,
        amount_col: str,
        reference_date: Optional[datetime] = None
    ):
        """
        Initialize the RFM Analyzer.

        Args:
            df: DataFrame containing transaction data
            customer_id_col: Column name for customer ID
            date_col: Column name for transaction date
            amount_col: Column name for transaction amount
            reference_date: Reference date for recency calculation (default: max date in data)
        """
        self.df = df.copy()
        self.customer_id_col = customer_id_col
        self.date_col = date_col
        self.amount_col = amount_col

        # Convert date column to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(self.df[date_col]):
            self.df[date_col] = pd.to_datetime(self.df[date_col])

        # Set reference date
        if reference_date is None:
            self.reference_date = self.df[date_col].max()
        else:
            self.reference_date = pd.to_datetime(reference_date)

        self.rfm_df = None

    def calculate_rfm(self) -> pd.DataFrame:
        """
        Calculate RFM metrics for each customer.

        Returns:
            DataFrame with RFM metrics
        """
        logger.info("Calculating RFM metrics...")

        # Calculate Recency, Frequency, and Monetary using named aggregation.
        # The previous version used a positional agg dict that included
        # `self.customer_id_col: 'count'` — but that's also the groupby
        # key, so after .reset_index() pandas tried to insert it as a
        # column and failed with "cannot insert CustomerID, already exists".
        # Named-aggregation here avoids the collision: Frequency uses
        # date_col as its source (any non-null column gives the row count).
        rfm = self.df.groupby(self.customer_id_col).agg(
            Recency=(self.date_col, lambda x: (self.reference_date - x.max()).days),
            Frequency=(self.date_col, 'count'),
            Monetary=(self.amount_col, 'sum'),
        ).reset_index()

        # Ensure Monetary is positive
        rfm = rfm[rfm['Monetary'] > 0]

        logger.success(f"Calculated RFM for {len(rfm)} customers")

        self.rfm_df = rfm
        return rfm

    def assign_rfm_scores(
        self,
        recency_bins: Optional[List[int]] = None,
        frequency_bins: Optional[List[int]] = None,
        monetary_bins: Optional[List[float]] = None,
        score_labels: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Assign RFM scores to customers based on quartiles or custom bins.

        Args:
            recency_bins: Custom bins for recency (lower is better)
            frequency_bins: Custom bins for frequency (higher is better)
            monetary_bins: Custom bins for monetary (higher is better)
            score_labels: Labels for scores (default: [1, 2, 3, 4, 5])

        Returns:
            DataFrame with RFM scores
        """
        if self.rfm_df is None:
            self.calculate_rfm()

        logger.info("Assigning RFM scores...")

        rfm = self.rfm_df.copy()

        # Default score labels (5-point scale)
        if score_labels is None:
            score_labels = [1, 2, 3, 4, 5]

        # Assign Recency score (lower recency = higher score)
        if recency_bins:
            rfm['R_Score'] = pd.cut(
                rfm['Recency'],
                bins=recency_bins,
                labels=score_labels[::-1],  # Reverse for recency
                include_lowest=True
            )
        else:
            rfm['R_Score'] = pd.qcut(
                rfm['Recency'],
                q=len(score_labels),
                labels=score_labels[::-1],
                duplicates='drop'
            )

        # Assign Frequency score (higher frequency = higher score)
        if frequency_bins:
            rfm['F_Score'] = pd.cut(
                rfm['Frequency'],
                bins=frequency_bins,
                labels=score_labels,
                include_lowest=True
            )
        else:
            rfm['F_Score'] = pd.qcut(
                rfm['Frequency'],
                q=len(score_labels),
                labels=score_labels,
                duplicates='drop'
            )

        # Assign Monetary score (higher monetary = higher score)
        if monetary_bins:
            rfm['M_Score'] = pd.cut(
                rfm['Monetary'],
                bins=monetary_bins,
                labels=score_labels,
                include_lowest=True
            )
        else:
            rfm['M_Score'] = pd.qcut(
                rfm['Monetary'],
                q=len(score_labels),
                labels=score_labels,
                duplicates='drop'
            )

        # Convert scores to integers
        rfm['R_Score'] = rfm['R_Score'].astype(int)
        rfm['F_Score'] = rfm['F_Score'].astype(int)
        rfm['M_Score'] = rfm['M_Score'].astype(int)

        # Calculate RFM Score (concatenated)
        rfm['RFM_Score'] = (
            rfm['R_Score'].astype(str) +
            rfm['F_Score'].astype(str) +
            rfm['M_Score'].astype(str)
        )

        # Calculate RFM Score (averaged)
        rfm['RFM_Score_Avg'] = (
            rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
        ) / 3

        logger.success("RFM scores assigned successfully")

        self.rfm_df = rfm
        return rfm

    def segment_customers(self) -> pd.DataFrame:
        """
        Segment customers based on RFM scores.

        Returns:
            DataFrame with customer segments
        """
        if self.rfm_df is None or 'RFM_Score' not in self.rfm_df.columns:
            self.assign_rfm_scores()

        logger.info("Segmenting customers...")

        rfm = self.rfm_df.copy()

        # 使用向量化操作進行客戶分群（性能優化）
        # 相比 .apply(axis=1)，向量化操作可提升 10-100 倍性能
        rfm['Segment'] = self._assign_segment_vectorized(rfm)

        logger.success("Customer segmentation completed")

        self.rfm_df = rfm
        return rfm

    def _assign_segment_vectorized(self, df: pd.DataFrame) -> pd.Series:
        """
        使用向量化操作分配客戶分群。

        性能優化：使用布爾掩碼替代 .apply(axis=1)，
        對於大型數據集可提升 10-100 倍性能。

        Args:
            df: RFM DataFrame with R_Score, F_Score, M_Score columns

        Returns:
            Series containing segment labels
        """
        r = df['R_Score']
        f = df['F_Score']
        m = df['M_Score']

        # 初始化所有行為 'Lost' (默認值)
        segments = pd.Series('Lost', index=df.index, dtype='object')

        # 按照與原始 if-elif 鏈相反的順序應用條件
        # 這樣優先級更高的條件會覆蓋優先級低的

        # Hibernating: Low recency, frequency, and monetary
        mask = (r <= 2) & (f <= 2) & (m <= 2)
        segments[mask] = 'Hibernating'

        # Can't Lose Them: Were best customers, now gone
        # 注意：此條件在原邏輯中實際上無法到達，因為會被 Loyal Customers 捕獲
        mask = (f >= 4) & (m >= 4)
        segments[mask] = "Can't Lose Them"

        # At Risk: Low recency, but were frequent/high spenders
        # 注意：此條件在原邏輯中實際上無法到達，因為會被 Need Attention 捕獲
        mask = (f >= 3) | (m >= 3)
        segments[mask] = 'At Risk'

        # About to Sleep: Below average recency, frequency, and monetary
        mask = (r == 2) & (f == 2)
        segments[mask] = 'About to Sleep'

        # Need Attention: Above average recency, frequency, and monetary
        mask = (r >= 3) | (f >= 3) | (m >= 3)
        segments[mask] = 'Need Attention'

        # Promising: Recent, moderate spenders
        mask = (r >= 3) & (m >= 3)
        segments[mask] = 'Promising'

        # Recent Customers: Very recent, low frequency
        mask = (r >= 4) & (f <= 2)
        segments[mask] = 'Recent Customers'

        # Potential Loyalists: Recent, good frequency
        mask = (r >= 3) & (f >= 3)
        segments[mask] = 'Potential Loyalists'

        # Loyal Customers: Frequent, high spenders
        mask = (f >= 4) & (m >= 4)
        segments[mask] = 'Loyal Customers'

        # Champions: Recent, frequent, high spenders (highest priority)
        mask = (r >= 4) & (f >= 4) & (m >= 4)
        segments[mask] = 'Champions'

        return segments

    def get_segment_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for each segment.

        Returns:
            DataFrame with segment statistics
        """
        if self.rfm_df is None or 'Segment' not in self.rfm_df.columns:
            self.segment_customers()

        logger.info("Generating segment summary...")

        summary = self.rfm_df.groupby('Segment').agg({
            self.customer_id_col: 'count',
            'Recency': ['mean', 'median'],
            'Frequency': ['mean', 'median'],
            'Monetary': ['mean', 'median', 'sum'],
            'RFM_Score_Avg': 'mean'
        }).round(2)

        # Flatten column names
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]

        # Rename customer count column
        summary = summary.rename(columns={f'{self.customer_id_col}_count': 'Customer_Count'})

        # Add percentage
        summary['Percentage'] = (summary['Customer_Count'] / summary['Customer_Count'].sum() * 100).round(2)

        # Sort by customer count
        summary = summary.sort_values('Customer_Count', ascending=False)

        logger.success("Segment summary generated")

        return summary.reset_index()

    def get_top_customers(self, n: int = 100, by: str = 'RFM_Score_Avg') -> pd.DataFrame:
        """
        Get top N customers by specified metric.

        Args:
            n: Number of customers to return
            by: Metric to sort by ('RFM_Score_Avg', 'Monetary', 'Frequency')

        Returns:
            DataFrame with top customers
        """
        if self.rfm_df is None:
            self.calculate_rfm()

        if by not in self.rfm_df.columns:
            raise ValueError(f"Column '{by}' not found in RFM data")

        return self.rfm_df.nlargest(n, by)

    def export_results(self, filename: str, include_segments: bool = True) -> str:
        """
        Export RFM results to CSV.

        Args:
            filename: Output filename
            include_segments: Include segment information

        Returns:
            Path to exported file
        """
        if include_segments and (self.rfm_df is None or 'Segment' not in self.rfm_df.columns):
            self.segment_customers()
        elif self.rfm_df is None:
            self.calculate_rfm()

        self.rfm_df.to_csv(filename, index=False)
        logger.success(f"RFM results exported to {filename}")

        return filename

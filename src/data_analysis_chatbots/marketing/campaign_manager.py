"""Marketing campaign management and customer targeting."""

from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from loguru import logger


class CampaignManager:
    """Manage marketing campaigns and customer targeting."""

    def __init__(self, customer_df: pd.DataFrame, customer_id_col: str = 'CustomerID'):
        """
        Initialize the Campaign Manager.

        Args:
            customer_df: DataFrame with customer data
            customer_id_col: Column name for customer ID
        """
        self.customer_df = customer_df.copy()
        self.customer_id_col = customer_id_col
        self.campaigns = {}

    def create_campaign(
        self,
        campaign_name: str,
        target_criteria: Dict[str, Any],
        campaign_details: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Create a marketing campaign with target criteria.

        Args:
            campaign_name: Name of the campaign
            target_criteria: Dictionary with targeting criteria
            campaign_details: Additional campaign details

        Returns:
            DataFrame with targeted customers
        """
        logger.info(f"Creating campaign: {campaign_name}")

        df = self.customer_df.copy()

        # Apply targeting criteria
        mask = pd.Series([True] * len(df))

        for column, criteria in target_criteria.items():
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found in customer data")
                continue

            if isinstance(criteria, dict):
                # Handle range criteria
                if 'min' in criteria:
                    mask &= df[column] >= criteria['min']
                if 'max' in criteria:
                    mask &= df[column] <= criteria['max']
                if 'in' in criteria:
                    mask &= df[column].isin(criteria['in'])
                if 'not_in' in criteria:
                    mask &= ~df[column].isin(criteria['not_in'])
            else:
                # Handle exact match
                mask &= df[column] == criteria

        targeted_customers = df[mask].copy()

        # Store campaign
        self.campaigns[campaign_name] = {
            'criteria': target_criteria,
            'details': campaign_details or {},
            'target_count': len(targeted_customers),
            'target_customers': targeted_customers[self.customer_id_col].tolist()
        }

        logger.success(f"Campaign '{campaign_name}' created with {len(targeted_customers)} targeted customers")

        return targeted_customers

    def segment_by_demographics(
        self,
        age_ranges: Optional[List[Tuple[int, int, str]]] = None,
        gender: Optional[str] = None,
        income_ranges: Optional[List[Tuple[float, float, str]]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Segment customers by demographics.

        Args:
            age_ranges: List of (min_age, max_age, label) tuples
            gender: Gender filter
            income_ranges: List of (min_income, max_income, label) tuples

        Returns:
            Dictionary of segments
        """
        logger.info("Segmenting customers by demographics...")

        segments = {}
        df = self.customer_df.copy()

        if age_ranges and 'Age' in df.columns:
            for min_age, max_age, label in age_ranges:
                mask = (df['Age'] >= min_age) & (df['Age'] <= max_age)
                if gender and 'Gender' in df.columns:
                    mask &= df['Gender'] == gender
                segments[label] = df[mask].copy()

        if income_ranges:
            income_col = self._find_income_column()
            if income_col:
                for min_income, max_income, label in income_ranges:
                    mask = (df[income_col] >= min_income) & (df[income_col] <= max_income)
                    segments[label] = df[mask].copy()

        logger.success(f"Created {len(segments)} demographic segments")

        return segments

    def _find_income_column(self) -> Optional[str]:
        """Find income column in DataFrame."""
        income_keywords = ['income', 'salary', 'annual income']
        for col in self.customer_df.columns:
            if any(keyword in col.lower() for keyword in income_keywords):
                return col
        return None

    def target_high_value_customers(
        self,
        value_column: str,
        top_n: Optional[int] = None,
        top_percentile: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Target high-value customers.

        Args:
            value_column: Column to use for value determination
            top_n: Number of top customers to target
            top_percentile: Percentile threshold (e.g., 0.9 for top 10%)

        Returns:
            DataFrame with high-value customers
        """
        logger.info("Targeting high-value customers...")

        df = self.customer_df.copy()

        if value_column not in df.columns:
            raise ValueError(f"Column '{value_column}' not found")

        if top_n:
            targeted = df.nlargest(top_n, value_column)
        elif top_percentile:
            threshold = df[value_column].quantile(top_percentile)
            targeted = df[df[value_column] >= threshold]
        else:
            raise ValueError("Must specify either top_n or top_percentile")

        logger.success(f"Targeted {len(targeted)} high-value customers")

        return targeted

    def target_at_risk_customers(
        self,
        recency_column: str,
        recency_threshold: int,
        value_column: Optional[str] = None,
        min_value: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Target at-risk customers (high recency, but valuable).

        Args:
            recency_column: Column with recency data
            recency_threshold: Threshold for considering customer at risk
            value_column: Column for customer value (optional)
            min_value: Minimum value threshold (optional)

        Returns:
            DataFrame with at-risk customers
        """
        logger.info("Targeting at-risk customers...")

        df = self.customer_df.copy()

        # High recency means at risk
        mask = df[recency_column] > recency_threshold

        # But should have been valuable
        if value_column and min_value is not None:
            mask &= df[value_column] >= min_value

        targeted = df[mask]

        logger.success(f"Identified {len(targeted)} at-risk customers")

        return targeted

    def create_personalized_offers(
        self,
        df: pd.DataFrame,
        segment_column: str,
        offer_mapping: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Create personalized offers for customer segments.

        Args:
            df: DataFrame with customers
            segment_column: Column with segment labels
            offer_mapping: Dictionary mapping segments to offers

        Returns:
            DataFrame with personalized offers
        """
        logger.info("Creating personalized offers...")

        result = df.copy()

        # Add offer columns
        result['Offer_Type'] = result[segment_column].map(
            lambda x: offer_mapping.get(x, {}).get('type', 'Standard')
        )
        result['Discount_Percentage'] = result[segment_column].map(
            lambda x: offer_mapping.get(x, {}).get('discount', 0)
        )
        result['Offer_Description'] = result[segment_column].map(
            lambda x: offer_mapping.get(x, {}).get('description', 'No special offer')
        )

        logger.success(f"Created offers for {len(result)} customers")

        return result

    def calculate_campaign_roi(
        self,
        campaign_name: str,
        cost_per_customer: float,
        conversion_rate: float,
        avg_revenue_per_conversion: float
    ) -> Dict[str, float]:
        """
        Calculate expected ROI for a campaign.

        Args:
            campaign_name: Name of the campaign
            cost_per_customer: Cost to reach each customer
            conversion_rate: Expected conversion rate (0-1)
            avg_revenue_per_conversion: Average revenue per conversion

        Returns:
            Dictionary with ROI metrics
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        campaign = self.campaigns[campaign_name]
        target_count = campaign['target_count']

        total_cost = target_count * cost_per_customer
        expected_conversions = target_count * conversion_rate
        expected_revenue = expected_conversions * avg_revenue_per_conversion
        expected_profit = expected_revenue - total_cost
        roi = (expected_profit / total_cost * 100) if total_cost > 0 else 0

        return {
            'campaign_name': campaign_name,
            'target_customers': target_count,
            'total_cost': round(total_cost, 2),
            'expected_conversions': round(expected_conversions, 2),
            'expected_revenue': round(expected_revenue, 2),
            'expected_profit': round(expected_profit, 2),
            'roi_percentage': round(roi, 2)
        }

    def export_campaign_list(
        self,
        campaign_name: str,
        filename: str,
        include_details: bool = True
    ) -> str:
        """
        Export campaign customer list to CSV.

        Args:
            campaign_name: Name of the campaign
            filename: Output filename
            include_details: Include customer details

        Returns:
            Path to exported file
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        campaign = self.campaigns[campaign_name]
        customer_ids = campaign['target_customers']

        if include_details:
            export_df = self.customer_df[
                self.customer_df[self.customer_id_col].isin(customer_ids)
            ].copy()
        else:
            export_df = pd.DataFrame({self.customer_id_col: customer_ids})

        export_df.to_csv(filename, index=False)
        logger.success(f"Campaign list exported to {filename}")

        return filename

    def get_campaign_summary(self) -> pd.DataFrame:
        """
        Get summary of all campaigns.

        Returns:
            DataFrame with campaign summary
        """
        if not self.campaigns:
            logger.warning("No campaigns created yet")
            return pd.DataFrame()

        summary_data = []
        for name, campaign in self.campaigns.items():
            summary_data.append({
                'Campaign': name,
                'Target_Count': campaign['target_count'],
                'Criteria': str(campaign['criteria'])
            })

        return pd.DataFrame(summary_data)

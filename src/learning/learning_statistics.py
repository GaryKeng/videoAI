"""
Learning statistics and visualization.
"""
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

from src.database.models import LearningRecord, GlobalLearningRecord, get_session


class LearningStatistics:
    """Track and visualize learning statistics."""

    def __init__(self):
        self.session = get_session()

    def get_total_adjustments(self) -> int:
        """Get total number of user adjustments."""
        return self.session.query(LearningRecord).filter(
            LearningRecord.user_adjusted_match == True
        ).count()

    def get_adjustments_by_type(self) -> Dict[str, int]:
        """Get adjustment counts by type."""
        records = self.session.query(LearningRecord).filter(
            LearningRecord.user_adjusted_match == True
        ).all()

        counts = defaultdict(int)
        for record in records:
            counts[record.adjustment_type or "unknown"] += 1

        return dict(counts)

    def get_adjustments_over_time(self, days: int = 30) -> List[Dict]:
        """Get adjustments over time period."""
        start_date = datetime.now() - timedelta(days=days)

        records = self.session.query(LearningRecord).filter(
            LearningRecord.user_adjusted_match == True,
            LearningRecord.last_updated >= start_date
        ).order_by(LearningRecord.last_updated).all()

        result = []
        for record in records:
            result.append({
                "date": record.last_updated.isoformat(),
                "type": record.adjustment_type,
                "frequency": record.frequency
            })

        return result

    def get_top_patterns(self, limit: int = 10) -> List[Dict]:
        """Get most frequently adjusted patterns."""
        records = self.session.query(LearningRecord).filter(
            LearningRecord.frequency >= 2
        ).order_by(LearningRecord.frequency.desc()).limit(limit).all()

        result = []
        for record in records:
            result.append({
                "subtitle_text": record.subtitle_text[:50],
                "ocr_text": record.ocr_text[:50],
                "frequency": record.frequency,
                "adjustment_type": record.adjustment_type
            })

        return result

    def get_success_rate(self) -> float:
        """Get AI match success rate."""
        total = self.session.query(LearningRecord).count()
        if total == 0:
            return 0.0

        not_adjusted = self.session.query(LearningRecord).filter(
            LearningRecord.user_adjusted_match == False
        ).count()

        return (total - not_adjusted) / total if total > 0 else 0.0

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        return {
            "total_adjustments": self.get_total_adjustments(),
            "adjustments_by_type": self.get_adjustments_by_type(),
            "success_rate": self.get_success_rate(),
            "top_patterns": self.get_top_patterns()
        }


class LearningHistoryWidget:
    """Widget to display learning history."""

    def __init__(self):
        self.stats = LearningStatistics()

    def get_html_report(self) -> str:
        """Generate HTML report of learning statistics."""
        summary = self.stats.get_summary()

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 20px; }}
                .stat {{ margin: 10px 0; }}
                .success {{ color: green; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4a4a8a; color: white; }}
            </style>
        </head>
        <body>
            <h1>VideoAI Learning Statistics</h1>

            <h2>Overview</h2>
            <div class="stat">Total Adjustments: {summary['total_adjustments']}</div>
            <div class="stat">AI Success Rate: <span class="success">{summary['success_rate']:.1%}</span></div>

            <h2>Adjustments by Type</h2>
            <table>
                <tr><th>Type</th><th>Count</th></tr>
        """

        for adj_type, count in summary.get("adjustments_by_type", {}).items():
            html += f"<tr><td>{adj_type}</td><td>{count}</td></tr>"

        html += """
            </table>

            <h2>Top Patterns</h2>
            <table>
                <tr><th>Subtitle</th><th>OCR Text</th><th>Frequency</th><th>Last Adjustment</th></tr>
        """

        for pattern in summary.get("top_patterns", []):
            html += f"""
                <tr>
                    <td>{pattern['subtitle_text']}</td>
                    <td>{pattern['ocr_text']}</td>
                    <td>{pattern['frequency']}</td>
                    <td>{pattern['adjustment_type']}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

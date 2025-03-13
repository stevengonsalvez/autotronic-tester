"""
Report generator for AutoGen 0.4 that creates HTML reports from event data.
"""
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates HTML reports from AutoGen event data stored in SQLite.
    
    This class reads event data from a SQLite database and generates
    interactive HTML reports with visualizations of token usage,
    conversation flow, and other metrics.
    """
    
    def __init__(self, db_path: Union[str, Path] = "runtime_logs/autogen_logs.db"):
        """
        Initialize the report generator.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            logger.warning(f"Database file not found at {self.db_path}")
    
    def _get_llm_calls_df(self, session_id: Optional[str] = None) -> pd.DataFrame:
        """Get LLM calls as a DataFrame."""
        if not self.db_path.exists():
            return pd.DataFrame()
            
        conn = sqlite3.connect(str(self.db_path))
        
        query = "SELECT * FROM llm_calls"
        params = []
        
        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            
        return df
    
    def _get_events_df(self, session_id: Optional[str] = None) -> pd.DataFrame:
        """Get events as a DataFrame."""
        if not self.db_path.exists():
            return pd.DataFrame()
            
        conn = sqlite3.connect(str(self.db_path))
        
        query = "SELECT * FROM events"
        params = []
        
        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            
        return df
    
    def generate_token_usage_chart(self, session_id: Optional[str] = None) -> go.Figure:
        """Generate a chart of token usage over time."""
        df = self._get_llm_calls_df(session_id)
        
        if df.empty:
            # Create an empty figure with a message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Create a figure with two y-axes
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add cumulative token usage
        df['cumulative_tokens'] = df['total_tokens'].cumsum()
        
        # Add individual token usage bars
        fig.add_trace(
            go.Bar(
                x=df['datetime'],
                y=df['prompt_tokens'],
                name='Prompt Tokens',
                marker_color='blue'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Bar(
                x=df['datetime'],
                y=df['completion_tokens'],
                name='Completion Tokens',
                marker_color='green'
            ),
            secondary_y=False
        )
        
        # Add cumulative line
        fig.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df['cumulative_tokens'],
                name='Cumulative Tokens',
                line=dict(color='red', width=2)
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
            title='Token Usage Over Time',
            xaxis_title='Time',
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Tokens per Request", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative Tokens", secondary_y=True)
        
        return fig
    
    def generate_agent_activity_chart(self, session_id: Optional[str] = None) -> go.Figure:
        """Generate a chart of agent activity over time."""
        df = self._get_events_df(session_id)
        
        if df.empty:
            # Create an empty figure with a message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Count events by agent and type
        agent_events = df.groupby(['agent_id', 'event_type']).size().reset_index(name='count')
        
        # Create the figure
        fig = px.bar(
            agent_events,
            x='agent_id',
            y='count',
            color='event_type',
            title='Agent Activity by Event Type',
            labels={'agent_id': 'Agent', 'count': 'Number of Events', 'event_type': 'Event Type'}
        )
        
        return fig
    
    def generate_html_report(self, output_path: Union[str, Path], session_id: Optional[str] = None):
        """
        Generate an HTML report with visualizations.
        
        Args:
            output_path: Path where the HTML report will be saved
            session_id: Optional session ID to filter by
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get data
        llm_calls_df = self._get_llm_calls_df(session_id)
        events_df = self._get_events_df(session_id)
        
        # Calculate statistics
        if llm_calls_df.empty:
            stats = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "request_count": 0,
                "prompt_cost": 0,
                "completion_cost": 0,
                "total_cost": 0
            }
        else:
            stats = {
                "prompt_tokens": llm_calls_df['prompt_tokens'].sum(),
                "completion_tokens": llm_calls_df['completion_tokens'].sum(),
                "total_tokens": llm_calls_df['total_tokens'].sum(),
                "request_count": len(llm_calls_df),
                "prompt_cost": round(llm_calls_df['prompt_tokens'].sum() * 0.03 / 1000, 4),
                "completion_cost": round(llm_calls_df['completion_tokens'].sum() * 0.06 / 1000, 4)
            }
            stats["total_cost"] = round(stats["prompt_cost"] + stats["completion_cost"], 4)
        
        # Generate charts
        token_chart = self.generate_token_usage_chart(session_id)
        agent_chart = self.generate_agent_activity_chart(session_id)
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AutoGen Session Report</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .stats-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }}
                .stat-box {{
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    padding: 15px;
                    width: calc(33% - 20px);
                    margin-bottom: 20px;
                    box-shadow: 0 0 5px rgba(0,0,0,0.05);
                }}
                .stat-box h3 {{
                    margin-top: 0;
                    color: #333;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #0066cc;
                }}
                .chart-container {{
                    margin-bottom: 30px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AutoGen Session Report</h1>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    {f'<p>Session ID: {session_id}</p>' if session_id else ''}
                </div>
                
                <div class="stats-container">
                    <div class="stat-box">
                        <h3>Total Requests</h3>
                        <div class="stat-value">{stats['request_count']}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Total Tokens</h3>
                        <div class="stat-value">{stats['total_tokens']}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Total Cost</h3>
                        <div class="stat-value">${stats['total_cost']}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Prompt Tokens</h3>
                        <div class="stat-value">{stats['prompt_tokens']}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Completion Tokens</h3>
                        <div class="stat-value">{stats['completion_tokens']}</div>
                    </div>
                    <div class="stat-box">
                        <h3>Avg. Tokens per Request</h3>
                        <div class="stat-value">{round(stats['total_tokens'] / stats['request_count'], 2) if stats['request_count'] > 0 else 0}</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h2>Token Usage Over Time</h2>
                    <div id="token-chart"></div>
                </div>
                
                <div class="chart-container">
                    <h2>Agent Activity</h2>
                    <div id="agent-chart"></div>
                </div>
                
                <div class="footer">
                    <p>Generated by AutoGen Playwright Report Generator</p>
                </div>
            </div>
            
            <script>
                // Token usage chart
                var tokenChartData = {token_chart.to_json()};
                Plotly.newPlot('token-chart', tokenChartData.data, tokenChartData.layout);
                
                // Agent activity chart
                var agentChartData = {agent_chart.to_json()};
                Plotly.newPlot('agent-chart', agentChartData.data, agentChartData.layout);
            </script>
        </body>
        </html>
        """
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)
            
        logger.info(f"Generated HTML report at {output_path}")
        return output_path 
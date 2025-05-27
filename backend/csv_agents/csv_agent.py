import json
import os
from typing import Optional

import pandas as pd
from agents import Agent, Runner, function_tool
from openai import OpenAI
from pydantic import BaseModel

from app.config import settings

# OpenAI API keyを環境変数に設定（トレーシング警告の抑制）
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = settings.openai_api_key

class DataForGraph(BaseModel):
    x: list[str]
    y: list[float]
    x_label: str
    y_label: str

class VisualizationParams(BaseModel):
    type: str
    chart_type: str
    data_for_graph: DataForGraph
    title: str

class ResponseCSVAgent(BaseModel):
    result: str
    visualization_data: Optional[VisualizationParams]

class CSVAgent:
    def __init__(self, df: pd.DataFrame, filename: str):
        self.df = df
        self.filename = filename
        self.client = OpenAI(api_key=settings.openai_api_key)
        
        # エージェントのツールを定義
        self.tools = [
            self._create_get_data_info_tool(),
            self._create_calculate_statistics_tool(),
            self._create_execute_pandas_query_tool(),
            self._create_create_visualization_tool()
        ]
        
        # エージェントを作成
        self.agent = Agent(
            name="CSV Analyst",
            instructions=f"""You are a helpful data analyst working with a CSV file.
            The file '{self.filename}' has been loaded with the following columns: {', '.join(self.df.columns.tolist())}.
            The data has {len(self.df)} rows.
            
            When answering questions:
            1. Always use the provided tools to analyze data
            2. For calculations, use calculate_statistics with appropriate operation
            3. For complex queries, use execute_pandas_query
            4. Create visualizations when it would be helpful
            5. Be precise with column names - they are case-sensitive
            6. Respond in the same language as the user's query
            
            Available columns: {', '.join(self.df.columns.tolist())}
            
            For Japanese queries:
            - "合計" -> Use calculate_statistics with operation='sum'
            - "平均" -> Use calculate_statistics with operation='mean'
            - "グラフ" or "チャート" or "棒グラフ" or "示して" -> Use create_visualization
            - "月別" + "グラフ" -> Use create_visualization with groupby_column parameter
            - "グループ別" -> Use groupby_column parameter in create_visualization or execute appropriate pandas query
            
            IMPORTANT: 
            1. When user asks for visualization (グラフ, チャート, 示して), ALWAYS use create_visualization tool
            2. For "月別の売り上げを棒グラフで示して", use create_visualization with chart_type='bar' and appropriate columns
            3. The create_visualization tool returns VISUALIZATION_PARAMS data, not image data
            """,
            tools=self.tools,
            model="gpt-4o",
            output_type=ResponseCSVAgent
        )
    
    def _create_get_data_info_tool(self):
        """データ情報取得ツールを作成"""
        df = self.df
        filename = self.filename
        
        @function_tool
        def get_data_info() -> str:
            """Get basic information about the dataset"""
            try:
                info = {
                    "filename": filename,
                    "shape": f"{df.shape[0]} rows × {df.shape[1]} columns",
                    "columns": df.columns.tolist(),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "sample_data": df.head(3).to_dict('records')
                }
                return json.dumps(info, ensure_ascii=False, default=str)
            except Exception as e:
                return f"Error getting data info: {str(e)}"
        
        return get_data_info
    
    def _create_calculate_statistics_tool(self):
        """統計計算ツールを作成"""
        df = self.df
        
        @function_tool
        def calculate_statistics(column: str, operation: str = "sum") -> str:
            """Calculate statistics for a specific column
            
            Args:
                column: The column name to calculate statistics for
                operation: The operation to perform (sum, mean, median, min, max, count, std, describe)
            """
            try:
                if column not in df.columns:
                    return f"Error: Column '{column}' not found. Available columns: {', '.join(df.columns.tolist())}"
                
                operations = {
                    "sum": lambda: df[column].sum(),
                    "mean": lambda: df[column].mean(),
                    "median": lambda: df[column].median(),
                    "min": lambda: df[column].min(),
                    "max": lambda: df[column].max(),
                    "count": lambda: df[column].count(),
                    "std": lambda: df[column].std(),
                    "describe": lambda: df[column].describe().to_string()
                }
                
                if operation not in operations:
                    return f"Error: Unknown operation '{operation}'. Use: {', '.join(operations.keys())}"
                
                result = operations[operation]()
                
                if operation == "describe":
                    return result
                
                return f"{operation} of {column}: {result:,.2f}" if isinstance(result, (int, float)) else f"{operation} of {column}: {result}"
                
            except Exception as e:
                return f"Error calculating statistics: {str(e)}"
        
        return calculate_statistics
    
    def _create_execute_pandas_query_tool(self):
        """Pandasクエリ実行ツールを作成"""
        df = self.df  # クロージャでDataFrameを捕捉
        
        @function_tool
        def execute_pandas_query(query: str) -> str:
            """Execute a pandas query on the dataframe
            
            Args:
                query: Pandas query to execute (e.g., "groupby('商品名')['売上金額'].sum()")
            """
            try:
                # セキュリティのため、一部の操作を制限
                forbidden_ops = ['__', 'import', 'open', 'file', 'input', 'raw_input', 'compile', 'globals', 'locals']
                if any(op in query.lower() for op in forbidden_ops):
                    return "Error: Forbidden operation detected"
                
                # DataFrameの参照を使ってクエリを実行
                # クエリがすでに"df."で始まっている場合は追加しない
                if query.strip().startswith('df.'):
                    result = eval(query, {"df": df, "pd": pd})
                else:
                    result = eval(f"df.{query}", {"df": df, "pd": pd})
                
                if isinstance(result, pd.DataFrame):
                    return result.to_string()
                elif isinstance(result, pd.Series):
                    return result.to_string()
                else:
                    return str(result)
                    
            except Exception as e:
                return f"Error executing query: {str(e)}. Make sure the query is valid pandas syntax."
        
        return execute_pandas_query
    
    def _create_create_visualization_tool(self):
        """可視化ツールを作成"""
        df = self.df
        
        @function_tool
        def create_visualization(
            chart_type: str,
            x_column: Optional[str] = None,
            y_column: Optional[str] = None,
            title: Optional[str] = None,
            groupby_column: Optional[str] = None
        ) -> str:
            """Create visualization parameters for frontend rendering
            
            Args:
                chart_type: Type of chart (bar, line, scatter, hist, box, heatmap, pie)
                x_column: Column for x-axis
                y_column: Column for y-axis
                title: Chart title
                groupby_column: Column to group by before plotting
            """
            try:
                # データを準備
                if groupby_column and y_column:
                    # グループ化して集計
                    grouped_data = df.groupby(groupby_column)[y_column].sum().sort_values(ascending=False)
                    chart_data = {
                        "x": [str(x) for x in grouped_data.index.tolist()],
                        "y": [float(y) for y in grouped_data.values.tolist()],
                        "x_label": groupby_column,
                        "y_label": y_column
                    }
                elif x_column and y_column:
                    if x_column == "日付":
                        # 日付でグループ化して集計
                        date_grouped = df.groupby(x_column)[y_column].sum()
                        chart_data = {
                            "x": [str(x) for x in date_grouped.index.tolist()],
                            "y": [float(y) for y in date_grouped.values.tolist()],
                            "x_label": x_column,
                            "y_label": y_column
                        }
                    else:
                        # 通常のx,yデータ
                        chart_data = {
                            "x": [str(x) for x in df[x_column].tolist()],
                            "y": [float(y) for y in df[y_column].tolist()],
                            "x_label": x_column,
                            "y_label": y_column
                        }
                elif x_column:
                    # ヒストグラム用のデータ（yは空リスト）
                    chart_data = {
                        "x": [str(x) for x in df[x_column].tolist()],
                        "y": [],  # ヒストグラムの場合、yは空リスト
                        "x_label": x_column,
                        "y_label": "Frequency"
                    }
                else:
                    return "Error: Missing required columns for visualization"
                
                # 可視化パラメータを返す
                viz_params = VisualizationParams(
                    type="VISUALIZATION_DATA",
                    chart_type=chart_type.lower(),
                    data_for_graph=DataForGraph(**chart_data),
                    title=title or f"{chart_type.title()} Chart"
                )
                
                return viz_params.model_dump_json()
                
            except Exception as e:
                return f"Error preparing visualization: {str(e)}"
        
        return create_visualization
    
    async def process_query(self, query: str) -> ResponseCSVAgent:
        """クエリを処理してレスポンスを生成"""
        try:
            # Runnerを使用してエージェントを実行
            result = await Runner.run(
                self.agent,
                query,
                max_turns=20
            )
            
            # output_type=ResponseCSVAgentを使用しているため、
            # result.final_outputがResponseCSVAgentオブジェクトになる
            if hasattr(result, 'final_output') and isinstance(result.final_output, ResponseCSVAgent):
                return result.final_output
            
            # フォールバック: 期待した形式でない場合
            return ResponseCSVAgent(
                result="予期しないレスポンス形式です。",
                visualization_data=None
            )
            
        except Exception as e:
            return ResponseCSVAgent(
                result=f"エラーが発生しました: {str(e)}",
                visualization_data=None
            )
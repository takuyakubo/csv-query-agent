from agents import Agent, Runner, function_tool
from openai import OpenAI
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, Any, Optional
import asyncio
import json
from app.config import settings


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
            - "グラフ" or "チャート" -> Use create_visualization
            - "グループ別" -> Use groupby_column parameter in create_visualization or execute appropriate pandas query
            """,
            tools=self.tools,
            model="gpt-4o-mini"
        )
    
    def _create_get_data_info_tool(self):
        """データ情報取得ツールを作成"""
        @function_tool
        def get_data_info() -> str:
            """Get basic information about the dataset"""
            try:
                info = {
                    "filename": self.filename,
                    "shape": f"{self.df.shape[0]} rows × {self.df.shape[1]} columns",
                    "columns": self.df.columns.tolist(),
                    "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
                    "sample_data": self.df.head(3).to_dict('records')
                }
                return json.dumps(info, ensure_ascii=False, default=str)
            except Exception as e:
                return f"Error getting data info: {str(e)}"
        
        return get_data_info
    
    def _create_calculate_statistics_tool(self):
        """統計計算ツールを作成"""
        @function_tool
        def calculate_statistics(column: str, operation: str = "sum") -> str:
            """Calculate statistics for a specific column
            
            Args:
                column: The column name to calculate statistics for
                operation: The operation to perform (sum, mean, median, min, max, count, std, describe)
            """
            try:
                if column not in self.df.columns:
                    return f"Error: Column '{column}' not found. Available columns: {', '.join(self.df.columns.tolist())}"
                
                operations = {
                    "sum": lambda: self.df[column].sum(),
                    "mean": lambda: self.df[column].mean(),
                    "median": lambda: self.df[column].median(),
                    "min": lambda: self.df[column].min(),
                    "max": lambda: self.df[column].max(),
                    "count": lambda: self.df[column].count(),
                    "std": lambda: self.df[column].std(),
                    "describe": lambda: self.df[column].describe().to_string()
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
                result = eval(f"self.df.{query}")
                
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
        @function_tool
        def create_visualization(
            chart_type: str,
            x_column: Optional[str] = None,
            y_column: Optional[str] = None,
            title: Optional[str] = None,
            groupby_column: Optional[str] = None
        ) -> str:
            """Create data visualization
            
            Args:
                chart_type: Type of chart (bar, line, scatter, hist, box, heatmap, pie)
                x_column: Column for x-axis
                y_column: Column for y-axis
                title: Chart title
                groupby_column: Column to group by before plotting
            """
            try:
                plt.figure(figsize=(10, 6))
                
                # グループ化が必要な場合
                if groupby_column and y_column:
                    grouped_data = self.df.groupby(groupby_column)[y_column].sum().sort_values(ascending=False)
                    
                    if chart_type.lower() == "bar":
                        grouped_data.plot(kind='bar')
                        plt.xlabel(groupby_column)
                        plt.ylabel(f"Sum of {y_column}")
                        plt.xticks(rotation=45)
                    elif chart_type.lower() == "pie":
                        grouped_data.plot(kind='pie', autopct='%1.1f%%')
                    else:
                        grouped_data.plot()
                
                # 時系列データの場合の特別処理
                elif chart_type.lower() in ["line", "bar"] and x_column == "日付" and y_column:
                    # 日付でグループ化して集計
                    date_grouped = self.df.groupby(x_column)[y_column].sum()
                    
                    if chart_type.lower() == "bar":
                        date_grouped.plot(kind='bar')
                        plt.xticks(rotation=45)
                    else:
                        date_grouped.plot(kind='line', marker='o')
                    
                    plt.xlabel(x_column)
                    plt.ylabel(f"Sum of {y_column}")
                
                # 通常のプロット
                elif chart_type.lower() == "scatter" and x_column and y_column:
                    plt.scatter(self.df[x_column], self.df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                    
                elif chart_type.lower() == "line" and x_column and y_column:
                    plt.plot(self.df[x_column], self.df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                    
                elif chart_type.lower() == "bar" and x_column and y_column:
                    plt.bar(self.df[x_column], self.df[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                    plt.xticks(rotation=45)
                    
                elif chart_type.lower() == "hist" and x_column:
                    plt.hist(self.df[x_column], bins=30, edgecolor='black')
                    plt.xlabel(x_column)
                    plt.ylabel("Frequency")
                    
                elif chart_type.lower() == "box" and y_column:
                    if x_column:
                        self.df.boxplot(column=y_column, by=x_column)
                    else:
                        plt.boxplot(self.df[y_column])
                        plt.ylabel(y_column)
                        
                elif chart_type.lower() == "heatmap":
                    numeric_df = self.df.select_dtypes(include=['float64', 'int64'])
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
                    
                else:
                    return "Error: Invalid chart type or missing required columns"
                
                if title:
                    plt.title(title)
                
                # 画像をbase64エンコード
                buffer = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.read()).decode()
                plt.close()
                
                return f"Visualization created successfully. Image data: data:image/png;base64,{image_base64}"
                
            except Exception as e:
                plt.close()
                return f"Error creating visualization: {str(e)}"
        
        return create_visualization
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """クエリを処理してレスポンスを生成"""
        try:
            print(f"Processing query: {query}")
            
            # Runnerを使用してエージェントを実行
            result = await asyncio.to_thread(
                Runner.run_sync,
                self.agent,
                query,
                max_turns=5
            )
            
            print(f"Agent result: {result}")
            
            # 結果を取得
            final_output = result.final_output if hasattr(result, 'final_output') else str(result)
            
            # 可視化が含まれているかチェック
            visualization = None
            if final_output and "data:image/png;base64," in final_output:
                # Base64画像を抽出
                start = final_output.find("data:image/png;base64,")
                # 画像データの終わりを見つける（スペース、改行、または文字列の終わり）
                end = len(final_output)
                for delimiter in [' ', '\n', '"', "'", ',']:
                    pos = final_output.find(delimiter, start + 22)  # "data:image/png;base64,"の長さ分スキップ
                    if pos != -1 and pos < end:
                        end = pos
                
                visualization = final_output[start:end]
                # 結果から画像部分を削除してメッセージを整形
                final_output = final_output[:start].strip()
                if not final_output:
                    final_output = "グラフを作成しました。"
            
            return {
                "result": final_output,
                "visualization": visualization,
                "data": None
            }
            
        except Exception as e:
            import traceback
            print(f"Error in process_query: {str(e)}")
            print(traceback.format_exc())
            return {
                "result": f"エラーが発生しました: {str(e)}",
                "visualization": None,
                "data": None
            }
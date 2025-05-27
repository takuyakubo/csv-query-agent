from swarm import Swarm, Agent
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
        self.client = Swarm(client=OpenAI(api_key=settings.openai_api_key))
        self.context_variables = {"df": self.df, "filename": self.filename}
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        return Agent(
            name="CSV Analyst",
            instructions=f"""You are a helpful data analyst working with a CSV file named '{self.filename}'.
            The CSV has the following columns: {', '.join(self.df.columns.tolist())}.
            The data has {len(self.df)} rows.
            
            When answering questions:
            1. Always use the provided tools to analyze data
            2. For any calculation or data analysis, use the calculate_statistics or execute_pandas_query tools
            3. Create visualizations when it would be helpful
            4. Be precise with column names - they are case-sensitive
            5. Provide specific numeric results
            
            Available columns: {', '.join(self.df.columns.tolist())}
            
            Example queries you can handle:
            - "売上金額の合計" -> Use calculate_statistics with operation='sum' and column='売上金額'
            - "商品別の売上" -> Use execute_pandas_query with "groupby('商品名')['売上金額'].sum()"
            - "日別の売上推移をグラフで" -> Use create_visualization with appropriate parameters
            """,
            functions=[self.get_data_info, self.calculate_statistics, self.execute_pandas_query, self.create_visualization]
        )
    
    def get_data_info(self) -> str:
        """Get basic information about the dataset"""
        try:
            info = {
                "filename": self.filename,
                "shape": f"{self.df.shape[0]} rows × {self.df.shape[1]} columns",
                "columns": self.df.columns.tolist(),
                "dtypes": self.df.dtypes.to_dict(),
                "sample_data": self.df.head(3).to_dict('records')
            }
            return json.dumps(info, ensure_ascii=False, default=str)
        except Exception as e:
            return f"Error getting data info: {str(e)}"
    
    def calculate_statistics(self, column: str, operation: str = "sum") -> str:
        """Calculate statistics for a specific column
        
        Args:
            column: The column name to calculate statistics for
            operation: The operation to perform (sum, mean, median, min, max, count, std)
        """
        try:
            if column not in self.df.columns:
                return f"Error: Column '{column}' not found. Available columns: {', '.join(self.df.columns.tolist())}"
            
            if operation == "sum":
                result = self.df[column].sum()
            elif operation == "mean":
                result = self.df[column].mean()
            elif operation == "median":
                result = self.df[column].median()
            elif operation == "min":
                result = self.df[column].min()
            elif operation == "max":
                result = self.df[column].max()
            elif operation == "count":
                result = self.df[column].count()
            elif operation == "std":
                result = self.df[column].std()
            elif operation == "describe":
                return self.df[column].describe().to_string()
            else:
                return f"Error: Unknown operation '{operation}'. Use: sum, mean, median, min, max, count, std, describe"
            
            return f"{operation} of {column}: {result:,.2f}" if isinstance(result, (int, float)) else f"{operation} of {column}: {result}"
            
        except Exception as e:
            return f"Error calculating statistics: {str(e)}"
    
    def create_visualization(self, chart_type: str, x_column: Optional[str] = None, 
                           y_column: Optional[str] = None, title: Optional[str] = None) -> str:
        """データの可視化を作成"""
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type.lower() == "scatter" and x_column and y_column:
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
                plt.hist(self.df[x_column], bins=30)
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
                return "Unsupported chart type or missing required columns"
            
            if title:
                plt.title(title)
            
            # 画像をbase64エンコード
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            plt.close()
            return f"Error creating visualization: {str(e)}"
    
    def execute_pandas_query(self, query: str) -> str:
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
            # query は "groupby('商品名')['売上金額'].sum()" のような形式
            result = eval(f"self.df.{query}")
            
            if isinstance(result, pd.DataFrame):
                return result.to_string()
            elif isinstance(result, pd.Series):
                return result.to_string()
            else:
                return str(result)
                
        except Exception as e:
            return f"Error executing query: {str(e)}. Make sure the query is valid pandas syntax."
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """クエリを処理してレスポンスを生成"""
        try:
            print(f"Processing query: {query}")
            
            # Swarmを使用してクエリを処理
            response = await asyncio.to_thread(
                self.client.run,
                agent=self.agent,
                messages=[{"role": "user", "content": query}],
                context_variables=self.context_variables,
                max_turns=5,
                debug=True
            )
            
            print(f"Response: {response}")
            
            # レスポンスから結果を抽出
            if hasattr(response, 'messages') and response.messages:
                result = response.messages[-1]["content"]
            else:
                result = "No response generated"
            
            # 可視化が含まれているかチェック
            visualization = None
            if "data:image/png;base64," in result:
                # Base64画像を抽出
                start = result.find("data:image/png;base64,")
                end = result.find('"', start)
                if end == -1:
                    # スペースや改行で区切られている場合
                    end = min(
                        result.find(' ', start) if result.find(' ', start) != -1 else len(result),
                        result.find('\n', start) if result.find('\n', start) != -1 else len(result)
                    )
                visualization = result[start:end]
                # 結果から画像部分を削除
                result = result[:start] + "[グラフを作成しました]" + result[end:]
            
            return {
                "result": result,
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
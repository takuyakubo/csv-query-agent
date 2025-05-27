#!/usr/bin/env python3
"""CSVAgentのテストスクリプト"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from csv_agents.csv_agent import CSVAgent

async def test_csv_agent():
    csv_path = Path("../sample_data.csv")
    df = pd.read_csv(csv_path, encoding='utf-8')
    # CSVAgentのインスタンスを作成
    agent = CSVAgent(df, csv_path)
    
    # テスト用のCSVファイルパスを設定（実際のファイルパスに変更してください）
   
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        print("Please update the csv_path variable with your actual CSV file path")
        return
    
    # クエリを実行
    query = "月毎の売り上げを棒グラフで表示してください"
    print(f"Query: {query}")
    print("-" * 50)
    
    # process_queryメソッドを使用して実行
    result = await agent.process_query(query)
    
    # 結果を表示
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    # 結果の詳細を表示
    if hasattr(result, '__dict__'):
        print("\nResult attributes:")
        for key, value in result.__dict__.items():
            print(f"  {key}: {value}")
    
    # visualization_dataがある場合は詳細を表示
    if hasattr(result, 'visualization_data') and result.visualization_data:
        print("\nVisualization Data:")
        print(f"  Type: {result.visualization_data.type}")
        print(f"  Chart Type: {result.visualization_data.chart_type}")
        print(f"  Title: {result.visualization_data.title}")
        print(f"  Data: {json.dumps(result.visualization_data.data_for_graph.model_dump(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test_csv_agent())
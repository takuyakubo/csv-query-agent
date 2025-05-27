import asyncio
import io
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Tuple, Optional

import gradio as gr
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import redis

from app.config import settings
from csv_agents.csv_agent import CSVAgent

# OpenAI API keyを環境変数に設定（トレーシング警告の抑制）
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = settings.openai_api_key

matplotlib.use('Agg')

# 日本語フォントの設定
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# グローバル状態
current_session = None

def create_chart_from_params(viz_data: dict) -> Optional[str]:
    """可視化パラメータから画像を生成"""
    try:
        chart_type = viz_data["chart_type"]
        data = viz_data["data_for_graph"]
        title = viz_data["title"]
        
        plt.figure(figsize=(10, 6))
        
        # チャートタイプに応じた描画
        chart_functions = {
            "bar": lambda: _create_bar_chart(data),
            "line": lambda: _create_line_chart(data),
            "scatter": lambda: _create_scatter_chart(data),
            "pie": lambda: _create_pie_chart(data),
            "hist": lambda: _create_histogram(data),
        }
        
        # チャートを描画
        chart_function = chart_functions.get(chart_type, lambda: _create_bar_chart(data))
        chart_function()
        
        plt.title(title)
        plt.tight_layout()
        
        # システムのtempディレクトリに保存
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        plt.savefig(temp_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_path
        
    except Exception as e:
        print(f"Error creating chart: {e}")
        plt.close()
        return None


def _create_bar_chart(data: dict) -> None:
    """棒グラフを作成"""
    plt.bar(data["x"], data["y"])
    plt.xlabel(data["x_label"])
    plt.ylabel(data["y_label"])
    plt.xticks(rotation=45)


def _create_line_chart(data: dict) -> None:
    """折れ線グラフを作成"""
    plt.plot(data["x"], data["y"], marker='o')
    plt.xlabel(data["x_label"])
    plt.ylabel(data["y_label"])


def _create_scatter_chart(data: dict) -> None:
    """散布図を作成"""
    plt.scatter(data["x"], data["y"])
    plt.xlabel(data["x_label"])
    plt.ylabel(data["y_label"])


def _create_pie_chart(data: dict) -> None:
    """円グラフを作成"""
    plt.pie(data["y"], labels=data["x"], autopct='%1.1f%%')


def _create_histogram(data: dict) -> None:
    """ヒストグラムを作成"""
    plt.hist(data["x"], bins=30, edgecolor='black')
    plt.xlabel(data["x_label"])
    plt.ylabel(data["y_label"])

def upload_csv(file) -> Tuple[str, gr.update, gr.update]:
    """CSVファイルをアップロードして処理"""
    global current_session
    
    if file is None:
        return "ファイルが選択されていません", gr.update(visible=False), gr.update(visible=False)
    
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(file.name, encoding='utf-8')
        
        # セッションIDを生成
        session_id = str(uuid.uuid4())
        
        # データをRedisに保存（30分間）
        session_data = {
            "filename": file.name.split('/')[-1],
            "columns": df.columns.tolist(),
            "shape": df.shape,
            "created_at": datetime.now().isoformat(),
            "data": df.to_json(orient='records')
        }
        
        redis_client.setex(
            f"session:{session_id}",
            timedelta(minutes=30),
            json.dumps(session_data)
        )
        
        current_session = session_id
        
        info_text = f"""
✅ ファイルアップロード成功！

📁 **ファイル名**: {session_data['filename']}
📊 **データサイズ**: {df.shape[0]} 行 × {df.shape[1]} 列
📝 **列名**: {', '.join(df.columns.tolist())}

下記のテキストボックスに質問を入力してください。
        """
        
        return info_text, gr.update(visible=True), gr.update(visible=True)
        
    except Exception as e:
        return f"❌ エラー: {str(e)}", gr.update(visible=False), gr.update(visible=False)

def process_query(query: str) -> Tuple[str, Optional[str]]:
    """クエリを処理して結果を返す"""
    global current_session
    
    if not current_session:
        return "まずCSVファイルをアップロードしてください", None
    
    if not query.strip():
        return "質問を入力してください", None
    
    try:
        # セッションデータを取得
        session_data = redis_client.get(f"session:{current_session}")
        if not session_data:
            return "セッションが期限切れです。再度CSVファイルをアップロードしてください", None
        
        session_info = json.loads(session_data)
        
        # DataFrameを復元
        df = pd.read_json(io.StringIO(session_info["data"]))
        
        # エージェントを初期化
        agent = CSVAgent(df, session_info["filename"])
        
        # CSVAgentのprocess_queryメソッドを使用
        result = asyncio.run(agent.process_query(query))
        
        # ResponseCSVAgentオブジェクトから結果を取得
        response_text = result.result
        
        # 可視化データがある場合は画像を生成
        if result.visualization_data:
            viz_data = {
                "type": result.visualization_data.type,
                "chart_type": result.visualization_data.chart_type,
                "data_for_graph": result.visualization_data.data_for_graph.model_dump(),
                "title": result.visualization_data.title
            }
            
            chart_path = create_chart_from_params(viz_data)
            if chart_path:
                return response_text, chart_path
        
        return response_text, None
        
    except Exception as e:
        import traceback
        print(f"Error in process_query: {str(e)}")
        print(traceback.format_exc())
        return f"❌ エラー: {str(e)}", None

def reset_session() -> Tuple[str, gr.update, gr.update, None, None]:
    """セッションをリセット"""
    global current_session
    current_session = None
    return "新しいCSVファイルをアップロードしてください", gr.update(visible=False), gr.update(visible=False), None, None

# Gradioインターフェースを作成
with gr.Blocks(title="CSV Query Agent", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🤖 CSV Query Agent
    
    CSVファイルをアップロードして、自然言語で質問してみましょう！
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            # ファイルアップロード
            file_input = gr.File(
                label="📁 CSVファイルをアップロード",
                file_types=[".csv"],
                file_count="single"
            )
            
            upload_btn = gr.Button("📤 アップロード", variant="primary")
            
            # リセットボタン
            reset_btn = gr.Button("🔄 新しいファイル", variant="secondary")
        
        with gr.Column(scale=2):
            # アップロード結果表示
            upload_status = gr.Markdown("CSVファイルをアップロードしてください")
    
    # クエリセクション（初期は非表示）
    with gr.Row(visible=False) as query_section:
        with gr.Column():
            query_input = gr.Textbox(
                label="📝 質問を入力してください",
                placeholder="例: 売上の合計を教えて、月別の売上を棒グラフで表示して",
                lines=2
            )
            
            query_btn = gr.Button("🚀 質問する", variant="primary")
    
    # 結果表示セクション（初期は非表示）
    with gr.Row(visible=False) as result_section:
        with gr.Column(scale=1):
            result_text = gr.Markdown("結果がここに表示されます")
        
        with gr.Column(scale=1):
            result_image = gr.Image(label="📊 グラフ", visible=True)
    
    # イベントハンドラー
    upload_btn.click(
        fn=upload_csv,
        inputs=[file_input],
        outputs=[upload_status, query_section, result_section]
    )
    
    query_btn.click(
        fn=process_query,
        inputs=[query_input],
        outputs=[result_text, result_image]
    )
    
    # Enterキーでクエリ実行
    query_input.submit(
        fn=process_query,
        inputs=[query_input],
        outputs=[result_text, result_image]
    )
    
    reset_btn.click(
        fn=reset_session,
        inputs=[],
        outputs=[upload_status, query_section, result_section, result_text, result_image]
    )

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False
    )
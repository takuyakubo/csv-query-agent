from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io
import uuid
from typing import Optional
from datetime import datetime, timedelta
import redis
import json
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.models import QueryRequest, QueryResponse, SessionInfo
from agents.csv_agent import CSVAgent


# Redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up CSV Query Agent API...")
    yield
    # Shutdown
    print("Shutting down CSV Query Agent API...")


app = FastAPI(
    title="CSV Query Agent API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "CSV Query Agent API is running"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    # CSVファイルかチェック
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # ファイルを読み込む
        contents = await file.read()
        
        # ファイルサイズチェック
        if len(contents) > settings.max_file_size:
            raise HTTPException(status_code=413, detail="File size exceeds maximum allowed size (10MB)")
        
        # CSVを読み込む（エンコーディングを試行）
        try:
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        except UnicodeDecodeError:
            # UTF-8でダメならshift-jisを試す
            try:
                df = pd.read_csv(io.StringIO(contents.decode('shift-jis')))
            except:
                df = pd.read_csv(io.BytesIO(contents))
        
        # セッションIDを生成
        session_id = str(uuid.uuid4())
        
        # データをRedisに保存（30分間）
        session_data = {
            "filename": file.filename,
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
        
        return JSONResponse(content={
            "session_id": session_id,
            "filename": file.filename,
            "columns": df.columns.tolist(),
            "rows": df.shape[0],
            "columns_count": df.shape[1]
        })
        
    except Exception as e:
        import traceback
        print(f"Error in upload_csv: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Error processing CSV file: {str(e)}")


@app.post("/query")
async def query_csv(request: QueryRequest):
    # セッションデータを取得
    session_data = redis_client.get(f"session:{request.session_id}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session_info = json.loads(session_data)
    
    try:
        # DataFrameを復元
        df = pd.read_json(io.StringIO(session_info["data"]))
        
        # エージェントを初期化
        agent = CSVAgent(df, session_info["filename"])
        
        # クエリを実行
        result = await agent.process_query(request.query)
        
        return QueryResponse(
            success=True,
            result=result.get("result"),
            visualization=result.get("visualization"),
            data=result.get("data"),
            query=request.query
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            result=None,
            error=str(e),
            query=request.query
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    session_data = redis_client.get(f"session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session_info = json.loads(session_data)
    # データ本体は返さない
    session_info.pop("data", None)
    
    return SessionInfo(**session_info)


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    result = redis_client.delete(f"session:{session_id}")
    if result == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}
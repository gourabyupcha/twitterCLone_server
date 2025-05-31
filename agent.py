from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect, text
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import httpx
import json,os
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from .env file

class Config:
    DB_URL = os.getenv("DB_URL")
    POST_ENDPOINT = "https://twitterclone-server-2xz2.onrender.com/post_tweet"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = "llama-3.1-8b-instant"

class BaseAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.MODEL_NAME
        )

class SQLAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.engine = create_engine(Config.DB_URL)
        self.inspector = inspect(self.engine)
    
    def get_schema_info(self) -> str:
        try:
            schema_info = """
            Table: tweets
            Columns:
            - tweet_id (SERIAL) [PK]
            - username (TEXT)
            - text (TEXT)
            - embedding (VECTOR(768))
            - retweets (INT)
            - likes (INT)
            - timestamp (TIMESTAMP)
            """
            return schema_info
        except Exception as e:
            raise Exception(f"Failed to get schema info: {str(e)}")

    def validate_query(self, query: str) -> bool:
        try:
            # Check for common SQL injection patterns
            dangerous_patterns = [
                ';--', ';/*', ';*/', ';--', ';--', 
                'UNION ALL', 'UNION SELECT', 'DROP', 'DELETE', 'UPDATE'
            ]
            for pattern in dangerous_patterns:
                if pattern.lower() in query.lower():
                    return False
            return True
        except Exception:
            return False

    def execute_query(self, sql_query: str) -> List[Dict]:
        try:
            if not self.validate_query(sql_query):
                raise Exception("Query validation failed: Potentially unsafe query detected")
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            raise Exception(f"Failed to execute SQL query: {str(e)}")

class PostGeneratorAgent(BaseAgent):
    def generate_post(self, data: List[Dict], prompt: str) -> str:
        try:
            prompt_template = """
            Create a tweet (max 50 words) from this data:
            Prompt: {prompt}
            Data: {data}
            Rules: Be concise, engaging, use hashtags if relevant.
            """
            
            chain = LLMChain(
                llm=self.llm,
                prompt=PromptTemplate.from_template(prompt_template)
            )
            
            tweet = chain.run({"prompt": prompt, "data": json.dumps(data)})
            
            # Ensure word limit
            words = tweet.split()
            if len(words) > 50:
                tweet = ' '.join(words[:50]) + '...'
            
            return tweet
        except Exception as e:
            raise Exception(f"Failed to generate tweet: {str(e)}")

class PosterAgent:
    def __init__(self):
        self.endpoint = Config.POST_ENDPOINT
        self.headers = {
            "api-key": "286b3bca733bfdb0e30e3ca315b1ffb4",
            "Content-Type": "application/json"
        }
    
    async def post_content(self, content: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers=self.headers,
                    json={
                        "username": "john",
                        "text": content
                    }
                )
                return response.json()
        except Exception as e:
            raise Exception(f"Failed to post content: {str(e)}")

class SupervisorAgent:
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.post_generator = PostGeneratorAgent()
        self.poster = PosterAgent()
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.MODEL_NAME
        )

    def clean_sql_query(self, sql_query: str) -> str:
        try:
            sql_query = sql_query.replace('```sql', '').replace('```', '')
            sql_query = sql_query.split(';')[0] + ';'
            sql_query = ' '.join(sql_query.split())
            return sql_query.strip()
        except Exception as e:
            raise Exception(f"Failed to clean SQL query: {str(e)}")

    async def process_request(self, prompt: str) -> Dict[str, Any]:
        try:
            sql_prompt = f"""
            Schema: {self.sql_agent.get_schema_info()}
            Task: "{prompt}"
            Rules:
            1. Output ONLY the SQL query
            2. Use PostgreSQL syntax
            3. Use || for string concat
            4. Use single % for LIKE
            5. Use single quotes
            6. Wrap UNION in parentheses
            7. End with semicolon
            8. No comments or explanations
            
            Example: SELECT text FROM tweets WHERE likes > 100 ORDER BY timestamp DESC LIMIT 5;
            """
            
            sql_chain = LLMChain(
                llm=self.llm,
                prompt=PromptTemplate.from_template(sql_prompt)
            )
            sql_query = sql_chain.run({})
            
            # Clean the SQL query
            clean_sql = self.clean_sql_query(sql_query)
            
            # 2. Execute SQL and get data
            data = self.sql_agent.execute_query(clean_sql)
            
            # 3. Generate post content
            post_content = self.post_generator.generate_post(data, prompt)
            
            # 4. Post the content
            post_result = await self.poster.post_content(post_content)
            
            return {
                "sql_query": clean_sql,
                "data": data,
                "generated_post": post_content,
                "post_result": post_result
            }
        except Exception as e:
            raise Exception(f"Failed to process request: {str(e)}")

# @app.post("/process")
# async def process_request(request: QueryRequest):
#     try:
#         supervisor = SupervisorAgent()
#         result = await supervisor.process_request(request.prompt)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)
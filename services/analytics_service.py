import asyncio
import json
from db.sqlite.connection import get_db

class AnalyticsService:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def answer_question(self, question: str) -> str:
        profiles_data = []
        with get_db() as conn:
            cursor = conn.execute("SELECT profile FROM profiles")
            for row in cursor:
                profile_json = row[0]
                if isinstance(profile_json, str):
                    profiles_data.append(json.loads(profile_json))
                else:
                    profiles_data.append(profile_json)

        if not profiles_data:
            return "The database is empty. Please index some resumes first."
        
        context = json.dumps(profiles_data, indent=2, ensure_ascii=False)
        
        prompt = (
            f"You are an HR Analytics Assistant. Below is a list of candidate profiles in JSON format.\n"
            f"Answer the user's question based ONLY on this data.\n"
            f"If you cannot find the answer, say so.\n\n"
            f"Data:\n{context}\n\n"
            f"User Question: {question}\n"
            f"Answer in user language."
        )

        response = await self.llm_client.generate(prompt)
        return response

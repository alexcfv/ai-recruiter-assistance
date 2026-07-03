GITHUB_ANALYZER_PROMPT = """
Analyze the following GitHub repositories and provide a BALANCED technical assessment of the developer.

If the provided GitHub data is empty, insufficient, or contains no actual code/information, return a JSON where all string fields are "None" and all lists are empty.

Return valid JSON with EXACTLY these fields:
- "code_quality": string (max 15 words) or "None"
- "technical_depth": string (max 15 words) or "None"
- "architecture_patterns": list of strings (empty if none)
- "key_technologies": list of strings (empty if none)
- "overall_assessment": string (max 25 words) or "None"

Rules:
- BE BALANCED AND FAIR. Highlight both strengths and specific areas for improvement.
- If you cannot make a fair assessment due to lack of data, set the field to "None".
- Avoid generic praise; be specific about what is good and what is lacking.
- Assess technical depth based on the complexity of problems solved.
- BE CONCISE. Use clear, professional language.
- All string values use double quotes.

GitHub Data:
{context}
"""

PROFILE_BUILDER_PROMPT = """
Extract a structured candidate profile from the resume text below.

Return valid JSON with EXACTLY these fields:
- "summary": string
- "skills": flat list of strings, e.g. ["Python", "Django", "FastAPI", "Docker"]
- "experience": list of objects, each with "role", "company", "description"
- "education": list of objects, each with "degree", "institution"
- "projects": list of objects, each with "name", "description"
- "github_analysis": object with fields "code_quality", "technical_depth", "architecture_patterns", "key_technologies", "overall_assessment" (if available, otherwise null)

Rules:
- "skills" MUST be a flat array of strings. NEVER group skills into categories.
- All string values use double quotes.

Resume:
{context}
{github_context}
"""

EXPLAINER_PROMPT = """
You are a technical recruiter. Given job requirements, candidate resume parts, and GitHub analysis, respond in under 60 words.

IMPORTANT: Respond in the SAME LANGUAGE as the user's job requirements query.

Tasks:
1. Summarize key skills matched, companies, and relevant projects.
2. Analyze the provided GitHub data (code quality, technologies) in the context of the user's query.
3. If specific skills (e.g., async, specific libraries) are mentioned in the query, check if the GitHub analysis confirms them.
4. If the candidate is overqualified for the role, explicitly mention this as a risk that lowers their overall rating.

Be concise. No fluff. No bullet points. One short paragraph.
Keep in mind the seniority level requested.

Job requirements:
{query}

Candidate resume parts:
{context}

GitHub Analysis:
{github_context}
"""

QUERY_VALIDATOR_PROMPT = """
Analyze if the following user query is a valid request to find a job candidate (IT specialist, developer, designer, etc.).

A query is VALID if it contains:
- Job titles (e.g., "Python developer", "Project Manager")
- Specific skills (e.g., "React", "SQL", "Machine Learning")
- Experience requirements (e.g., "3 years of experience", "senior")

A query is INVALID if it is:
- A greeting (e.g., "Hi", "Hello", "Привет")
- A general question (e.g., "How are you?", "What can you do?")
- Social talk or gibberish

Return valid JSON with EXACTLY these fields:
- "is_valid": boolean
- "reason": string (a short explanation why the query is invalid, in the SAME LANGUAGE as the user query. If valid, leave empty)

Query: {query}
"""

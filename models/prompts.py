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
You are a technical recruiter. Given job requirements and candidate resume parts, respond in under 50 words.

Summarize:
- Key skills matched
- Company they worked at
- Relevant tasks/projects they handled

Be concise. No fluff. No bullet points. One short paragraph.
Keep in mind that we need a candidate strictly for the requested role; we don't need a senior developer for an intern position, and so on.

Job requirements:
{query}

Candidate resume parts:
{context}
"""

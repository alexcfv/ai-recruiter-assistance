import litellm

class MistralEmbedder:
    def __init__(self, api_key, model="mistral-embed", timeout=60, rate_limiter=None, api_base=None):
        self.model = f"mistral/{model}"
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.rate_limiter = rate_limiter

    async def embed(self, text: str) -> list[float]:
        if self.rate_limiter:
            self.rate_limiter.wait()
        response = await litellm.aembedding(
            model=self.model,
            input=text,
            api_key=self.api_key,
            api_base=self.api_base,
            timeout=self.timeout,
        )
        return response.data[0]["embedding"]

    async def embed_batch(self, texts: list[str], batch_size=32) -> list[list[float]]:
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            if self.rate_limiter:
                self.rate_limiter.wait()
            response = await litellm.aembedding(
                model=self.model,
                input=batch,
                api_key=self.api_key,
                api_base=self.api_base,
                timeout=self.timeout,
            )

            embeddings = [item["embedding"] for item in response.data]
            all_embeddings.extend(embeddings)

        return all_embeddings

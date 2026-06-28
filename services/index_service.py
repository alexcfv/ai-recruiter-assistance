class IndexService:
    def __init__(self, embedder, loader, vector_store, profile_builder, profile_repository, github_collector=None, github_analyzer=None, resume_parser=None):
        self.embedder = embedder
        self.loader = loader
        self.vector_store = vector_store
        self.profile_builder = profile_builder
        self.profile_repository = profile_repository
        self.github_collector = github_collector
        self.github_analyzer = github_analyzer
        self.resume_parser = resume_parser

    async def index_folder(self, dir_path: str) -> dict:
        documents = self.loader.load_folder(dir_path)

        existing = set()
        if self.vector_store.collection.count() > 0:
            existing = set(
                m["source"]
                for m in self.vector_store.collection.get(limit=10000)["metadatas"]
            )

        new_docs = [d for d in documents if d["source"] not in existing]

        if new_docs:
            self.vector_store.add_documents(new_docs, self.embedder)

        all_grouped = self.vector_store.get_all_grouped_by_source()
        new_profiles = []
        for source, chunks in all_grouped.items():
            # Проверяем существование профиля, но для отладки можем разрешить обновление
            if not self.profile_repository.profile_exists(source):
                github_analysis = None
                
                if self.resume_parser and self.github_collector and self.github_analyzer:
                    full_text = " ".join(chunks)
                    github_username = self.resume_parser.extract_github_link(full_text)
                    
                    if github_username:
                        print(f"DEBUG: Found GitHub username: {github_username} for {source}")
                        try:
                            github_data = await self.github_collector.collect_user_data(github_username)
                            print(f"DEBUG: Collected GitHub data for {github_username}")
                            
                            # Проверяем, что метод асинхронный
                            import inspect
                            if inspect.iscoroutinefunction(self.github_analyzer.analyze_code):
                                github_analysis = await self.github_analyzer.analyze_code(github_data)
                            else:
                                print(f"DEBUG: analyze_code is NOT a coroutine function! Type: {type(self.github_analyzer.analyze_code)}")
                                github_analysis = self.github_analyzer.analyze_code(github_data)
                                
                            print(f"DEBUG: GitHub analysis result obtained")
                        except Exception as e:
                            print(f"GitHub analysis failed for {source}: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"DEBUG: No GitHub username found in {source}")
                
                profile = await self.profile_builder.build_profile(chunks, github_analysis)
                print(f"DEBUG: Final profile github_analysis field: {profile.get('github_analysis')}")
                self.profile_repository.create_profile(source, profile)
                new_profiles.append(source)

        return {
            "total_files": len(set(d["source"] for d in documents)),
            "new_chunks": len(new_docs),
            "new_profiles": new_profiles,
        }

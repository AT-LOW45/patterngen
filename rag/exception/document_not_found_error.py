class DocumentNotFoundError(Exception):
    def __init__(self, source: str):
        self.source = source
        super().__init__(f"Document not found: {source}")
class SourceDerivationError(Exception):
    """No identity key could be derived — the document has no H1 and no usable filename."""

    def __init__(self) -> None:
        super().__init__("Could not derive a source from the document or its filename")


class DuplicateSourceError(Exception):
    """A record with this identity already exists; creating would overwrite it."""

    def __init__(self, source: str):
        self.source = source
        super().__init__(f"Document already exists: {source}")

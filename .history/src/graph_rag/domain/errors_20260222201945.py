from __future__ import annotations


class DomainError(Exception):
    """Base class for domain/application errors."""


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class DependencyError(DomainError):
    """External dependency failed (db, vector store, graph store, llm, etc)."""
    pass
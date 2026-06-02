import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


class TenantRepository:
    """Base class for all tenant-scoped repositories.

    Every concrete subclass MUST set the `model` class attribute to the
    SQLAlchemy model that carries a `firm_id` column.

    Calling `_scope(stmt)` on any SELECT statement automatically appends
    ``WHERE <model>.firm_id = self.firm_id``, making it structurally
    impossible to execute an unscoped query through this interface.
    """

    model = None  # Subclasses must override this.

    def __init__(self, db: AsyncSession, firm_id: uuid.UUID) -> None:
        if firm_id is None:
            raise ValueError(
                "firm_id is required for tenant-scoped queries. "
                "Never instantiate a TenantRepository without a firm_id."
            )
        self.db = db
        self.firm_id = firm_id

    def _scope(self, stmt: Select) -> Select:
        """Append the tenant filter to a SELECT statement."""
        if self.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define a `model` attribute."
            )
        return stmt.where(self.model.firm_id == self.firm_id)

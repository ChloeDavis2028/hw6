"""The structured types the vendor desk agent uses."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class VendorFacts(BaseModel):
    """What the reader model pulls from a document. It has no free-text notes."""

    vendor: Optional[str] = Field(description="Vendor name from the document, or null if unknown.")
    sku: Optional[str] = Field(description="Campus Customs SKU, or null if unknown.")
    unit_price: Optional[float] = Field(description="Quoted unit price in dollars, or null if unknown.")
    lead_time_days: Optional[int] = Field(
        description="Lead time as a number. 14 business days is 14. Null only if no lead time is stated."
    )
    min_order_units: Optional[int] = Field(description="Minimum order in units, or null if unknown.")


class DecisionDraft(BaseModel):
    """What the decider model returns after reading the checked facts."""

    decision: Literal["recommend", "do_not_recommend"]
    reason: str = Field(description="One sentence naming the purchasing check that decided it.")


class VendorReport(VendorFacts, DecisionDraft):
    """The final report the handbook requires in section 13."""

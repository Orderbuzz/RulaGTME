from typing import List, Optional
from pydantic import BaseModel, Field


class AccountProfile(BaseModel):
    company: str
    industry: Optional[str] = None
    us_employees: Optional[int] = None
    contact: Optional[str] = None
    title: Optional[str] = None
    health_plan: Optional[str] = None
    notes: Optional[str] = None


class ValuePropMatch(BaseModel):
    value_prop_id: str
    value_prop_name: str
    confidence: float
    reasoning: List[str] = Field(default_factory=list)


class ProspectOutput(BaseModel):
    is_icp: bool
    icp_confidence: float
    icp_reasons: List[str] = Field(default_factory=list)
    matched_value_props: List[ValuePropMatch]
    email_subject: str
    email_body: str
    discovery_questions: List[str]
    quality_score: float
    review_required: bool
    review_reasons: List[str] = Field(default_factory=list)

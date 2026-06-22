from typing import Optional
from pydantic import BaseModel, Field

# Common disability categories in Indian welfare schemes
DISABILITY_OPTIONS = [
    "None",
    "Blind",
    "Hearing Impaired",
    "Physically Handicapped",
    "Mentally Challenged",
    "Multiple Disabilities"
]

class CitizenProfile(BaseModel):
    student: Optional[bool] = Field(None, description="Whether the citizen is actively studying or a student")
    income: Optional[float] = Field(None, description="Family annual income in Indian Rupees (INR)")
    state: Optional[str] = Field(None, description="Home state or region of the citizen, e.g. 'Tamil Nadu'")
    category: Optional[str] = Field(None, description="Social category, e.g. SC, ST, OBC, DNT, EBC, or General")
    gender: Optional[str] = Field(None, description="Gender of the citizen, e.g. Male, Female, Other")
    education: Optional[str] = Field(None, description="Level of education, e.g. School, Graduate, Engineering")
    disability: Optional[str] = Field(None, description=f"Disability status: {', '.join(DISABILITY_OPTIONS)}")

class ProfileExtraction(BaseModel):
    student: Optional[bool] = Field(None, description="Whether the user stated they are a student")
    income: Optional[float] = Field(None, description="Extracted family annual income in INR")
    state: Optional[str] = Field(None, description="Extracted home state, e.g., 'Tamil Nadu'")
    category: Optional[str] = Field(None, description="Extracted social category (SC/ST/OBC/DNT/EBC/General)")
    gender: Optional[str] = Field(None, description="Extracted gender (Male/Female/Other)")
    education: Optional[str] = Field(None, description="Extracted level of education (School/Graduate/Postgraduate/Engineering)")
    disability: Optional[str] = Field(None, description=f"Disability status: {', '.join(DISABILITY_OPTIONS)}")

class DocumentExtraction(BaseModel):
    document_type: str = Field("other", description="Type of document: 'aadhaar', 'income_certificate', 'community_certificate', or 'other'")
    income: Optional[float] = Field(None, description="Extracted annual family income if present in the document")
    state: Optional[str] = Field(None, description="Extracted state if present in the document")
    gender: Optional[str] = Field(None, description="Extracted gender if present in the document")
    category: Optional[str] = Field(None, description="Extracted social category if present in the document")

class ComparisonItem(BaseModel):
    scheme_name: str = Field(..., description="Name of the scheme")
    financial_benefit: str = Field("", description="Financial benefit amount/value")
    eligibility_difficulty: str = Field("Medium", description="Easy/Medium/Hard based on criteria strictness")
    required_documents_count: int = Field(0, description="Number of required documents")
    processing_time: str = Field("Varies", description="Estimated processing time")
    approval_likelihood: str = Field("Medium", description="Low/Medium/High based on profile match strength")
    renewal_required: bool = Field(False, description="Whether the scheme requires annual renewal")
    goal_alignment: str = Field("", description="How well this matches the user's stated goals")
    notes: str = Field("", description="Additional comparison notes")

class DecisionReport(BaseModel):
    recommended_scheme: str = Field(..., description="The top recommended scheme name")
    recommendation_reasoning: str = Field(..., description="Detailed reasoning for the recommendation")
    key_strengths: str = Field("", description="Key strengths of the recommended scheme")
    potential_drawbacks: str = Field("", description="Potential drawbacks or considerations")
    important_tradeoffs: str = Field("", description="Important tradeoffs the user should consider")
    runner_up: str = Field("", description="Second-best alternative scheme")

class ActionPlanItem(BaseModel):
    step_number: int = Field(..., description="Step number in the action plan")
    action: str = Field(..., description="What the user needs to do")
    details: str = Field("", description="Additional details or instructions")
    resource_link: str = Field("", description="Link to relevant resource or portal")
    estimated_time: str = Field("", description="Estimated time to complete this step")
    priority: str = Field("Medium", description="High/Medium/Low priority")

class SearchQueryRewrite(BaseModel):
    """LLM rewrites user query into a search-optimized query for vector retrieval."""
    search_query: str = Field(..., description="Concise keyword-rich search query for finding government schemes. Focus on scheme type, benefits, and target group.")

class IncomeVerificationResult(BaseModel):
    """
    LLM verifies whether the user's income qualifies for each scheme
    by reading the raw eligibility text (not the parsed income_max).
    """
    qualifying_indices: list[int] = Field(
        ...,
        description="Zero-based indices of schemes where the user's income qualifies based on the scheme's eligibility text"
    )

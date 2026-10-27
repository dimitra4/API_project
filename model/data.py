from pydantic import BaseModel, Field, model_validator
from typing import Optional


class Data(BaseModel):
    """
    Base class for data models.
    """
    name: str = Field(
        description="The name from the request, echoed exactly as sent",
        pattern=r'^[a-zA-Z]+$',
        frozen=True,
    )
    age: Optional[int] = Field(
        description="The predicted age for the name, or null if no prediction could be made",
        ge=0,
        lt=120,
        default=None,
    )
    count: Optional[int] = Field(
        description="The number of people with this name in the dataset, or 0 if no prediction could be made",
        ge=0,
        default=0,
    )
    country_id: Optional[str] = Field(
        description="The 2-letter country code for the prediction, or null if no prediction could be made",
        max_length=2,
        default=None,
    )

    @model_validator(mode="after")
    def validate_age_count(self):
        has_prediction = self.age is not None and self.count is not None and self.count > 0
        no_prediction = self.age is None and self.count == 0

        if has_prediction or no_prediction:
            return self

        raise ValueError(
            "age must be None and count must be 0 if no prediction could be made"
        )
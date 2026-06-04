from pydantic import BaseModel, model_validator, ConfigDict

from src.exceptions import AtLeastOneFieldRequiredException, EmptyRequestBodyException


class ChangeBaseSchema(BaseModel):

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if not self.model_fields_set:
            raise EmptyRequestBodyException

        if all(value is None or value == "" for value in self.model_dump().values()):
            raise AtLeastOneFieldRequiredException
        return self

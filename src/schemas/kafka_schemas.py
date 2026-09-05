from pydantic import BaseModel


class BaseKafkaHeadersSchema(BaseModel):

    def to_kafka_format(self) -> list[tuple[str, bytes]]:
        return [
            (field_name, str(value).encode("utf-8"))
            for field_name, value in self.model_dump().items()
            if value is not None
        ]


class BaseKafkaMessageSchema(BaseModel):
    topic: str
    key: str | None = None
    payload: BaseModel
    headers: BaseKafkaHeadersSchema | None = None
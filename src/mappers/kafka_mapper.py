from pydantic import BaseModel

from src.schemas.kafka_schemas import BaseKafkaHeadersSchema


def payload_to_bytes(payload: BaseModel) -> bytes:
    return payload.model_dump_json().encode("utf-8")


def headers_to_kafka_format(headers: BaseKafkaHeadersSchema | None) -> list[tuple[str, bytes]] | None:
    if headers is None:
        return None
    return headers.to_kafka_format()
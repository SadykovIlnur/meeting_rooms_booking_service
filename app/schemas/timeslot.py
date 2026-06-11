from datetime import time

from pydantic import BaseModel


class SlotResponse(BaseModel):
    id: int
    start_time: time
    end_time: time

    model_config = {"from_attributes": True}

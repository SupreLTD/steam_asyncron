from pydantic import BaseModel, field_validator


class PriceDetail(BaseModel):
    initial: int
    final: int

    @field_validator('initial')
    def set_initial(cls, value):
        return f"{value / 100:.2f}"

    @field_validator('final')
    def set_final(cls, value):
        return f"{value / 100:.2f}"


class Price(BaseModel):
    appid: str
    price_overview: PriceDetail

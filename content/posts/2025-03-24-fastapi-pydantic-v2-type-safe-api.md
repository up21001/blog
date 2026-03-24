---
title: "FastAPI + Pydantic v2 완전 가이드 — 타입 안전한 API 서버 만들기"
date: 2025-03-24T08:00:00+09:00
lastmod: 2025-03-25T08:00:00+09:00
description: "FastAPI와 Pydantic v2를 조합해 타입 안전한 REST API 서버를 구축하는 방법을 모델 정의, 유효성 검사, 직렬화, 의존성 주입, 실전 예시까지 단계별로 정리합니다."
slug: "fastapi-pydantic-v2-type-safe-api"
categories: ["software-dev"]
tags: ["FastAPI", "Pydantic", "Python", "REST API", "타입 힌팅"]
series: []
draft: false
---

Python 웹 프레임워크 중에서 FastAPI는 2026년에도 빠르게 성장하고 있습니다. 타입 힌팅 기반 자동 문서화, 비동기 지원, Pydantic을 통한 강력한 유효성 검사가 결합되어 있기 때문입니다. 특히 Pydantic v2가 2023년 출시되고 2024년부터 프로덕션에서 널리 쓰이면서, FastAPI와의 조합이 더욱 강력해졌습니다. 이 글에서는 두 라이브러리의 핵심을 실전 코드 중심으로 정리합니다.

![FastAPI + Pydantic v2 아키텍처](/images/fastapi-pydantic-v2-architecture.svg)

## 왜 FastAPI + Pydantic v2인가

FastAPI의 핵심 가치는 "타입 힌팅으로 모든 것을 표현한다"는 철학입니다. 라우터 함수의 파라미터 타입을 선언하면, FastAPI가 자동으로 요청 파싱, 유효성 검사, OpenAPI 문서화를 처리합니다. Pydantic v2는 이 과정의 핵심 엔진입니다.

Pydantic v2의 주요 변화:

- **Rust 코어(pydantic-core)**: 유효성 검사 속도가 v1 대비 5~50배 빠름
- **`model_validator`, `field_validator`**: 데코레이터 기반 validator 재설계
- **`model_config`**: `Config` 내부 클래스 대신 `model_config` 딕셔너리 방식
- **직렬화 개선**: `model_dump()` / `model_dump_json()` (구 `dict()` / `json()` 대체)
- **Annotated 타입 지원 강화**: `Annotated[str, Field(...)]` 패턴

## 설치

```bash
pip install fastapi uvicorn pydantic
# 또는 uv 사용
uv add fastapi uvicorn pydantic
```

FastAPI는 설치 시 Pydantic v2를 자동으로 가져옵니다. Python 3.11 이상을 권장합니다.

## Pydantic v2 모델 기초

### 기본 모델 정의

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    email: EmailStr
    age: int = Field(..., ge=0, le=150)
    bio: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
```

`Field(...)` 는 필수 필드를 나타냅니다. `ge`, `le`, `min_length`, `max_length` 같은 파라미터로 유효성 조건을 선언합니다.

### 모델 설정 (model_config)

```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,   # ORM 객체에서 생성 허용 (구 orm_mode=True)
        str_strip_whitespace=True,  # 문자열 앞뒤 공백 자동 제거
        populate_by_name=True,  # alias와 field name 모두 허용
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    id: int
    name: str
    email: str
```

### 커스텀 validator

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Self

class ProductCreate(BaseModel):
    name: str
    price: float
    discount_price: Optional[float] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("상품명은 공백일 수 없습니다")
        return v.strip()

    @field_validator("price", "discount_price", mode="before")
    @classmethod
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
        return v

    @model_validator(mode="after")
    def discount_less_than_price(self) -> Self:
        if self.discount_price and self.discount_price >= self.price:
            raise ValueError("할인가는 정가보다 낮아야 합니다")
        return self
```

`@field_validator`는 개별 필드 검증, `@model_validator`는 전체 모델 레벨 검증에 사용합니다. `mode="after"`는 모든 필드가 파싱된 이후에 실행됩니다.

### Annotated 패턴

```python
from typing import Annotated
from pydantic import BaseModel, Field

PositiveInt = Annotated[int, Field(gt=0)]
EmailField = Annotated[str, Field(pattern=r'^[\w.-]+@[\w.-]+\.\w+$')]

class Order(BaseModel):
    quantity: PositiveInt
    user_email: EmailField
    unit_price: Annotated[float, Field(gt=0, le=1_000_000)]
```

타입 별칭을 `Annotated`로 정의해 재사용 가능한 검증 규칙을 만들 수 있습니다.

## FastAPI 라우터 구성

### 기본 CRUD 엔드포인트

```python
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Product API", version="1.0.0")

# 인메모리 저장소 (실제로는 DB 사용)
products_db: dict[int, dict] = {}
_id_counter = 0

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate) -> ProductResponse:
    global _id_counter
    _id_counter += 1
    data = {"id": _id_counter, **product.model_dump()}
    products_db[_id_counter] = data
    return ProductResponse(**data)

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int) -> ProductResponse:
    if product_id not in products_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"상품 ID {product_id}를 찾을 수 없습니다",
        )
    return ProductResponse(**products_db[product_id])

@app.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, update: ProductUpdate) -> ProductResponse:
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    # exclude_none=True: None 값 필드는 제외하고 업데이트
    update_data = update.model_dump(exclude_none=True)
    products_db[product_id].update(update_data)
    return ProductResponse(**products_db[product_id])

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    del products_db[product_id]
```

### 쿼리 파라미터와 페이지네이션

```python
from fastapi import Query

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

@app.get("/products", response_model=list[ProductResponse])
async def list_products(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    size: int = Query(default=20, ge=1, le=100, description="페이지 크기"),
    name_contains: Optional[str] = Query(None, description="상품명 검색"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
) -> list[ProductResponse]:
    items = list(products_db.values())

    if name_contains:
        items = [p for p in items if name_contains.lower() in p["name"].lower()]
    if min_price is not None:
        items = [p for p in items if p["price"] >= min_price]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]

    start = (page - 1) * size
    return [ProductResponse(**p) for p in items[start : start + size]]
```

## 의존성 주입 (Dependency Injection)

FastAPI의 `Depends`를 활용하면 공통 로직을 재사용할 수 있습니다.

```python
from fastapi import Depends, Header
from typing import Annotated

async def get_current_user(authorization: str = Header(...)) -> dict:
    """Authorization 헤더에서 사용자 정보 추출 (실제로는 JWT 검증)"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="유효하지 않은 인증 헤더")
    token = authorization.replace("Bearer ", "")
    # 실제 구현에서는 JWT 디코딩
    if token == "test-token":
        return {"id": 1, "name": "테스트 유저", "role": "admin"}
    raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

CurrentUser = Annotated[dict, Depends(get_current_user)]

@app.post("/products/admin", response_model=ProductResponse)
async def create_product_admin(
    product: ProductCreate,
    current_user: CurrentUser,
) -> ProductResponse:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    # ... 생성 로직
```

## 직렬화와 응답 형식

```python
from pydantic import BaseModel, model_serializer
from datetime import datetime

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    created_at: datetime
    items: list[dict]

    # 특정 필드를 응답에서 제외
    model_config = ConfigDict(populate_by_name=True)

# 직렬화 시 특정 필드 제외
order = OrderResponse(id=1, total_amount=50000.0, created_at=datetime.now(), items=[])
print(order.model_dump(exclude={"items"}))
# {'id': 1, 'total_amount': 50000.0, 'created_at': datetime(...)}

# JSON 직렬화
print(order.model_dump_json(indent=2))

# 응답 모델과 실제 반환 타입 분리 (민감 정보 제외)
class UserInDB(BaseModel):
    id: int
    email: str
    hashed_password: str  # DB에는 있지만 응답에서는 제외

class UserPublic(BaseModel):
    id: int
    email: str

@app.get("/users/me", response_model=UserPublic)
async def get_me(current_user: CurrentUser):
    # UserInDB를 반환해도 response_model=UserPublic이 필드 필터링
    return UserInDB(id=1, email="user@example.com", hashed_password="hashed...")
```

## 에러 처리 표준화

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

class ErrorResponse(BaseModel):
    error: str
    detail: str | list
    code: int

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            detail=exc.detail,
            code=exc.status_code,
        ).model_dump(),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=exc.errors(),
            code=422,
        ).model_dump(),
    )
```

## SQLAlchemy ORM과 연동

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, ConfigDict

class Base(DeclarativeBase):
    pass

class ProductORM(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]

class ProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # ORM 객체에서 직접 생성 가능

    id: int
    name: str
    price: float

# ORM 객체 → Pydantic 모델 변환
@app.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(ProductORM, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="찾을 수 없음")
    return ProductSchema.model_validate(product)  # from_attributes=True 덕분에 동작
```

## 서버 실행

```bash
# 개발 환경
uvicorn main:app --reload --port 8000

# 프로덕션
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

실행 후 `http://localhost:8000/docs` 에서 Swagger UI 자동 문서를 확인할 수 있습니다. `http://localhost:8000/redoc` 에서는 ReDoc 형식 문서도 제공됩니다.

## 성능 팁

**Pydantic v2 직렬화 최적화:**

```python
# model_dump()보다 model_dump_json()이 훨씬 빠름 (Rust 레벨 직렬화)
response_json = product.model_dump_json()

# 대량 처리 시 TypeAdapter 활용
from pydantic import TypeAdapter

adapter = TypeAdapter(list[ProductResponse])
# 리스트 전체를 한 번에 검증/직렬화
validated = adapter.validate_python(raw_list)
json_str = adapter.dump_json(validated)
```

## 정리

FastAPI + Pydantic v2 조합은 Python 웹 개발에서 타입 안전성과 성능을 동시에 가져갈 수 있는 현재 최선의 선택입니다. Pydantic v2의 Rust 코어 덕분에 유효성 검사 오버헤드가 거의 없고, FastAPI의 비동기 처리와 자동 문서화는 개발 생산성을 크게 높입니다.

처음 시작한다면 공식 FastAPI 튜토리얼과 Pydantic v2 마이그레이션 가이드를 함께 읽기를 권장합니다. v1에서 v2로의 변경 사항은 `model_dump()`, `model_validate()`, `model_config` 세 가지만 이해하면 대부분 커버됩니다.

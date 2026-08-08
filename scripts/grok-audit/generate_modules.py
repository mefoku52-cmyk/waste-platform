"""Generator vsetkych 6 chybajucich modulov podla vzoru listings."""
import os

MODULES = {
    "inquiries": {"class_name": "Inquiry", "table": "inquiries", "statuses": ["open", "answered", "closed"], "default_status": "open",
        "fields": [("listing_id", "UUID", "listing_id", "UUID(as_uuid=True)", False, "listingId"),
                   ("company_id", "UUID", "company_id", "UUID(as_uuid=True)", False, "companyId"),
                   ("message", "str", "message", "Text", False, "message"),
                   ("contact_email", "str", "contact_email", "String(255)", False, "contactEmail"),
                   ("contact_phone", "str | None", "contact_phone", "String(64)", True, "contactPhone")]},
    "documents": {"class_name": "Document", "table": "documents", "statuses": ["pending", "approved", "rejected"], "default_status": "pending",
        "fields": [("title", "str", "title", "String(255)", False, "title"),
                   ("document_type", "str", "document_type", "String(120)", False, "documentType"),
                   ("file_url", "str", "file_url", "String(1024)", False, "fileUrl"),
                   ("company_id", "UUID", "company_id", "UUID(as_uuid=True)", False, "companyId"),
                   ("listing_id", "UUID | None", "listing_id", "UUID(as_uuid=True)", True, "listingId")]},
    "compliance": {"class_name": "ComplianceRecord", "table": "compliance_records", "statuses": ["pending", "compliant", "non_compliant"], "default_status": "pending",
        "fields": [("company_id", "UUID", "company_id", "UUID(as_uuid=True)", False, "companyId"),
                   ("regulation_type", "str", "regulation_type", "String(120)", False, "regulationType"),
                   ("document_ref", "str | None", "document_ref", "String(255)", True, "documentRef"),
                   ("valid_until", "datetime | None", "valid_until", "DateTime", True, "validUntil"),
                   ("notes", "str | None", "notes", "Text", True, "notes")]},
    "notifications": {"class_name": "Notification", "table": "notifications", "statuses": None, "default_status": None,
        "fields": [("user_id", "UUID", "user_id", "UUID(as_uuid=True)", False, "userId"),
                   ("type", "str", "type", "String(64)", False, "type"),
                   ("title", "str", "title", "String(255)", False, "title"),
                   ("message", "str", "message", "Text", False, "message"),
                   ("is_read", "bool", "is_read", "Boolean", False, "isRead"),
                   ("related_entity_id", "UUID | None", "related_entity_id", "UUID(as_uuid=True)", True, "relatedEntityId")],
        "field_defaults": {"is_read": "False"}},
    "analytics": {"class_name": "AnalyticsEvent", "table": "analytics_events", "statuses": None, "default_status": None,
        "fields": [("event_type", "str", "event_type", "String(120)", False, "eventType"),
                   ("entity_type", "str", "entity_type", "String(120)", False, "entityType"),
                   ("entity_id", "UUID | None", "entity_id", "UUID(as_uuid=True)", True, "entityId"),
                   ("company_id", "UUID | None", "company_id", "UUID(as_uuid=True)", True, "companyId"),
                   ("event_metadata", "str | None", "event_metadata", "Text", True, "eventMetadata"),
                   ("recorded_at", "datetime", "recorded_at", "DateTime", False, "recordedAt")],
        "field_defaults": {"recorded_at": "field(default_factory=datetime.utcnow)"}},
    "admin": {"class_name": "AdminAuditEntry", "table": "admin_audit_entries", "statuses": ["pending", "success", "failed"], "default_status": "success",
        "fields": [("actor_user_id", "UUID", "actor_user_id", "UUID(as_uuid=True)", False, "actorUserId"),
                   ("action", "str", "action", "String(120)", False, "action"),
                   ("target_type", "str", "target_type", "String(120)", False, "targetType"),
                   ("target_id", "UUID | None", "target_id", "UUID(as_uuid=True)", True, "targetId"),
                   ("details", "str | None", "details", "Text", True, "details")]},
}

BASE = "app/modules"

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def gen_module(name, spec):
    cls = spec["class_name"]; table = spec["table"]; fields = spec["fields"]
    has_status = spec["statuses"] is not None
    field_defaults = spec.get("field_defaults", {})
    for sub in ["domain", "application", "infrastructure", "presentation"]:
        w(f"{BASE}/{name}/{sub}/__init__.py", "")
    w(f"{BASE}/{name}/__init__.py", "")
    if has_status:
        enum_lines = "\n".join(f'    {s.upper()} = "{s}"' for s in spec["statuses"])
        w(f"{BASE}/{name}/domain/enums.py", f'"""{name} domain enums."""\n\nfrom enum import Enum\n\n\nclass {cls}Status(str, Enum):\n{enum_lines}\n')
    entity_fields = []
    for py_name, py_type, *_rest, camel in fields:
        default = field_defaults.get(py_name)
        if default: entity_fields.append(f"    {py_name}: {py_type} = {default}")
        elif "None" in py_type: entity_fields.append(f"    {py_name}: {py_type} = None")
        else: entity_fields.append(f"    {py_name}: {py_type}")
    required = [l for l in entity_fields if "=" not in l]
    defaulted = [l for l in entity_fields if "=" in l]
    if has_status: defaulted.insert(0, f"    status: {cls}Status = {cls}Status.{spec['default_status'].upper()}")
    entity_body = "\n".join(required + defaulted)
    validate_checks = []
    for py_name, py_type, *_rest, camel in fields:
        if "None" not in py_type and py_type == "str":
            validate_checks.append(f'        if not self.{py_name}:\n            raise ValidationDomainError("{cls} {py_name} is required")')
    validate_body = "\n".join(validate_checks) if validate_checks else "        pass"
    imports_extra = f"from app.modules.{name}.domain.enums import {cls}Status\n" if has_status else ""
    needs_uuid = any("UUID" in py_type for py_name, py_type, *_r in fields)
    uuid_import = "from uuid import UUID\n" if needs_uuid else ""
    dataclass_import = "from dataclasses import dataclass, field" if field_defaults else "from dataclasses import dataclass"
    w(f"{BASE}/{name}/domain/entities.py", f'"""{name} domain entities."""\n\n{dataclass_import}\nfrom datetime import datetime\n{uuid_import}\n{imports_extra}from app.shared.domain.base import AuditFields\nfrom app.shared.domain.exceptions import ValidationDomainError\n\n\n@dataclass(slots=True)\nclass {cls}Entity(AuditFields):\n    """{cls} entity."""\n\n{entity_body}\n\n    def validate(self) -> None:\n{validate_body}\n')
    w(f"{BASE}/{name}/domain/repositories.py", f'"""{name} domain repositories."""\n\nfrom abc import ABC, abstractmethod\nfrom typing import List, Optional\n\nfrom .entities import {cls}Entity\n\n\nclass {cls}Repository(ABC):\n    """{cls} repository interface."""\n\n    @abstractmethod\n    async def get_by_id(self, id: str) -> Optional[{cls}Entity]:\n        pass\n\n    @abstractmethod\n    async def list_all(self, page: int = 1, limit: int = 20) -> List[{cls}Entity]:\n        pass\n\n    @abstractmethod\n    async def count_all(self) -> int:\n        pass\n\n    @abstractmethod\n    async def create(self, entity: {cls}Entity) -> {cls}Entity:\n        pass\n\n    @abstractmethod\n    async def update(self, entity: {cls}Entity) -> {cls}Entity:\n        pass\n\n    @abstractmethod\n    async def delete(self, id: str) -> None:\n        pass\n')
    col_lines = []
    for py_name, py_type, sql_col, sql_type, nullable, camel in fields:
        default = ", default=False" if py_name == "is_read" else ""
        col_lines.append(f'    {sql_col} = Column({sql_type}, nullable={nullable}{default})')
    status_col = f'    status = Column(String(32), nullable=False, default="{spec["default_status"]}")\n' if has_status else ""
    w(f"{BASE}/{name}/infrastructure/models.py", f'"""{name} database models."""\n\nimport uuid\nfrom datetime import datetime\n\nfrom sqlalchemy import Boolean, Column, DateTime, String, Text\nfrom sqlalchemy.dialects.postgresql import UUID\n\nfrom app.shared.infrastructure.db.base import Base\n\n\nclass {cls}Model(Base):\n    __tablename__ = "{table}"\n\n    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)\n{chr(10).join(col_lines)}\n{status_col}    created_at = Column(DateTime, default=datetime.utcnow)\n    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)\n    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)\n')
    to_domain_fields = [f"        {py_name}=model.{py_name}," for py_name, *_r in fields]
    to_model_fields = [f"        {py_name}=entity.{py_name}," for py_name, *_r in fields]
    status_to_domain = f"        status={cls}Status(model.status),\n" if has_status else ""
    status_to_model = f"        status=entity.status.value,\n" if has_status else ""
    status_import = f"from app.modules.{name}.domain.enums import {cls}Status\n" if has_status else ""
    w(f"{BASE}/{name}/infrastructure/mappers.py", f'"""{name} infrastructure mappers."""\n\nfrom app.modules.{name}.domain.entities import {cls}Entity\n{status_import}from app.modules.{name}.infrastructure.models import {cls}Model\n\n\ndef to_domain(model: {cls}Model) -> {cls}Entity:\n    return {cls}Entity(\n        id=model.id,\n{chr(10).join(to_domain_fields)}\n{status_to_domain}        created_at=model.created_at,\n        updated_at=model.updated_at,\n        created_by_user_id=model.created_by_user_id,\n        updated_by_user_id=model.updated_by_user_id,\n    )\n\n\ndef to_model(entity: {cls}Entity) -> {cls}Model:\n    return {cls}Model(\n        id=entity.id,\n{chr(10).join(to_model_fields)}\n{status_to_model}        created_at=entity.created_at,\n        updated_at=entity.updated_at,\n        created_by_user_id=entity.created_by_user_id,\n        updated_by_user_id=entity.updated_by_user_id,\n    )\n')
    update_field_lines = "\n".join(f"        model.{py_name} = entity.{py_name}" for py_name, *_r in fields)
    update_status_line = "        model.status = entity.status.value\n" if has_status else ""
    w(f"{BASE}/{name}/infrastructure/repositories.py", f'"""{name} repository implementations."""\n\nfrom typing import List, Optional\n\nfrom sqlalchemy import delete as sql_delete\nfrom sqlalchemy import func, select\nfrom sqlalchemy.ext.asyncio import AsyncSession\n\nfrom ..domain.entities import {cls}Entity\nfrom ..domain.repositories import {cls}Repository\nfrom .mappers import to_domain, to_model\nfrom .models import {cls}Model\n\n\nclass {cls}RepositoryImpl({cls}Repository):\n    """{cls} repository implementation."""\n\n    def __init__(self, session: AsyncSession):\n        self.session = session\n\n    async def get_by_id(self, id: str) -> Optional[{cls}Entity]:\n        result = await self.session.execute(select({cls}Model).where({cls}Model.id == id))\n        model = result.scalar_one_or_none()\n        return to_domain(model) if model else None\n\n    async def list_all(self, page: int = 1, limit: int = 20) -> List[{cls}Entity]:\n        offset = (page - 1) * limit\n        result = await self.session.execute(select({cls}Model).order_by({cls}Model.created_at.desc()).offset(offset).limit(limit))\n        models = result.scalars().all()\n        return [to_domain(m) for m in models]\n\n    async def count_all(self) -> int:\n        result = await self.session.execute(select(func.count()).select_from({cls}Model))\n        return int(result.scalar_one())\n\n    async def create(self, entity: {cls}Entity) -> {cls}Entity:\n        model = to_model(entity)\n        self.session.add(model)\n        await self.session.flush()\n        await self.session.refresh(model)\n        return to_domain(model)\n\n    async def update(self, entity: {cls}Entity) -> {cls}Entity:\n        model = await self.session.get({cls}Model, entity.id)\n        if model is None:\n            raise ValueError("Entity not found")\n{update_field_lines}\n{update_status_line}        model.updated_at = entity.updated_at\n        model.updated_by_user_id = entity.updated_by_user_id\n        await self.session.flush()\n        await self.session.refresh(model)\n        return to_domain(model)\n\n    async def delete(self, id: str) -> None:\n        await self.session.execute(sql_delete({cls}Model).where({cls}Model.id == id))\n        await self.session.flush()\n')
    w(f"{BASE}/{name}/application/services.py", f'"""{name} application services."""\n\nfrom typing import List, Optional\n\nfrom app.shared.domain.exceptions import NotFoundDomainError\n\nfrom ..domain.entities import {cls}Entity\nfrom ..domain.repositories import {cls}Repository\n\n\nclass {cls}Service:\n    """{cls} service."""\n\n    def __init__(self, repository: {cls}Repository):\n        self.repository = repository\n\n    async def get_by_id(self, id: str) -> Optional[{cls}Entity]:\n        return await self.repository.get_by_id(id)\n\n    async def list_all(self, page: int = 1, limit: int = 20) -> List[{cls}Entity]:\n        return await self.repository.list_all(page, limit)\n\n    async def count_all(self) -> int:\n        return await self.repository.count_all()\n\n    async def create(self, entity: {cls}Entity) -> {cls}Entity:\n        entity.validate()\n        return await self.repository.create(entity)\n\n    async def update(self, id: str, entity: {cls}Entity) -> {cls}Entity:\n        existing = await self.repository.get_by_id(id)\n        if existing is None:\n            raise NotFoundDomainError(f"{cls} {{id}} not found")\n        entity.id = existing.id\n        entity.created_at = existing.created_at\n        entity.created_by_user_id = existing.created_by_user_id\n        entity.validate()\n        return await self.repository.update(entity)\n\n    async def delete(self, id: str) -> None:\n        existing = await self.repository.get_by_id(id)\n        if existing is None:\n            raise NotFoundDomainError(f"{cls} {{id}} not found")\n        await self.repository.delete(id)\n')
    w(f"{BASE}/{name}/presentation/dependencies.py", f'"""{name} dependencies."""\n\nfrom fastapi import Depends\nfrom sqlalchemy.ext.asyncio import AsyncSession\n\nfrom app.shared.infrastructure.db.session import get_db_session\n\nfrom ..application.services import {cls}Service\nfrom ..infrastructure.repositories import {cls}RepositoryImpl\n\n\ndef get_{name}_repo(session: AsyncSession = Depends(get_db_session)) -> {cls}RepositoryImpl:\n    return {cls}RepositoryImpl(session)\n\n\ndef get_{name}_service(repo: {cls}RepositoryImpl = Depends(get_{name}_repo)) -> {cls}Service:\n    return {cls}Service(repository=repo)\n')
    create_lines, update_lines, data_lines = [], [], []
    for py_name, py_type, *_rest, camel in fields:
        if "None" in py_type: create_lines.append(f"    {camel}: {py_type} = None")
        else: create_lines.append(f"    {camel}: {py_type}")
        update_pytype = py_type if "None" in py_type else f"{py_type} | None"
        update_lines.append(f"    {camel}: {update_pytype} = None")
        data_lines.append(f"    {camel}: {py_type}")
    status_data_line = "    status: str\n" if has_status else ""
    status_update_line = "    status: str | None = None\n" if has_status else ""
    w(f"{BASE}/{name}/presentation/schemas.py", f'"""{name} API schemas."""\n\nfrom datetime import datetime\nfrom uuid import UUID\n\nfrom pydantic import BaseModel\n\n\nclass {cls}CreateRequest(BaseModel):\n{chr(10).join(create_lines)}\n\n\nclass {cls}UpdateRequest(BaseModel):\n{chr(10).join(update_lines)}\n{status_update_line}\n\nclass {cls}Data(BaseModel):\n    id: UUID\n{chr(10).join(data_lines)}\n{status_data_line}    createdAt: datetime\n    updatedAt: datetime\n\n\nclass {cls}Response(BaseModel):\n    data: {cls}Data\n\n\nclass PaginationMeta(BaseModel):\n    page: int\n    pageSize: int\n    total: int\n\n\nclass Paginated{cls}sResponse(BaseModel):\n    items: list[{cls}Data]\n    meta: PaginationMeta\n')
    to_data_lines = "\n".join(f"        {camel}=entity.{py_name}," for py_name, py_type, sql_col, sql_type, nullable, camel in fields)
    status_to_data = "        status=entity.status.value,\n" if has_status else ""
    create_entity_lines = "\n".join(f"        {py_name}=request.{camel}," for py_name, py_type, sql_col, sql_type, nullable, camel in fields)
    update_entity_lines = "\n".join(f"        {py_name}=request.{camel} if request.{camel} is not None else existing.{py_name}," for py_name, py_type, sql_col, sql_type, nullable, camel in fields)
    status_update_entity = f"        status={cls}Status(request.status) if request.status is not None else existing.status,\n" if has_status else ""
    status_import_router = f"from ..domain.enums import {cls}Status\n" if has_status else ""
    w(f"{BASE}/{name}/presentation/router.py", f'"""{name} API router."""\n\nfrom fastapi import APIRouter, Depends, HTTPException, status as http_status\n\nfrom app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError\n\nfrom ..application.services import {cls}Service\nfrom ..domain.entities import {cls}Entity\n{status_import_router}from .dependencies import get_{name}_service\nfrom .schemas import (\n    {cls}CreateRequest,\n    {cls}Data,\n    {cls}Response,\n    {cls}UpdateRequest,\n    Paginated{cls}sResponse,\n    PaginationMeta,\n)\n\nrouter = APIRouter(prefix="/{name}", tags=["{name}"])\n\n\ndef _to_data(entity: {cls}Entity) -> {cls}Data:\n    return {cls}Data(\n        id=entity.id,\n{to_data_lines}\n{status_to_data}        createdAt=entity.created_at,\n        updatedAt=entity.updated_at,\n    )\n\n\n@router.get("/", response_model=Paginated{cls}sResponse)\nasync def list_{name}(page: int = 1, limit: int = 20, service: {cls}Service = Depends(get_{name}_service)):\n    items = await service.list_all(page, limit)\n    total = await service.count_all()\n    return Paginated{cls}sResponse(items=[_to_data(e) for e in items], meta=PaginationMeta(page=page, pageSize=limit, total=total))\n\n\n@router.get("/{{id}}", response_model={cls}Response)\nasync def get_{name.rstrip("s")}(id: str, service: {cls}Service = Depends(get_{name}_service)):\n    entity = await service.get_by_id(id)\n    if entity is None:\n        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="{cls} not found")\n    return {cls}Response(data=_to_data(entity))\n\n\n@router.post("/", response_model={cls}Response, status_code=http_status.HTTP_201_CREATED)\nasync def create_{name.rstrip("s")}(request: {cls}CreateRequest, service: {cls}Service = Depends(get_{name}_service)):\n    entity = {cls}Entity(\n{create_entity_lines}\n    )\n    try:\n        created = await service.create(entity)\n    except ValidationDomainError as exc:\n        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc\n    return {cls}Response(data=_to_data(created))\n\n\n@router.put("/{{id}}", response_model={cls}Response)\nasync def update_{name.rstrip("s")}(id: str, request: {cls}UpdateRequest, service: {cls}Service = Depends(get_{name}_service)):\n    existing = await service.get_by_id(id)\n    if existing is None:\n        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="{cls} not found")\n    updated_entity = {cls}Entity(\n{update_entity_lines}\n{status_update_entity}    )\n    try:\n        result = await service.update(id, updated_entity)\n    except NotFoundDomainError as exc:\n        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc\n    except ValidationDomainError as exc:\n        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc\n    return {cls}Response(data=_to_data(result))\n\n\n@router.delete("/{{id}}", status_code=http_status.HTTP_204_NO_CONTENT)\nasync def delete_{name.rstrip("s")}(id: str, service: {cls}Service = Depends(get_{name}_service)):\n    try:\n        await service.delete(id)\n    except NotFoundDomainError as exc:\n        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=exc.message) from exc\n')

if __name__ == "__main__":
    for mod_name, mod_spec in MODULES.items():
        gen_module(mod_name, mod_spec)
        print(f"Vygenerovany modul: {mod_name}")

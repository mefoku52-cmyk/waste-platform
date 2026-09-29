"""Explicitny import vsetkych SQLAlchemy modelov, aby Base.metadata vzdy poznala
vsetky tabulky nezavisle od poradia/existencie importov cez routery.
Import tohto suboru pred Base.metadata.create_all() je jedina zaruka."""

from app.modules.admin.infrastructure.models import AdminAuditEntryModel  # noqa: F401
from app.modules.agent_platform.infrastructure.models import (  # noqa: F401
    AgentAuditRecordModel,
    AiConversationModel,
    AiMessageModel,
    AlertRecordModel,
    ApprovalRequestModel,
    ControlStateModel,
    SecurityEventModel,
)
from app.modules.analytics.infrastructure.models import (
    AnalyticsEventModel,  # noqa: F401
)
from app.modules.auth.infrastructure.models import RefreshSessionModel  # noqa: F401
from app.modules.chat.infrastructure.models import ChatMessageModel, ChatThreadModel  # noqa: F401
from app.modules.companies.infrastructure.models import CompanyModel  # noqa: F401
from app.modules.company_memberships.infrastructure.models import (
    CompanyMembershipModel,  # noqa: F401
)
from app.modules.compliance.infrastructure.models import (
    ComplianceRecordModel,  # noqa: F401
)
from app.modules.documents.infrastructure.models import DocumentModel  # noqa: F401
from app.modules.events.infrastructure.models import ActivityEventModel  # noqa: F401
from app.modules.inquiries.infrastructure.models import InquiryModel  # noqa: F401
from app.modules.lead_finder.infrastructure.persistence.models import (
    OutreachCandidateModel,  # noqa: F401
)
from app.modules.listings.infrastructure.models import ListingsModel, ListingViewModel  # noqa: F401
from app.modules.notifications.infrastructure.models import (
    NotificationModel,  # noqa: F401
)
from app.modules.users.infrastructure.models import UserModel  # noqa: F401

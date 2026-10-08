"""P4.9 compatibility re-exports for the shared failure classifier."""

from tizen_ci_shared.classify import CONFIDENCE_THRESHOLD as CONFIDENCE_THRESHOLD
from tizen_ci_shared.classify import DENYLIST_RULES as DENYLIST_RULES
from tizen_ci_shared.classify import EXPLICIT_NON_REPAIR_CLASSES as EXPLICIT_NON_REPAIR_CLASSES
from tizen_ci_shared.classify import NON_BUILD_STAGE_CLASSES as NON_BUILD_STAGE_CLASSES
from tizen_ci_shared.classify import RAW_KINDS as RAW_KINDS
from tizen_ci_shared.classify import REPAIR_AUTO as REPAIR_AUTO
from tizen_ci_shared.classify import REPAIR_DENIED as REPAIR_DENIED
from tizen_ci_shared.classify import REPAIR_NEEDS_CONFIRMATION as REPAIR_NEEDS_CONFIRMATION
from tizen_ci_shared.classify import SOURCE_KINDS as SOURCE_KINDS
from tizen_ci_shared.classify import SUSPECT_PATH_PARTS as SUSPECT_PATH_PARTS
from tizen_ci_shared.classify import SYSTEM_PREFIXES as SYSTEM_PREFIXES
from tizen_ci_shared.classify import FailureClassification as FailureClassification
from tizen_ci_shared.classify import classify_failure as classify_failure

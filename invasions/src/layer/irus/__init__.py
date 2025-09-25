# Legacy facades (backward compatibility)
# Environment and utilities
from .environ import IrusResources as IrusResources
from .environ import IrusSecrets as IrusSecrets

# Legacy facades (now implemented as modern service wrappers)
from .imageprep import ImagePreprocessor as ImagePreprocessor
from .invasion import IrusInvasion as IrusInvasion

# Refactored modules (using repository pattern)
from .invasionlist import IrusInvasionList as IrusInvasionList

# Legacy facades (backward compatibility - these are large facade files)
from .ladder import IrusLadder as IrusLadder
from .ladderrank import IrusLadderRank as IrusLadderRank
from .member import IrusMember as IrusMember
from .memberlist import IrusMemberList as IrusMemberList
from .month import IrusMonth as IrusMonth
from .posttable import IrusPostTable as IrusPostTable
from .process import IrusFiles as IrusFiles
from .process import IrusProcess as IrusProcess
from .report import IrusReport as IrusReport

# Modern service layer
from .services import DiscordMessagingService as DiscordMessagingService
from .services import ImageProcessingService as ImageProcessingService
from .services import MemberManagementService as MemberManagementService

# Legacy utilities (maintained for backward compatibility)
from .utilities import (
    update_invasions_for_new_member as update_invasions_for_new_member,
)

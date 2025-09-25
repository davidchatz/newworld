# Legacy facades (backward compatibility)
# Environment and utilities
from .environ import IrusResources as IrusResources
from .environ import IrusSecrets as IrusSecrets
from .invasion import IrusInvasion as IrusInvasion

# Refactored modules (using repository pattern)
from .invasionlist import IrusInvasionList as IrusInvasionList
from .ladderrank import IrusLadderRank as IrusLadderRank
from .member import IrusMember as IrusMember
from .memberlist import IrusMemberList as IrusMemberList
from .month import IrusMonth as IrusMonth
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

# TODO: Legacy modules scheduled for replacement by services
# from .ladder import IrusLadder  # Use models.ladder.IrusLadder instead
# from .posttable import IrusPostTable  # Use DiscordMessagingService instead
# from .imageprep import ImagePreprocessor  # Use ImageProcessingService instead

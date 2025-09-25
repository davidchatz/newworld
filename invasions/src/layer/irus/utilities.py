from .environ import IrusResources
from .member import IrusMember
from .services.member_management import MemberManagementService

logger = IrusResources.logger()


def update_invasions_for_new_member(member: IrusMember) -> str:
    """
    Legacy function maintained for backward compatibility.
    New code should use MemberManagementService directly.
    """
    logger.warning(
        "Using deprecated update_invasions_for_new_member. Use MemberManagementService instead."
    )

    service = MemberManagementService()
    return service.update_invasions_for_new_member(member)

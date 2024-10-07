import os
from .invasion import IrusInvasion
from .invasionlist import IrusInvasionList
from .member import IrusMember
from .memberlist import IrusMemberList
from .ladderrank import IrusLadderRank
from .ladder import IrusLadder
from .environ import IrusResources

logger = IrusResources.logger()


def update_invasions_for_new_member(member: IrusMember) -> str:
    logger.info(f'Ladder.update_invasions: {member}')
    invasionlist = IrusInvasionList.from_start(member.start)
    logger.debug(f'Invasions on or after {invasionlist.start}: {invasionlist.str()}')

    if invasionlist.count() == 0:
        mesg = f'\nNo invasions found to update\n'
    else:
        mesg = f'\n## Member flag updated in these invasions:\n'
        for i in invasionlist.invasions:
            try:
                ladder = IrusLadderRank.from_invasion_for_member(i, member)
                logger.debug(f'LadderRank.from_invasion_for_member: {ladder}')
                mesg += f'- {i.name} rank {ladder.rank}\n'
                ladder.update_membership(True)
            except ValueError:
                pass

    logger.info(mesg)
    return mesg
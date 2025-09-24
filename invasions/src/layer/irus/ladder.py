"""Backward compatibility facade for IrusLadder.

This module provides backward compatibility for the legacy IrusLadder class
while internally using the new repository pattern architecture.

DEPRECATED: This facade is provided for backward compatibility only.
New code should use irus.models.ladder.IrusLadder and irus.repositories.ladder.LadderRepository directly.
"""

import builtins
import json
import time
import warnings

from .environ import IrusResources
from .imageprep import ImagePreprocessor
from .ladderrank import IrusLadderRank  # Legacy facade
from .models.ladder import IrusLadder as PureLadder
from .models.ladderrank import IrusLadderRank as PureLadderRank
from .repositories.ladder import LadderRepository

# Issue deprecation warning when this module is imported
warnings.warn(
    "irus.ladder module is deprecated. Use irus.models.ladder.IrusLadder and "
    "irus.repositories.ladder.LadderRepository instead.",
    DeprecationWarning,
    stacklevel=2,
)


class IrusLadder:
    """Legacy IrusLadder class for backward compatibility.

    This class wraps the new repository pattern implementation to maintain
    backward compatibility with existing code.

    DEPRECATED: Use irus.models.ladder.IrusLadder and irus.repositories.ladder.LadderRepository instead.
    """

    def __init__(self, invasion, ranks: list):
        """Initialize from invasion and rank list (legacy API).

        Args:
            invasion: Invasion object (legacy)
            ranks: List of IrusLadderRank instances
        """
        # Extract invasion name from invasion object
        invasion_name = getattr(invasion, "name", str(invasion))

        # Convert legacy ranks to pure models if needed
        pure_ranks = []
        for rank in ranks:
            if hasattr(rank, "_model"):  # It's a legacy facade
                pure_ranks.append(rank._model)
            elif isinstance(rank, PureLadderRank):  # It's already pure
                pure_ranks.append(rank)
            else:  # It's a raw dict or other format
                # Try to convert from dict-like object
                item = {
                    "rank": getattr(rank, "rank", "01"),
                    "player": getattr(rank, "player", ""),
                    "score": getattr(rank, "score", 0),
                    "kills": getattr(rank, "kills", 0),
                    "deaths": getattr(rank, "deaths", 0),
                    "assists": getattr(rank, "assists", 0),
                    "heals": getattr(rank, "heals", 0),
                    "damage": getattr(rank, "damage", 0),
                    "member": getattr(rank, "member", False),
                    "ladder": getattr(rank, "ladder", False),
                    "adjusted": getattr(rank, "adjusted", False),
                    "error": getattr(rank, "error", False),
                }
                pure_ranks.append(PureLadderRank(invasion_name=invasion_name, **item))

        # Create the pure model
        self._model = PureLadder(invasion_name=invasion_name, ranks=pure_ranks)

        # Store invasion and ranks for legacy compatibility
        self.invasion = invasion
        self.ranks = [IrusLadderRank(invasion, rank.to_dict()) for rank in pure_ranks]

        # Create repository for database operations
        self._repository = LadderRepository()

    def invasion_key(self) -> str:
        """Get DynamoDB invasion key (legacy compatibility)."""
        return f"#ladder#{self._model.invasion_name}"

    @classmethod
    def from_ladder_image(cls, invasion, members, bucket: str, key: str):
        """Create ladder from image processing (legacy compatibility)."""
        # This method requires significant image processing logic that should be
        # moved to a service layer. For now, import and use the original functions.
        from . import ladder as ladder_module

        # Use the original processing functions
        response = ladder_module.import_ladder_table(bucket, key)
        table_blocks, blocks_map = ladder_module.extract_blocks(response)

        if len(table_blocks) == 0:
            raise ValueError(f"No invasion ladder not found in {bucket}/{key}")
        elif len(table_blocks) > 1:
            raise ValueError(f"Do not recognise invasion ladder in {bucket}/{key}")

        rows = ladder_module.get_rows_columns_map(table_blocks[0], blocks_map)
        ranks = ladder_module.generate_ladder_ranks(invasion, rows, members)

        # Create instance and save to database
        ladder = cls(invasion, ranks)
        repository = LadderRepository()
        repository.save_ladder_from_processing(ladder._model, key)

        return ladder

    @classmethod
    def from_roster_image(cls, invasion, members, bucket: str, key: str):
        """Create ladder from roster image (legacy compatibility)."""
        from . import ladder as ladder_module

        response = ladder_module.import_roster_table(bucket, key)
        candidates = ladder_module.reduce_list(response)
        matched = ladder_module.member_match(candidates, members)
        ranks = ladder_module.generate_roster_ranks(invasion, matched)

        # Create instance and save to database
        ladder = cls(invasion, ranks)
        repository = LadderRepository()
        repository.save_ladder_from_processing(ladder._model, key)

        return ladder

    @classmethod
    def from_invasion(cls, invasion):
        """Load ladder from database (legacy compatibility)."""
        repository = LadderRepository()
        invasion_name = getattr(invasion, "name", str(invasion))

        pure_ladder = repository.get_ladder(invasion_name)
        if pure_ladder is None:
            return cls(invasion, [])

        return cls(invasion, pure_ladder.ranks)

    @classmethod
    def from_csv(cls, invasion, csv: str, members):
        """Create ladder from CSV data (legacy compatibility)."""
        invasion_name = getattr(invasion, "name", str(invasion))
        ranks = []
        lines = csv.splitlines()

        for line in lines[1:]:  # Skip header
            cols = line.split(",")
            if len(cols) == 8:
                item = {
                    "rank": cols[0],
                    "player": cols[1],
                    "score": int(cols[2]),
                    "kills": int(cols[3]),
                    "deaths": int(cols[4]),
                    "assists": int(cols[5]),
                    "heals": int(cols[6]),
                    "damage": int(cols[7]),
                    "member": getattr(members, "is_member", lambda x: False)(cols[1]),
                    "ladder": True,
                    "adjusted": False,
                    "error": False,
                }
                ranks.append(PureLadderRank(invasion_name=invasion_name, **item))

        # Create instance and save to database
        ladder = cls(invasion, ranks)
        repository = LadderRepository()
        repository.save_ladder_from_processing(ladder._model, "csv")

        return ladder

    def contiguous_from_1_until(self) -> int:
        """Get contiguous rank count from 1 (legacy compatibility)."""
        return self._model.contiguous_from_1_until()

    def count(self) -> int:
        """Get total rank count (legacy compatibility)."""
        return self._model.count

    def members(self) -> int:
        """Get member count (legacy compatibility)."""
        return self._model.member_count

    def rank(self, rank: int):
        """Get rank by position (legacy compatibility)."""
        pure_rank = self._model.get_rank_by_position(rank)
        if pure_rank is None:
            return None
        return IrusLadderRank(self.invasion, pure_rank.to_dict())

    def member(self, player: str):
        """Get member rank (legacy compatibility)."""
        pure_rank = self._model.get_member_rank(player)
        if pure_rank is None:
            return None
        return IrusLadderRank(self.invasion, pure_rank.to_dict())

    def list(self, member: bool) -> str:
        """Get formatted player list (legacy compatibility)."""
        return self._model.list_members(member)

    def str(self) -> str:
        """Get string summary (legacy compatibility)."""
        return self._model.str()

    def csv(self) -> str:
        """Export to CSV (legacy compatibility)."""
        return self._model.to_csv()

    def markdown(self) -> str:
        """Export to markdown (legacy compatibility)."""
        return self._model.to_markdown()

    def post(self) -> builtins.list[str]:
        """Format for Discord posting (legacy compatibility)."""
        return self._model.post()

    def delete_from_table(self):
        """Delete ladder from database (legacy compatibility)."""
        self._repository.delete_ladder(self._model.invasion_name)

    def edit(
        self, rank: int, new_rank=None, member=None, player=None, score=None
    ) -> str:
        """Edit ladder rank (legacy compatibility)."""
        rank_obj = self.rank(rank)
        msg = ""

        if rank_obj:
            if new_rank is None:
                msg = f"Updating rank {rank} in invasion {self._model.invasion_name}: "
            elif int(new_rank) != rank:
                msg = f"Replacing rank {new_rank} in invasion {self._model.invasion_name} : "
                # Delete old rank
                self._repository.delete_rank(self._model.invasion_name, f"{rank:02d}")
                rank_obj.rank = f"{new_rank:02d}"

            # Apply updates
            if member is not None:
                msg += f"\nmember {rank_obj.member} -> {member}"
                rank_obj.member = bool(member)
                rank_obj.adjusted = True

            if player:
                msg += f"\nplayer {rank_obj.player} -> {player}"
                rank_obj.player = player
                rank_obj.adjusted = True

            if score:
                msg += f"\nscore {rank_obj.score} -> {score}"
                rank_obj.score = int(score)
                rank_obj.adjusted = True

            # Save changes
            rank_obj.update_item()
            msg += "\n" + rank_obj.str()

        elif player is None:
            msg = f"Rank {rank} in invasion {self._model.invasion_name} not found, need to provide player name to add new row"
        elif new_rank is not None and int(new_rank) != rank:
            msg = f"Rank {rank} does not exist to replace new rank {new_rank}"
        else:
            # Create new rank
            msg = f"Creating new entry for rank {rank} in invasion {self._model.invasion_name}"

            item = {
                "rank": f"{rank:02d}",
                "player": player,
                "score": int(score) if score else 0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
                "heals": 0,
                "damage": 0,
                "member": bool(member) if member is not None else False,
                "ladder": False,
                "adjusted": True,
                "error": False,
            }

            new_rank_obj = IrusLadderRank(self.invasion, item)
            new_rank_obj.update_item()
            self.ranks.append(new_rank_obj)
            msg += "\n" + new_rank_obj.str()

        return msg


# Import the original image processing functions for backward compatibility
# These should eventually be moved to a service layer

logger = IrusResources.logger()
table = IrusResources.table()
textract = IrusResources.textract()
s3 = IrusResources.s3()

# Original image processing functions (should be moved to service layer)


def save_enhanced_debug(
    bucket: str, key: str, response: dict, parsed_data: dict = None
):
    """Save both raw response and parsed data for debugging"""
    debug_data = {
        "textract_response": response,
        "parsed_data": parsed_data,
        "timestamp": time.ctime(),
    }
    debug_key = key.replace(".png", "_debug.json")
    s3.put_object(
        Bucket=bucket, Key=debug_key, Body=json.dumps(debug_data, indent=2, default=str)
    )
    logger.info(f"Enhanced debug saved to {bucket}/{debug_key}")


def import_ladder_table(bucket, key):
    # preprocess image for better OCR
    preprocessor = ImagePreprocessor()
    processed_key = preprocessor.preprocess_s3_image(bucket, key)

    # call textract on processed image
    response = textract.analyze_document(
        Document={"S3Object": {"Bucket": bucket, "Name": processed_key}},
        FeatureTypes=["TABLES"],
    )
    return response


def extract_blocks(response: dict):
    blocks = response["Blocks"]
    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block["Id"]] = block
        if block["BlockType"] == "TABLE":
            table_blocks.append(block)
    return table_blocks, blocks_map


def get_text(result, blocks_map):
    text = ""
    if "Relationships" in result:
        for relationship in result["Relationships"]:
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    word = blocks_map[child_id]
                    if word["BlockType"] == "WORD":
                        if (
                            "," in word["Text"]
                            and word["Text"].replace(",", "").isnumeric()
                        ):
                            text += '"' + word["Text"] + '"' + " "
                        else:
                            text += word["Text"] + " "
    return text


def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result["Relationships"]:
        if relationship["Type"] == "CHILD":
            for child_id in relationship["Ids"]:
                cell = blocks_map[child_id]
                if cell["BlockType"] == "CELL":
                    row_index = cell["RowIndex"]
                    col_index = cell["ColumnIndex"]
                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    logger.debug(f"get_rows_columns_map rows: {rows}")
    return rows


def numeric(orig: str) -> int:
    cleaned = (
        orig.replace("o", "0").replace("O", "0").replace("l", "1").replace("I", "1")
    )
    digits = "".join(filter(str.isnumeric, cleaned))
    return int(digits) if digits else 0


def generate_ladder_ranks(invasion, rows: list, members) -> list:
    rec = []

    for row_index, cols in rows.items():
        col_indices = len(cols.items())

        try:
            offset = 0 if col_indices == 8 else 1
            if col_indices >= 8 or col_indices <= 10:
                player = cols[2 + offset].rstrip()
                adjusted = False
                member = getattr(members, "is_member", lambda x, **kw: False)(
                    player, partial=False
                )
                if not member:
                    member = getattr(members, "is_member", lambda x, **kw: False)(
                        player, partial=True
                    )
                    if member:
                        adjusted = True

                result = IrusLadderRank(
                    invasion=invasion,
                    item={
                        "rank": f"{numeric(cols[1]):02d}",
                        "player": member if member else player,
                        "score": numeric(cols[3 + offset]),
                        "kills": numeric(cols[4 + offset]),
                        "deaths": numeric(cols[5 + offset]),
                        "assists": numeric(cols[6 + offset]),
                        "heals": numeric(cols[7 + offset]),
                        "damage": numeric(cols[8 + offset]),
                        "member": True if member else False,
                        "ladder": True,
                        "adjusted": adjusted,
                        "error": False,
                    },
                )

                if result.score > 0:
                    rec.append(result)
                else:
                    logger.info(f"Skipping {result} as score is 0")
            else:
                logger.info(f"Skipping {row_index} with {col_indices} items: {cols}")

        except Exception as e:
            logger.info(f"Skipping row {row_index} with {cols}, unable to scan: {e}")

    # Rank correction logic
    if len(rec) > 3:
        try:
            for r in range(0, len(rec)):
                if numeric(rec[r].rank) > 99:
                    logger.info(
                        f"Fixing rank {r + 1} from {rec[r].rank} to {rec[r].rank[:2]}"
                    )
                    rec[r].rank = rec[r].rank[:2]
                    rec[r].adjusted = True
        except Exception as e:
            logger.error(f"Unable to fix rank size: {e}")

        try:
            for r in range(0, len(rec) - 1):
                if numeric(rec[r].rank) > numeric(rec[r + 1].rank):
                    logger.info(
                        f"Fixing rank {r + 1} from {rec[r].rank} to {numeric(rec[r + 1].rank) - 1}"
                    )
                    rec[r].rank = f"{numeric(rec[r + 1].rank) - 1:02d}"
                    rec[r].adjusted = True
        except Exception as e:
            logger.error(f"Unable to fix rank order: {e}")

        pos = numeric(rec[0].rank)
        for r in range(1, len(rec)):
            pos += 1
            if numeric(rec[r].rank) != pos:
                logger.warning(f"Rank {r} is {rec[r].rank}, expected {pos}")
                rec[r].error = True

    logger.debug(f"scanned table: {rec}")
    return rec


def import_roster_table(bucket, key):
    preprocessor = ImagePreprocessor()
    processed_key = preprocessor.preprocess_s3_image(bucket, key)

    response = textract.detect_document_text(
        Document={"S3Object": {"Bucket": bucket, "Name": processed_key}}
    )
    return response


def reduce_list(table: dict) -> list:
    logger.debug("IrusLadder.reduce_list")
    response = []

    for block in table["Blocks"]:
        if block["BlockType"] != "PAGE":
            text = block["Text"]
            if not (text.isnumeric() or text == ":" or text.startswith("GROUP")):
                response.append(text)

    logger.debug(f"reduce_list: {response}")
    return response


def member_match(candidates: list, members) -> list:
    matched = []
    unmatched = []

    sorted_candidates = sorted(set(candidates))
    logger.debug(f"sorted_candidates ({len(sorted_candidates)}): {sorted_candidates}")

    for c in sorted_candidates:
        player = getattr(members, "is_member", lambda x, **kw: False)(c, partial=True)
        if player:
            matched.append(player)
        else:
            unmatched.append(c)

    sorted_matched = sorted(set(matched))

    logger.debug(f"matched ({len(sorted_matched)}): {sorted_matched}")
    logger.debug(f"unmatched ({len(unmatched)}): {unmatched}")

    return sorted_matched


def generate_roster_ranks(invasion, matched: list) -> list:
    rec = []
    rank = 1
    for m in matched:
        result = IrusLadderRank.from_roster(invasion=invasion, rank=rank, player=m)
        rec.append(result)
        rank += 1
    logger.debug(f"roster: {rec}")
    return rec

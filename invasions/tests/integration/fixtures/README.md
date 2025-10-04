# Test Fixtures Guide

This directory contains JSON fixtures for integration testing. Fixtures provide consistent, version-controlled test data that can be loaded into tests using the `FixtureLoader` utility.

## Directory Structure

```
fixtures/
├── __init__.py              # FixtureLoader utility class
├── README.md                # This file
├── member/                  # Member fixtures
│   ├── test_player1.json
│   ├── test_player2.json
│   └── ...
├── invasion/                # Invasion fixtures
│   ├── 99990301-bw.json
│   └── ...
├── ladder/                  # Ladder fixtures (full ladder with ranks)
│   ├── 99990301-bw.json
│   └── ...
└── month/                   # Monthly report fixtures
    └── 999903-expected.json
```

## Using FixtureLoader

### Loading Fixtures

```python
from tests.integration.fixtures import FixtureLoader
from irus.models.member import IrusMember
from irus.models.ladder import IrusLadder
from irus.models.invasion import IrusInvasion

# Load a single model
member = FixtureLoader.load(IrusMember, "test_player1")
invasion = FixtureLoader.load(IrusInvasion, "99990301-bw")
ladder = FixtureLoader.load(IrusLadder, "99990301-bw")

# Load a list of models
from irus.models.ladderrank import IrusLadderRank
ranks = FixtureLoader.load_list(IrusLadderRank, "99990301-bw-ranks")
```

### Saving Fixtures (for regression tests)

```python
# Capture production state for regression testing
month = IrusMonth.from_invasion_stats(3, 2024)
path = FixtureLoader.save(month, "202403-regression")
print(f"Saved regression fixture to {path}")

# Save a list of models
ranks = ladder.ranks
path = FixtureLoader.save_list(ranks, "99990301-bw-ranks", "ladderrank")
```

### Listing Available Fixtures

```python
# See what fixtures are available
member_fixtures = FixtureLoader.list_fixtures("member")
print(f"Available member fixtures: {member_fixtures}")
# Output: ['test_player1', 'test_player2', 'test_player3', 'test_player4']
```

## Data Sets

### Data Set 1: Basic Month (999903 - March 9999)
**Purpose**: Basic monthly report generation with full participation

- **Members**: test_player1 through test_player4 (4 total)
- **Invasions**: 99990301-bw, 99990315-ef, 99990329-wf (3 total)
- **Participation**: All members in all invasions
- **Test Coverage**: Basic monthly stats, win/loss tracking, average calculations

### Data Set 2: Partial Participation (999904 - April 9999)
**Purpose**: Test varied participation levels

- **Members**: 5 members with different activity levels
- **Invasions**: 4 invasions
- **Participation**: Varies from 0-4 invasions per member
- **Test Coverage**: Partial participation, inactive members, non-salary members

### Data Set 3: Mid-Month Join (999905 - May 9999)
**Purpose**: Test member join date filtering

- **Members**: 3 existing + 1 new (joins mid-month)
- **Invasions**: 6 invasions (3 before join, 3 after)
- **Test Coverage**: Start date filtering, eligibility logic

### Data Set 4: Ladder Variations (999906 - June 9999)
**Purpose**: Test ladder vs non-ladder participation

- **Invasions**: 3 invasions with varied ladder data
- **Variations**: ladder=true with score, ladder=true with score=0, ladder=false
- **Test Coverage**: Ladder filtering, stat calculations, participation without stats

### Data Set 5: Multi-Month Scenarios
**Purpose**: Test cross-month scenarios

- **Months**: 999908-999909, 999910-999911, 999912-100001
- **Test Coverage**: Month isolation, member evolution, activity patterns

## Naming Conventions

### Year 9999 Strategy
All test data uses year 9999 to avoid conflicts with production data:
- **Invasions**: `99990301-bw` (March 1, 9999)
- **Members**: start dates like `99990101` (January 1, 9999)
- **Monthly reports**: `999903` (March 9999)

### File Naming
- **Members**: `{player_name}.json` (lowercase, e.g., `test_player1.json`)
- **Invasions**: `{invasion_name}.json` (e.g., `99990301-bw.json`)
- **Ladders**: `{invasion_name}.json` (e.g., `99990301-bw.json`)
- **Monthly**: `{YYYYMM}-{descriptor}.json` (e.g., `999903-expected.json`)

## Creating New Fixtures

### Manual Creation
1. Create JSON file in appropriate subdirectory
2. Follow the model's Pydantic schema
3. Use consistent naming conventions

### From Production Data
```python
# Extract production data for regression testing
from tests.integration.fixtures import FixtureLoader

# Load from production
month = IrusMonth.from_table(month=3, year=2024)

# Save as fixture
FixtureLoader.save(month, "202403-production-snapshot")
```

### Validation
Fixtures are automatically validated against Pydantic models when loaded:
```python
# This will raise ValidationError if JSON doesn't match schema
member = FixtureLoader.load(IrusMember, "invalid_fixture")
```

## Best Practices

1. **Version Control**: Commit all fixtures to git for team consistency
2. **Descriptive Names**: Use clear, self-documenting fixture names
3. **Data Isolation**: Always use year 9999 for test data
4. **Cleanup**: Integration tests should clean up all test data after running
5. **Minimal Data**: Keep fixtures focused - only include necessary data
6. **Regression Tests**: Save production snapshots when fixing bugs

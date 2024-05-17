import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set

from tools.stats.import_test_stats import (
    ADDITIONAL_CI_FILES_FOLDER,
    TD_HEURISTIC_PREVIOUSLY_FAILED,
    TD_HEURISTIC_PREVIOUSLY_FAILED_ADDITIONAL,
)

from tools.testing.target_determination.heuristics.interface import (
    HeuristicInterface,
    TestPrioritizations,
)
from tools.testing.target_determination.heuristics.utils import (
    python_test_file_to_test_name,
)
from tools.testing.test_run import TestRun

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class PreviouslyFailedInPR(HeuristicInterface):
    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)

    def get_prediction_confidence(self, tests: List[str]) -> TestPrioritizations:
        critical_tests = get_previous_failures() | read_additional_test_failures_file()
        return TestPrioritizations(
            tests, {TestRun(test): 1 for test in critical_tests if test in tests}
        )


def get_previous_failures() -> Set[str]:
    path = REPO_ROOT / ADDITIONAL_CI_FILES_FOLDER / TD_HEURISTIC_PREVIOUSLY_FAILED
    if not os.path.exists(path):
        print(f"could not find path {path}")
        return set()
    with open(path) as f:
        return python_test_file_to_test_name(
            _parse_prev_failing_test_files(json.load(f))
        )


def _parse_prev_failing_test_files(last_failed_tests: Dict[str, bool]) -> Set[str]:
    prioritized_tests = set()

    # The keys are formatted as "test_file.py::test_class::test_method[params]"
    # We just need the test_file part
    for test in last_failed_tests:
        parts = test.split("::")
        if len(parts) > 1:
            test_file = parts[0]
            prioritized_tests.add(test_file)

    return prioritized_tests


def gen_additional_test_failures_file(tests: List[str]) -> None:
    # Segfaults usually result in no xml and some tests don't run through pytest
    # (ex doctests).  In these cases, there will be no entry in the pytest
    # cache, so we should generate a separate file for them and upload it to s3
    # along with the pytest cache
    with open(
        REPO_ROOT / ".pytest_cache" / TD_HEURISTIC_PREVIOUSLY_FAILED_ADDITIONAL, "w"
    ) as f:
        json.dump(tests, f, indent=2)


def read_additional_test_failures_file() -> Set[str]:
    path = REPO_ROOT / ".pytest_cache" / TD_HEURISTIC_PREVIOUSLY_FAILED_ADDITIONAL
    if not os.path.exists(path):
        print(f"could not find path {path}")
        return set()
    with open(path) as f:
        s = set(json.load(f))
        print(f"additional failures: {s}")
        return s

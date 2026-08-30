from ix_gabriella_brain.models import RouteKind
from ix_gabriella_brain.routing import DownshiftRouter


def test_simple_timer_routes_fast_lane() -> None:
    route = DownshiftRouter().route("set a timer for 5 minutes")
    assert route.route == RouteKind.FAST_LANE
    assert route.intent is not None
    assert route.intent.name == "set_timer"


def test_incomplete_timer_routes_clarification() -> None:
    route = DownshiftRouter().route("set a timer")
    assert route.route == RouteKind.CLARIFY_LANE


def test_memory_routes_approval() -> None:
    route = DownshiftRouter().route("remember that my wake word is Gabriella")
    assert route.route == RouteKind.APPROVAL_LANE
    assert route.required_approval


def test_complex_build_routes_brain_lane() -> None:
    route = DownshiftRouter().route("help me build a launch plan and compare the safest monetization paths")
    assert route.route == RouteKind.BRAIN_LANE
    assert route.complexity_score > 0.2


def test_high_risk_unstructured_routes_approval() -> None:
    route = DownshiftRouter().route("send the private file now")
    assert route.route == RouteKind.APPROVAL_LANE

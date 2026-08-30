from ix_assistant_core.identity import ASSISTANT_NAME, COPYRIGHT_HOLDER, PROJECT_NAME, WAKE_PHRASE


def test_identity_is_locked_to_ix_gabriella_and_bryce_lovell() -> None:
    assert PROJECT_NAME == "IX-Gabriella"
    assert ASSISTANT_NAME == "Gabriella"
    assert WAKE_PHRASE == "Hey Gabriella"
    assert COPYRIGHT_HOLDER == "Bryce Lovell"

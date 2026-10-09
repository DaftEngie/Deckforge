import deckforge


def test_frame_budget_matches_45_fps_target():
    assert deckforge.TARGET_FPS == 45
    assert deckforge.FRAME_BUDGET_MS == 22.2

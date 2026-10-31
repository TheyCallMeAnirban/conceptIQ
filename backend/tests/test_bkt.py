import pytest
from backend.app.domain.bkt import BKTEngine, BKTParameters, BKTUpdateResult


def test_bkt_correct_response_increases_mastery():
    """A correct observation must increase the probability of mastery."""
    prior = 0.30
    params = BKTParameters(p_init=0.30, p_transit=0.15, p_guess=0.20, p_slip=0.10)
    
    result = BKTEngine.update(prior=prior, is_correct=True, params=params)
    
    assert isinstance(result, BKTUpdateResult)
    assert result.observation is True
    assert result.posterior > prior
    assert result.delta > 0
    assert result.prior == prior
    assert result.p_transit == 0.15
    assert result.p_guess == 0.20
    assert result.p_slip == 0.10


def test_bkt_incorrect_response_decreases_mastery():
    """
    An incorrect observation must reduce P(L | obs=0).
    With standard parameters, the posterior P(L_t+1) should be lower than prior.
    """
    prior = 0.70
    params = BKTParameters(p_init=0.70, p_transit=0.10, p_guess=0.20, p_slip=0.10)
    
    result = BKTEngine.update(prior=prior, is_correct=False, params=params)
    
    assert result.observation is False
    assert result.posterior < prior
    assert result.delta < 0


def test_bkt_exact_hand_calculated_values():
    """
    Manual equation verification:
    P(L) = 0.5, S = 0.1, G = 0.2, T = 0.15
    If Correct:
      Num = 0.5 * (1 - 0.1) = 0.45
      Den = 0.45 + (1 - 0.5) * 0.2 = 0.45 + 0.10 = 0.55
      P(L | obs=1) = 0.45 / 0.55 = 0.818181...
      P(L_t+1) = 0.818181... + (1 - 0.818181...) * 0.15
               = 0.818181... + 0.181818... * 0.15
               = 0.818181... + 0.027272... = 0.84545... -> 0.8455
    """
    params = BKTParameters(p_init=0.5, p_transit=0.15, p_guess=0.20, p_slip=0.10)
    result = BKTEngine.update(prior=0.5, is_correct=True, params=params)
    
    assert abs(result.posterior - 0.8455) < 0.001
    assert abs(result.delta - (0.8455 - 0.5)) < 0.001


def test_bkt_bounds_and_extremes():
    """Verify BKT behavior at extreme ends (near 0 and near 1)."""
    params = BKTParameters(p_init=0.01, p_transit=0.10, p_guess=0.20, p_slip=0.10)
    
    res_low = BKTEngine.update(prior=0.001, is_correct=False, params=params)
    assert 0.0 <= res_low.posterior <= 1.0

    res_high = BKTEngine.update(prior=0.999, is_correct=True, params=params)
    assert 0.0 <= res_high.posterior <= 1.0


def test_bkt_invalid_parameters_raise():
    """Verify parameter bounds enforcement."""
    with pytest.raises(ValueError):
        BKTParameters(p_init=1.5)
    with pytest.raises(ValueError):
        BKTParameters(p_slip=-0.1)


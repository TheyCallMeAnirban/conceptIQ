from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BKTParameters:
    p_init: float = 0.20
    p_transit: float = 0.15
    p_guess: float = 0.20
    p_slip: float = 0.10

    def __post_init__(self):
        for name, val in [
            ("p_init", self.p_init),
            ("p_transit", self.p_transit),
            ("p_guess", self.p_guess),
            ("p_slip", self.p_slip),
        ]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"BKT parameter {name} must be between 0.0 and 1.0, got {val}")
        if self.p_guess + (1.0 - self.p_slip) <= 1e-6:
            raise ValueError("Degenerate BKT parameters: slip and guess cannot be simultaneously extreme")


@dataclass(frozen=True)
class BKTUpdateResult:
    prior: float
    posterior: float
    p_transit: float
    p_guess: float
    p_slip: float
    observation: bool
    delta: float


class BKTEngine:
    """
    Standard Bayesian Knowledge Tracing (Corbett & Anderson, 1995).
    Maintains pure binary observations.
    """

    @staticmethod
    def update(
        prior: float,
        is_correct: bool,
        params: Optional[BKTParameters] = None,
        p_transit: Optional[float] = None,
        p_guess: Optional[float] = None,
        p_slip: Optional[float] = None,
    ) -> BKTUpdateResult:
        """
        Updates the probability of mastery P(L) based on a binary observation.
        P(L_t+1) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
        """
        if not (0.0 <= prior <= 1.0):
            raise ValueError(f"BKT prior must be between 0.0 and 1.0, got {prior}")

        # Resolve parameters
        t = p_transit if p_transit is not None else (params.p_transit if params else 0.15)
        g = p_guess if p_guess is not None else (params.p_guess if params else 0.20)
        s = p_slip if p_slip is not None else (params.p_slip if params else 0.10)

        for name, val in [("p_transit", t), ("p_guess", g), ("p_slip", s)]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"BKT parameter {name} must be between 0.0 and 1.0, got {val}")

        # Clamp prior to safe numerical range [1e-4, 1 - 1e-4]
        clamped_prior = max(1e-4, min(1.0 - 1e-4, prior))

        if is_correct:
            # P(L | obs=1) = [ P(L) * (1 - S) ] / [ P(L) * (1 - S) + (1 - P(L)) * G ]
            numerator = clamped_prior * (1.0 - s)
            denominator = numerator + ((1.0 - clamped_prior) * g)
        else:
            # P(L | obs=0) = [ P(L) * S ] / [ P(L) * S + (1 - P(L)) * (1 - G) ]
            numerator = clamped_prior * s
            denominator = numerator + ((1.0 - clamped_prior) * (1.0 - g))

        p_learned_given_obs = numerator / denominator if denominator > 0 else clamped_prior

        # Knowledge transition step
        # P(L_t+1) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
        posterior = p_learned_given_obs + ((1.0 - p_learned_given_obs) * t)

        # Round to 4 decimal places for stable precision storage
        rounded_posterior = round(max(0.0, min(1.0, posterior)), 4)
        delta = round(rounded_posterior - prior, 4)

        return BKTUpdateResult(
            prior=prior,
            posterior=rounded_posterior,
            p_transit=t,
            p_guess=g,
            p_slip=s,
            observation=is_correct,
            delta=delta,
        )


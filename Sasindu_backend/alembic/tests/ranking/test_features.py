from app.ranking.features import CandidateInput, build_features


def test_build_features_normalizes_all_fields_to_unit_range():
    inputs = [
        CandidateInput(
            provider_id="p1",
            rating=4.5,
            availability_probability=0.9,
            reliability_alpha=8.0,
            reliability_beta=2.0,
            base_response_speed=10.0,
            eta_minutes=5.0,
        ),
        CandidateInput(
            provider_id="p2",
            rating=3.0,
            availability_probability=0.5,
            reliability_alpha=2.0,
            reliability_beta=8.0,
            base_response_speed=40.0,
            eta_minutes=30.0,
        ),
    ]
    features = build_features(inputs)
    for f in features:
        assert 0.0 <= f.rating <= 1.0
        assert 0.0 <= f.availability <= 1.0
        assert 0.0 <= f.reliability <= 1.0
        assert 0.0 <= f.response_speed <= 1.0
        assert 0.0 <= f.eta_score <= 1.0


def test_lower_eta_yields_higher_eta_score():
    inputs = [
        CandidateInput(
            provider_id="fast",
            rating=4.0,
            availability_probability=0.8,
            reliability_alpha=5.0,
            reliability_beta=5.0,
            base_response_speed=15.0,
            eta_minutes=3.0,
        ),
        CandidateInput(
            provider_id="slow",
            rating=4.0,
            availability_probability=0.8,
            reliability_alpha=5.0,
            reliability_beta=5.0,
            base_response_speed=15.0,
            eta_minutes=45.0,
        ),
    ]
    features = {f.provider_id: f for f in build_features(inputs)}
    assert features["fast"].eta_score > features["slow"].eta_score

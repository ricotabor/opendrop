import math

import pytest

from opendrop.app.ift.analysis_model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.app.ift.validation.image_annotator_validator import IFTImageAnnotatorValidator
from opendrop.mytypes import Rect2


@pytest.fixture
def good_image_annotator():
    image_annotator = IFTImageAnnotator()

    image_annotator.bn_drop_region_px.set(Rect2(x=10, y=20, w=30, h=40))
    image_annotator.bn_needle_region_px.set(Rect2(x=1, y=2, w=3, h=4))
    image_annotator.bn_needle_width.set(3)

    return image_annotator


@pytest.fixture
def good_image_annotator_and_validator(good_image_annotator):
    validator = IFTImageAnnotatorValidator(good_image_annotator, lambda: (100, 100))
    return good_image_annotator, validator


def test_validator_accepts_valid_data(good_image_annotator_and_validator):
    image_annotator, validator = good_image_annotator_and_validator

    assert validator.is_valid is True


@pytest.mark.parametrize('is_valid, drop_region_px', [
    (False, None),  # invalid because is None
    (False, Rect2(x=0, y=0, w=0, h=0)),  # invalid because has no finite size
    (False, Rect2(x=100, y=100, w=10, h=10)),  # invalid because outside of image extents
    (True, Rect2(x0=-30, y0=-20, x1=10, y1=10)),
    (True, Rect2(x0=-30, y0=-20, x1=110, y1=110)),
])
def test_validator_checks_drop_region(good_image_annotator_and_validator, is_valid, drop_region_px):
    image_annotator, validator = good_image_annotator_and_validator

    image_annotator.bn_drop_region_px.set(drop_region_px)

    assert validator.is_valid is is_valid


# Similar to test_validator_rejects_invalid_drop_region
@pytest.mark.parametrize('is_valid, needle_region_px', [
    (False, None),
    (False, Rect2(x=0, y=0, w=0, h=0)),
    (False, Rect2(x=100, y=100, w=10, h=10)),
    (True, Rect2(x0=-30, y0=-20, x1=10, y1=10)),
    (True, Rect2(x0=-30, y0=-20, x1=110, y1=110)),
])
def test_validator_checks_needle_region(good_image_annotator_and_validator, is_valid, needle_region_px):
    image_annotator, validator = good_image_annotator_and_validator

    image_annotator.bn_needle_region_px.set(needle_region_px)

    assert validator.is_valid is is_valid


@pytest.mark.parametrize('is_valid, drop_region_px', [
    (False, None),  # invalid because is None
    (False, Rect2(x=0, y=0, w=0, h=0)),  # invalid because has no finite size
    (True, Rect2(x=100, y=100, w=10, h=10)),  # assumed to be valid (not None and finite size) since no size hint.
])
def test_validator_checks_drop_region_when_no_size_hint(good_image_annotator, is_valid, drop_region_px):
    image_annotator = good_image_annotator
    validator = IFTImageAnnotatorValidator(image_annotator, lambda: None)

    image_annotator.bn_drop_region_px.set(drop_region_px)

    assert validator.is_valid is is_valid


@pytest.mark.parametrize('needle_width', [
    None,
    -1.23,
    0.0,
    math.nan,
    math.inf
])
def test_validator_rejects_invalid_needle_width(good_image_annotator_and_validator, needle_width):
    image_annotator, validator = good_image_annotator_and_validator

    image_annotator.bn_needle_width.set(needle_width)

    assert validator.is_valid is False
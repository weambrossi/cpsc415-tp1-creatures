"""Fakes for the two billed calls the web server makes, so the server and the page can be tested
without a key (plan rule 5: build the page against fake data until the critic-checker merges).

The prompt, the requirements, and the name rules still come from the real generator: only the
image call and the critique call are replaced.
"""
import base64

# A real 1x1 PNG, so the browser has an image it can draw.
PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


class FakeImageModel:
    """Stands in for one Image API call. Records what it was asked."""

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def __call__(self, prompt, seed):
        self.calls.append({"prompt": prompt, "seed": seed})
        if self.error:
            raise self.error
        return {"bytes": PIXEL_PNG, "media_type": "image/png", "cost": 0.014, "model": "fake/image-model"}


class FakeCritic:
    """Stands in for the critic-checker: returns what app.critic.critique_one returns (spec.md, C8).

    By default it answers every requirement, says the last one is unmet, and reads the name
    correctly, so a page test sees both a met and an unmet line.
    """

    def __init__(self, unmet_last=True, text_read=None, error=None):
        self.calls = []
        self.unmet_last = unmet_last
        self.text_read = text_read
        self.error = error

    def __call__(self, image_bytes, entry):
        self.calls.append({"image_bytes": image_bytes, "entry": entry})
        if self.error:
            raise self.error
        reqs = entry["requirements"]
        checks = [{"requirement": r, "met": not (self.unmet_last and i == len(reqs) - 1),
                   "evidence": "fake evidence"} for i, r in enumerate(reqs)]
        unmet = [c["requirement"] for c in checks if not c["met"]]
        read = entry["expected_text"] if self.text_read is None else self.text_read
        matches = read.strip().upper() == entry["expected_text"].upper()
        problems = [f"unmet: {r}" for r in unmet]
        if not matches:
            problems.append(f"name reads {read!r}, expected {entry['expected_text']!r}")
        return {
            "model": "fake/vision-model", "critique": {"checks": checks}, "raw": "{}",
            "usage": {"in": 1, "out": 1, "cost": 0.001, "finish": "stop"},
            "check": {"ok": not unmet, "problems": [f"unmet: {r}" for r in unmet],
                      "unmet": unmet, "missing": [], "extra": []},
            "text_read": read, "text_matches": matches,
            "usage_text": {"in": 1, "out": 1, "cost": 0.0005, "finish": "stop"},
            "passes": not problems, "problems": problems,
        }

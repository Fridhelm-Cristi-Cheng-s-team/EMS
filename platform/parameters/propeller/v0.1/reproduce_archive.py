"""Verify the A-V3-05AD archive and reproduce 05A and 05AR in a temporary directory."""

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
ZIP_05A = "av3-05a-deliverables.zip"
ZIP_05AR = "av3-05ar-deliverables.zip"
ORIGINAL = "calculations/original/replayed-package"
REVISED = "calculations/revised"

OUTPUTS_05A = (
    "mission_shaft_energy.json",
    "motor_requirements.csv",
    "propeller_candidate_comparison.csv",
    "propeller_map.csv",
    "propeller_parameters.json",
    "propulsion_matching_results.csv",
    "results.json",
    "sensitivity_results.csv",
    "verification_interpolation.json",
)

# 05AR output name -> location of the archived, unpacked copy.
OUTPUTS_05AR = {
    "propeller_parameters.json": "propeller_parameters.json",
    "map_comparison.csv": "maps/map_comparison.csv",
    "parameter_comparison.csv": "maps/parameter_comparison.csv",
    "propeller_map.csv": "maps/propeller_map.csv",
    "propeller_map_comparison.png": "maps/propeller_map_comparison.png",
    "motor_duty_PROP-B.json": "motor_requirements/motor_duty_PROP-B.json",
    "motor_requirements_PROP-B.csv": "motor_requirements/motor_requirements_PROP-B.csv",
    "motor_requirements_all_candidates.csv": "motor_requirements/motor_requirements_all_candidates.csv",
    "independent_recalculation.csv": "results/independent_recalculation.csv",
    "match_comparison.csv": "results/match_comparison.csv",
    "mission_comparison.csv": "results/mission_comparison.csv",
    "mission_shaft_energy.json": "results/mission_shaft_energy.json",
    "propulsion_matching_results.csv": "results/propulsion_matching_results.csv",
    "results.json": "results/results.json",
    "sensitivity_results.csv": "results/sensitivity_results.csv",
    "stress_boundary_diagnostics.csv": "results/stress_boundary_diagnostics.csv",
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def files(directory):
    return {file.relative_to(directory).as_posix() for file in directory.rglob("*") if file.is_file()}


def require_paths(label, actual, expected):
    missing, extra = sorted(expected - actual), sorted(actual - expected)
    if missing or extra:
        raise ValueError(f"{label}: missing={missing}, extra={extra}")


def verify_manifest(path, directory, expected=None):
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        sha, name = line.split(maxsplit=1)
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() in entries:
            raise ValueError(f"{path}: invalid or repeated path {name}")
        entries[relative.as_posix()] = sha
    if expected is not None:
        require_paths(str(path), set(entries), expected)
    for name, sha in entries.items():
        actual = digest(directory / name)
        if actual != sha:
            raise ValueError(f"{directory / name}: expected {sha}, got {actual}")
    return len(entries)


def require_same(actual, expected):
    actual_sha = digest(actual)
    expected_sha = digest(expected)
    if actual_sha != expected_sha:
        raise ValueError(
            f"Byte mismatch: {actual} ({actual.stat().st_size} bytes, {actual_sha}) "
            f"vs {expected} ({expected.stat().st_size} bytes, {expected_sha})"
        )


def extract(name, destination):
    sources = ROOT / "sources"
    verify_manifest(sources / (name + ".sha256"), sources, {name})
    with zipfile.ZipFile(sources / name) as bundle:
        bad_member = bundle.testzip()
        if bad_member is not None:
            raise ValueError(f"{name}: ZIP CRC failure in {bad_member}")
        bundle.extractall(destination)
    count = verify_manifest(destination / "SHA256SUMS", destination)
    print(f"PASS: {name} SHA-256, ZIP CRC and {count} internal hashes", flush=True)


def run(directory, env, script, *args):
    print(f"Running {directory.name}/{script} {' '.join(args)}", flush=True)
    subprocess.run(
        [sys.executable, "-X", "utf8", script, *args],
        cwd=directory,
        env=env,
        check=True,
    )


def reproduce(scratch, check_only):
    original = scratch / "05A"
    revised = scratch / "05AR"
    extract(ZIP_05A, original)
    extract(ZIP_05AR, revised)
    require_same(revised / "original" / ZIP_05A, ROOT / "sources" / ZIP_05A)
    verify_manifest(revised / "original/05A-ZIP-SHA256", revised, {f"original/{ZIP_05A}"})

    original_archive = ROOT / ORIGINAL
    require_paths("unpacked 05A archive", files(original_archive),
                  files(original) | {f"reproduced/{name}" for name in OUTPUTS_05A})
    verify_manifest(original_archive / "SHA256SUMS", original_archive)
    for name in sorted(files(original)):
        require_same(original_archive / name, original / name)
    for name in OUTPUTS_05A:
        require_same(original_archive / "reproduced" / name, original / name)

    revised_archive = ROOT / REVISED
    for name in sorted(files(revised / "inputs")):
        require_same(revised_archive / "inputs" / name, revised / "inputs" / name)
    for name in ("checks.py", "model.py", "plot_maps.py", "review.py", "original_reproduction.sh", "package.sh"):
        require_same(revised_archive / name, revised / name)
    require_paths("05AR ZIP outputs", files(revised / "outputs"), set(OUTPUTS_05AR))
    for name, path in OUTPUTS_05AR.items():
        require_same(ROOT / path, revised / "outputs" / name)
    print("PASS: unpacked evidence matches both original ZIPs", flush=True)
    if check_only:
        return

    from importlib.metadata import version

    packages = ", ".join(f"{name} {version(name)}" for name in ("numpy", "scipy", "matplotlib"))
    print(f"{platform.system()} {platform.machine()}, Python {platform.python_version()}, {packages}", flush=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLCONFIGDIR=str(scratch / "matplotlib"))
    run(original, env, "study.py", "--out", "reproduced")
    run(original, env, "verify_interpolation.py", "--map", "reproduced/propeller_map.csv",
        "--out", "reproduced/verification_interpolation.json")
    run(original, env, "annotate_parameter_sources.py", "reproduced/propeller_parameters.json")
    require_paths("05A replay", files(original / "reproduced"), set(OUTPUTS_05A))
    for name in OUTPUTS_05A:
        require_same(original / "reproduced" / name, original / name)
    print("PASS: 05A reproduced all 9 outputs byte for byte", flush=True)

    # 05AR takes the historical 05A package as its comparison source.
    run(revised, env, "review.py", "--original", str(original), "--out", "reproduced")
    run(revised, env, "plot_maps.py", "--original", str(original), "--out", "reproduced")
    require_paths("05AR replay", files(revised / "reproduced"), set(OUTPUTS_05AR))
    for name, path in OUTPUTS_05AR.items():
        require_same(revised / "reproduced" / name, ROOT / path)
    print("PASS: 05AR reproduced all 16 outputs byte for byte", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Verify archive integrity without running the models")
    args = parser.parse_args()
    count = verify_manifest(ROOT / "SHA256SUMS", ROOT, files(ROOT) - {"SHA256SUMS"})
    print(f"PASS: all {count} archive hashes and file paths", flush=True)
    with tempfile.TemporaryDirectory(prefix="av3-05ad-") as temp:
        reproduce(Path(temp), args.check_only)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(error.returncode if error.returncode > 0 else 128 - error.returncode)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)

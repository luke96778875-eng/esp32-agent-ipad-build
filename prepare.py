"""Prepare a pinned public source tree without adding credentials or capabilities."""
import pathlib
import plistlib
import subprocess
import sys

UPSTREAM_COMMIT = "0b22d9a99ce7bc887860e46fa1a61761836a55d2"


def prepare(root):
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM_COMMIT:
        raise ValueError("Unexpected upstream source revision")
    ios = root / "ios"
    local = ios / "Config" / "Local.xcconfig"
    if local.exists():
        raise ValueError("Refusing to include an existing private Local.xcconfig")
    local.write_text(
        "// Public build settings only. No credentials or developer account.\n"
        "IA_BUNDLE_ID = com.example.esp32agent.ipad\n"
        "IA_ENTITLEMENTS =\n"
        "IA_WIDGET_ENTITLEMENTS =\n"
        "IA_PRESET_BASE_URL =\n"
        "IA_PRESET_MODEL =\n"
        "IA_PRESET_KEY =\n"
        "IA_POSTHOG_KEY =\n"
        "IA_TRIAL_ORIGIN =\n"
        "IA_STORE_BUILD = NO\n",
        encoding="utf-8",
    )
    # The checked-in Xcode project already has universal app targets; make its
    # project-level default agree, without regenerating it or changing Swift code.
    project = ios / "IPhoneAgent.xcodeproj" / "project.pbxproj"
    text = project.read_text(encoding="utf-8")
    if "TARGETED_DEVICE_FAMILY = 1;" not in text:
        raise ValueError("Unexpected Xcode project device-family settings")
    project.write_text(
        text.replace("TARGETED_DEVICE_FAMILY = 1;", 'TARGETED_DEVICE_FAMILY = "1,2";'),
        encoding="utf-8",
    )
    # Keep XcodeGen's source of truth consistent with the checked-in project.
    spec = ios / "project.yml"
    text = spec.read_text(encoding="utf-8")
    if 'TARGETED_DEVICE_FAMILY: "1"' not in text:
        raise ValueError("Unexpected XcodeGen device-family setting")
    spec.write_text(text.replace('TARGETED_DEVICE_FAMILY: "1"', 'TARGETED_DEVICE_FAMILY: "1,2"'), encoding="utf-8")
    for relative in ("IPhoneAgent/Info.plist", "AgentActivity/Info.plist"):
        with (ios / relative).open("rb") as f:
            info = plistlib.load(f)
        if info.get("IAPresetKey") not in (None, "", "$(IA_PRESET_KEY)"):
            raise ValueError("Unexpected embedded model credential")
    print("Prepared pinned upstream iPad build; no Swift code or firmware changed.")


if __name__ == "__main__":
    prepare(pathlib.Path(sys.argv[1]).resolve())

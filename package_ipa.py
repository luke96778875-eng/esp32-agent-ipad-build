"""Validate physical-device binaries and package an unsigned, unencrypted IPA."""
import hashlib
import json
import pathlib
import plistlib
import shutil
import struct
import sys
import tempfile
import zipfile


def macho(path):
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError("Truncated executable")
    magic, cpu, _, _, ncmds, size, _, _ = struct.unpack_from("<8I", data)
    if magic != 0xFEEDFACF or cpu != 0x0100000C:
        raise ValueError("Expected a 64-bit ARM physical-device executable")
    offset, platforms, cryptids = 32, [], []
    end = 32 + size
    if end > len(data):
        raise ValueError("Truncated Mach-O load commands")
    for _ in range(ncmds):
        cmd, length = struct.unpack_from("<II", data, offset)
        if length < 8 or offset + length > end:
            raise ValueError("Invalid Mach-O load command")
        if cmd == 0x32:
            platforms.append(struct.unpack_from("<I", data, offset + 8)[0])
        if cmd in (0x21, 0x2C):
            cryptids.append(struct.unpack_from("<I", data, offset + 16)[0])
        offset += length
    if platforms != [2] or any(cryptids):
        raise ValueError("Executable is not unencrypted iOS device code")
    return {"architecture": "arm64", "platform": "iOS device", "encrypted": False}


def package(app, output):
    with (app / "Info.plist").open("rb") as f:
        info = plistlib.load(f)
    if 2 not in info.get("UIDeviceFamily", []):
        raise ValueError("iPad device family is missing")
    if info.get("CFBundleSupportedPlatforms") != ["iPhoneOS"]:
        raise ValueError("This is not a physical-device app")
    if info.get("IAPresetKey") not in (None, ""):
        raise ValueError("Model credential or unresolved preset in build")
    if info.get("IATrialOrigin") not in (None, ""):
        raise ValueError("Unexpected official trial service in personal build")
    if int(info.get("MinimumOSVersion", "999").split(".")[0]) > 27:
        raise ValueError("App requires an OS newer than the target iPad")
    binaries = [{"app": app.name, **macho(app / info["CFBundleExecutable"])}]
    for extension in sorted((app / "PlugIns").glob("*.appex")):
        with (extension / "Info.plist").open("rb") as f:
            ext = plistlib.load(f)
        binaries.append({"app": extension.name, **macho(extension / ext["CFBundleExecutable"])})
    output.mkdir(parents=True, exist_ok=True)
    ipa = output / "ESP32-Agent-iPad-unsigned.ipa"
    with tempfile.TemporaryDirectory() as scratch:
        payload = pathlib.Path(scratch) / "Payload"
        payload.mkdir()
        shutil.copytree(app, payload / app.name, symlinks=True)
        shutil.make_archive(str(output / "ESP32-Agent-iPad-unsigned"), "zip", scratch, "Payload")
    (output / "ESP32-Agent-iPad-unsigned.zip").replace(ipa)
    with zipfile.ZipFile(ipa) as z:
        bad = z.testzip()
        if bad:
            raise ValueError("Corrupt IPA member: " + bad)
    report = {
        "upstream": "https://github.com/onehumanbeing/esp32-iphone-agent",
        "source_commit": "0b22d9a99ce7bc887860e46fa1a61761836a55d2",
        "bundle_id": info["CFBundleIdentifier"],
        "device_families": info["UIDeviceFamily"],
        "minimum_os": info["MinimumOSVersion"],
        "binaries": binaries,
        "bytes": ipa.stat().st_size,
        "sha256": hashlib.sha256(ipa.read_bytes()).hexdigest(),
        "requires_local_signing": True,
        "ipad_hardware_control_verified": False,
        "dsh_go_integration_verified": False,
    }
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    package(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve())

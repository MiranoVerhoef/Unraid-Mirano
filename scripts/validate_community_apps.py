from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent


def fail(path: Path, message: str) -> None:
    raise SystemExit(f"{path.relative_to(ROOT)}: {message}")


def required_text(path: Path, root: ET.Element, tag: str) -> str:
    value = (root.findtext(tag) or "").strip()
    if not value:
        fail(path, f"<{tag}> must not be empty")
    return value


def require_https(path: Path, root: ET.Element, tag: str) -> None:
    value = required_text(path, root, tag)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(path, f"<{tag}> must contain an HTTPS URL")


profile_path = ROOT / "ca_profile.xml"
profile = ET.parse(profile_path).getroot()
if profile.tag != "CommunityApplications":
    fail(profile_path, "root element must be <CommunityApplications>")
required_text(profile_path, profile, "Profile")
for profile_url in ("Icon", "WebPage", "Forum"):
    require_https(profile_path, profile, profile_url)

template_count = 0
for template_path in sorted(ROOT.rglob("*.xml")):
    if template_path in {profile_path, ROOT / "ca_profile" / "ca_profile.xml"}:
        continue
    template = ET.parse(template_path).getroot()
    source = template_path.read_text(encoding="utf-8")
    if "YOUR_" in source or "YOUR-" in source:
        fail(template_path, "placeholder value remains")
    if template.tag == "Container":
        required_text(template_path, template, "Name")
        required_text(template_path, template, "Repository")
    elif template.tag == "Plugin":
        required_text(template_path, template, "Name")
        require_https(template_path, template, "PluginURL")
        if not required_text(template_path, template, "PluginURL").endswith(".plg"):
            fail(template_path, "<PluginURL> must point to a .plg manifest")
        for field in ("Overview", "Category"):
            required_text(template_path, template, field)
        for field in ("Support", "Project", "Icon"):
            require_https(template_path, template, field)
    else:
        fail(template_path, f"unsupported root element <{template.tag}>")
    template_count += 1

if template_count == 0:
    raise SystemExit("No Community Apps templates found")

print(f"Validated ca_profile.xml and {template_count} Community Apps templates")

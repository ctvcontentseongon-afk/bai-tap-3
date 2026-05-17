"""
brand_loader.py — Đọc và xử lý brand profile cho SEONGON Report Generator.

Usage:
    from scripts.brand_loader import load_brand, get_color, get_font, format_vn_number
    brand = load_brand("default")
"""

import json
import re
from pathlib import Path

from pptx.dml.color import RGBColor

BASE_DIR = Path(__file__).resolve().parent.parent
BRAND_DIR = BASE_DIR / "brand_profiles"

# Schema tối thiểu cần có trong mọi brand profile
REQUIRED_COLORS = {"primary", "secondary", "accent", "background",
                   "text_dark", "text_light", "success", "warning", "danger"}
REQUIRED_FONTS  = {"heading", "body", "fallback"}
REQUIRED_STYLE  = {"tone", "number_format", "currency"}

# ---------------------------------------------------------------------------
# Load & validate
# ---------------------------------------------------------------------------

def load_brand(profile_name: str) -> dict:
    """Đọc brand profile từ file JSON, validate schema, return dict."""
    profile_path = BRAND_DIR / f"{profile_name}.json"
    if not profile_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy brand profile '{profile_name}' tại {profile_path}\n"
            f"Các profile có sẵn: {list_profiles()}"
        )

    with open(profile_path, encoding="utf-8") as f:
        data = json.load(f)

    # Lọc bỏ các key bắt đầu bằng _ (comment/hướng dẫn)
    data = _strip_comments(data)

    errors = validate_brand(data)
    if errors:
        raise ValueError(f"Brand profile '{profile_name}' có lỗi:\n" + "\n".join(f"  • {e}" for e in errors))

    return data


def _strip_comments(obj):
    """Đệ quy xóa key bắt đầu bằng '_' khỏi dict."""
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items() if not k.startswith("_")}
    return obj


def validate_brand(data: dict) -> list[str]:
    """Kiểm tra schema brand profile. Trả về list lỗi (rỗng = hợp lệ)."""
    errors = []

    for field in ("client_name", "domain", "logo_path"):
        if not data.get(field):
            errors.append(f"Thiếu field bắt buộc: '{field}'")

    colors = data.get("colors", {})
    for key in REQUIRED_COLORS:
        if key not in colors:
            errors.append(f"Thiếu colors.{key}")
        elif not _is_valid_hex(colors[key]):
            errors.append(f"colors.{key} không hợp lệ: '{colors[key]}' — cần dạng #RRGGBB")

    fonts = data.get("fonts", {})
    for key in REQUIRED_FONTS:
        if key not in fonts:
            errors.append(f"Thiếu fonts.{key}")

    style = data.get("style", {})
    for key in REQUIRED_STYLE:
        if key not in style:
            errors.append(f"Thiếu style.{key}")

    return errors


def _is_valid_hex(value: str) -> bool:
    return bool(re.match(r"^#[0-9A-Fa-f]{6}$", str(value)))


def list_profiles() -> list[str]:
    """Liệt kê tên các profile có sẵn (bỏ qua file bắt đầu bằng _)."""
    return [
        p.stem for p in BRAND_DIR.glob("*.json")
        if not p.stem.startswith("_")
    ]

# ---------------------------------------------------------------------------
# Getter helpers
# ---------------------------------------------------------------------------

def get_color(brand: dict, color_name: str) -> str:
    """Lấy hex color từ brand dict. Fallback #000000 nếu không tìm thấy."""
    return brand.get("colors", {}).get(color_name, "#000000")


def get_rgb(brand: dict, color_name: str) -> RGBColor:
    """Lấy RGBColor (python-pptx) từ brand dict."""
    return hex_to_rgb(get_color(brand, color_name))


def hex_to_rgb(hex_color: str) -> RGBColor:
    """Chuyển hex string '#RRGGBB' sang RGBColor."""
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten_hex(hex_color: str, factor: float = 0.85) -> str:
    """Làm nhạt màu hex — dùng cho nền vùng phân tích."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = round(r + (255 - r) * factor)
    g = round(g + (255 - g) * factor)
    b = round(b + (255 - b) * factor)
    return f"#{r:02X}{g:02X}{b:02X}"


def get_font(brand: dict, role: str = "body") -> str:
    """
    Lấy tên font theo role ('heading' / 'body').
    Không kiểm tra font có cài hay không — python-pptx sẽ fallback tự động.
    """
    fonts = brand.get("fonts", {})
    return fonts.get(role, fonts.get("fallback", "Arial"))

# ---------------------------------------------------------------------------
# Logo helper
# ---------------------------------------------------------------------------

def get_logo_path(brand: dict, skill_base_dir: Path) -> Path:
    """
    Trả về Path tuyệt đối của file logo.
    Nếu file không tồn tại, tạo placeholder bằng Pillow.
    """
    rel = brand.get("logo_path", "brand_profiles/logos/_placeholder.png")
    abs_path = skill_base_dir / rel

    if not abs_path.exists():
        _create_placeholder_logo(abs_path, brand.get("client_name", "LOGO"),
                                 get_color(brand, "primary"))
    return abs_path


def _create_placeholder_logo(path: Path, text: str, bg_hex: str):
    """Tạo logo placeholder PNG bằng Pillow nếu chưa có."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        path.parent.mkdir(parents=True, exist_ok=True)
        w, h = 400, 120
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bg = _hex_to_tuple(bg_hex) + (255,)
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=16, fill=bg)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tx = (w - (bbox[2] - bbox[0])) // 2
        ty = (h - (bbox[3] - bbox[1])) // 2 - 4
        draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)
        img.save(path, "PNG")
    except ImportError:
        # Pillow chưa cài — bỏ qua, slide sẽ không có logo
        pass


def _hex_to_tuple(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

# ---------------------------------------------------------------------------
# Format số
# ---------------------------------------------------------------------------

def format_vn_number(n) -> str:
    """1234567 → '1.234.567'"""
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def format_vn_pct(f, decimals: int = 1) -> str:
    """0.1234 → '12,3%'"""
    try:
        return f"{float(f) * 100:.{decimals}f}%".replace(".", ",")
    except (TypeError, ValueError):
        return str(f)


def format_delta(current, previous, brand: dict, pct: bool = True) -> tuple[str, str]:
    """
    So sánh 2 giá trị, trả về (text_delta, hex_color).
    Ví dụ: (12450, 10820, brand) → ('▲ +15,1%', '#28A745')
    """
    try:
        cur, prev = float(current), float(previous)
        if prev == 0:
            return ("N/A", get_color(brand, "text_light"))
        delta = (cur - prev) / prev
        if pct:
            text = f"{'▲' if delta >= 0 else '▼'} {'+' if delta >= 0 else ''}{delta * 100:.1f}%".replace(".", ",")
        else:
            diff = cur - prev
            text = f"{'▲' if diff >= 0 else '▼'} {'+' if diff >= 0 else ''}{diff:.1f}".replace(".", ",")
        color = get_color(brand, "success") if delta >= 0 else get_color(brand, "danger")
        return (text, color)
    except (TypeError, ValueError):
        return ("N/A", get_color(brand, "text_light"))


# ---------------------------------------------------------------------------
# Quick test khi chạy trực tiếp
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    profile = sys.argv[1] if len(sys.argv) > 1 else "default"
    brand = load_brand(profile)

    print(f"\n=== Brand Profile: {profile} ===")
    print(f"  Client : {brand['client_name']}")
    print(f"  Domain : {brand['domain']}")
    print(f"  Primary: {get_color(brand, 'primary')} → RGB{hex_to_rgb(brand['colors']['primary'])}")
    print(f"  Font   : {get_font(brand, 'heading')} / {get_font(brand, 'body')}")
    print(f"  Profiles có sẵn: {list_profiles()}")
    print(f"\n  Format số:")
    print(f"    1234567   → '{format_vn_number(1234567)}'")
    print(f"    0.1537    → '{format_vn_pct(0.1537)}'")
    delta_text, delta_color = format_delta(12450, 10820, brand)
    print(f"    12450 vs 10820 → '{delta_text}' (màu {delta_color})")
    print()

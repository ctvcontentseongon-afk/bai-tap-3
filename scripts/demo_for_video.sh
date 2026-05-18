#!/bin/bash
# demo_for_video.sh — Demo toàn bộ 3 SEONGON Claude Skills

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$WORKSPACE/.venv/bin/python3"

# ─── INTRO ────────────────────────────────────────────────────────────────────
clear
echo "🎯 =============================================="
echo "🎯   DEMO: SEONGON Claude Workspace — 3 Skills"
echo "🎯 =============================================="
echo ""
echo "   Workspace: $WORKSPACE"
echo "   Python   : $PYTHON"
sleep 3

# ─── WORKSPACE STRUCTURE ──────────────────────────────────────────────────────
echo ""
echo "📁 Cấu trúc workspace:"
echo "──────────────────────────────────────────────"
ls -1 "$WORKSPACE/.claude/skills/"
sleep 3

# ─── SKILL 1 ──────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 SKILL 1: Project Status Tracker"
echo "   Đọc Google Sheets → phân loại task → báo cáo tuần .md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 2
echo ""
"$PYTHON" "$WORKSPACE/.claude/skills/project-status-tracker/scripts/gsheet_reader.py" \
    --mock --week current \
    --output "$WORKSPACE/outputs/demo_weekly_status.md"
echo ""
echo "   ✅ Output: outputs/demo_weekly_status.md"
sleep 3

# ─── SKILL 2 ──────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SKILL 2: GSC Insights Analyzer"
echo "   GSC API → Quick Wins, Giảm hạng, Cannibalization → .xlsx + .md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 2
echo ""
"$PYTHON" "$WORKSPACE/.claude/skills/gsc-insights/scripts/gsc_analyzer.py" \
    --domain seongon.com --mock \
    --output-dir "$WORKSPACE/outputs"
echo ""
echo "   ✅ Output: outputs/seongon.com_gsc_insights_*.xlsx + *_insights_summary.md"
sleep 3

# ─── SKILL 3 ──────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SKILL 3: Client Monthly Report — Viettel Store"
echo "   GSC + GA4 + Ahrefs → báo cáo SEO tháng 15 slides .pptx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 2
echo ""
"$PYTHON" "$WORKSPACE/.claude/skills/client-report-monthly/scripts/report_generator.py" \
    --client "Viettel Store" --domain viettelstore.vn \
    --month 2026-04 --brand viettel_store --mock \
    --output-dir "$WORKSPACE/outputs"
echo ""
echo "   ✅ Output: outputs/Viettel_Store_SEO_Report_2026-04.pptx"
sleep 3

# ─── OUTPUT SUMMARY ───────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ HOÀN TẤT! Các file output đã tạo:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -lh "$WORKSPACE/outputs/" | grep -v "^total" | grep -v "samples"
sleep 3

# ─── OUTRO ────────────────────────────────────────────────────────────────────
echo ""
echo "🎉 ================================================"
echo "🎉   SEONGON Claude Workspace — Demo hoàn tất!"
echo "🎉   3 skills chạy thành công với mock data ✅"
echo "🎉   GitHub: https://github.com/ctvcontentseongon-afk/bai-tap-3"
echo "🎉 ================================================"
echo ""

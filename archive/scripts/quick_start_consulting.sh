#!/bin/bash
# 咨询报告PPT生成 - 快速开始脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "咨询报告PPT生成 - 优化工作流"
echo "=========================================="
echo ""

# 检查JSON文件
JSON_FILE="${1:-data/ai_agent_report_slides.json}"
if [ ! -f "$JSON_FILE" ]; then
    echo "❌ 错误: 找不到JSON文件 $JSON_FILE"
    exit 1
fi

echo "📄 使用JSON文件: $JSON_FILE"
echo ""

# Step 1: 分析页面类型
echo "Step 1/4: 分析页面类型..."
uv run scripts/0-analyze_page_types.py "$JSON_FILE"
ENRICHED_FILE="${JSON_FILE%.json}_enriched.json"
echo "✓ 完成,生成了 $ENRICHED_FILE"
echo ""

# Step 2: 生成slide_prompt(使用咨询专用meta-prompt)
echo "Step 2/4: 生成slide_prompt..."
echo "使用咨询报告专用meta-prompt"

# 询问用户是否要测试模式
read -p "是否只生成前5页进行测试? (y/N): " TEST_MODE
if [[ $TEST_MODE =~ ^[Yy]$ ]]; then
    PAGES_ARG="--first-n 5"
    echo "📝 测试模式: 只生成前5页"
else
    PAGES_ARG="--pages 1-40"
    echo "📝 完整模式: 生成全部页面"
fi

uv run scripts/1-generate_slide_prompts.py \
    --json-file "$ENRICHED_FILE" \
    --meta-prompt-file docs/prompts/slide_prompt_meta_prompt_consulting.md \
    --no-tui $PAGES_ARG

echo "✓ Slide prompt生成完成"
echo ""

# Step 3: 质量验证
echo "Step 3/4: 质量验证..."
uv run scripts/validate_slide_quality.py "$ENRICHED_FILE"
echo ""

# 询问是否继续生成图片
read -p "质量验证完成,是否继续生成图片? (Y/n): " CONTINUE
if [[ $CONTINUE =~ ^[Nn]$ ]]; then
    echo "已取消图片生成"
    exit 0
fi

# Step 4: 生成图片
echo "Step 4/4: 生成图片..."

# 询问是否使用并发
read -p "是否使用并发生成(4个线程)? (Y/n): " USE_WORKERS
if [[ $USE_WORKERS =~ ^[Nn]$ ]]; then
    WORKERS_ARG=""
else
    WORKERS_ARG="--workers 4"
    echo "🚀 使用4个并发线程"
fi

uv run scripts/2-generate_images.py \
    --json-file "$ENRICHED_FILE" \
    --no-tui $PAGES_ARG $WORKERS_ARG

echo ""
echo "=========================================="
echo "✓ 全部完成!"
echo "=========================================="
echo ""
echo "生成的图片位于: output/generated_images_*/"
echo "质量报告位于: ${ENRICHED_FILE%.json}_quality_report.json"
echo ""

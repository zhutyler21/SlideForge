# 咨询报告PPT生成优化指南

## 核心优化点总结

### 1. 视觉层次强化
- ✅ 新增咨询专用图表模板库 (`docs/prompts/consulting_chart_templates.md`)
- ✅ 定义SCQA框架与图表类型的映射关系
- ✅ 建立页面类型分类系统(封面/章节页/内容页/总结页等)

### 2. 提示词工程优化
- ✅ 创建咨询报告专用meta-prompt (`slide_prompt_meta_prompt_consulting.md`)
- ✅ 内置图表选型逻辑,根据内容自动推荐合适的可视化方式
- ✅ 强化grid布局系统,确保版式一致性

### 3. 质量保障体系
- ✅ 页面类型自动分析脚本 (`0-analyze_page_types.py`)
- ✅ Slide prompt质量验证脚本 (`validate_slide_quality.py`)
- ✅ 自动检测常见问题(缺少图表、颜色使用不当、重复描述等)

## 推荐工作流

### 标准流程(适合新项目)

```bash
# Step 1: 分析页面类型
uv run scripts/0-analyze_page_types.py data/your_slides.json

# Step 2: 使用咨询专用meta-prompt生成slide_prompt
uv run scripts/1-generate_slide_prompts.py \
  --json-file data/your_slides_enriched.json \
  --meta-prompt-file docs/prompts/slide_prompt_meta_prompt_consulting.md \
  --no-tui --pages 1-40

# Step 3: 验证质量
uv run scripts/validate_slide_quality.py data/your_slides_enriched.json

# Step 4: 如果质量达标(平均分>80),生成图片
uv run scripts/2-generate_images.py \
  --json-file data/your_slides_enriched.json \
  --no-tui --pages 1-40 --workers 4
```

### 迭代优化流程(适合已有项目)

```bash
# Step 1: 验证现有slide_prompt质量
uv run scripts/validate_slide_quality.py data/ai_agent_report_slides.json

# Step 2: 找出得分<80的页面,重新生成
# 假设验证报告显示第5,12,23页需要改进
uv run scripts/1-generate_slide_prompts.py \
  --meta-prompt-file docs/prompts/slide_prompt_meta_prompt_consulting.md \
  --no-tui --pages 5,12,23 --overwrite

# Step 3: 再次验证
uv run scripts/validate_slide_quality.py data/ai_agent_report_slides.json

# Step 4: 只重新生成改进过的页面图片
uv run scripts/2-generate_images.py --no-tui --pages 5,12,23 --overwrite
```

## 咨询报告质量标准

### 必须满足的要求(否则扣分)
1. ✅ 使用grid定位语法 (upper-left, middle-center等)
2. ✅ 内容页必须包含实质性图表(表格/矩阵/流程图等)
3. ✅ 使用consulting green (#2E9B6F)高亮关键信息
4. ✅ 避免重复metadata中的全局规则
5. ✅ 中文内容用引号标注

### 推荐的最佳实践
1. 📊 **图表优先**: 能用图表就不用纯文字
2. 🎨 **颜色语义化**:
   - #2E9B6F = 关键结论/优势
   - #1E3A5F = 结构框架
   - #E7F3EE = 背景高亮
3. 📐 **信息密度**: 每页至少1个主图表 + 1个辅助元素
4. 🔄 **SCQA映射**:
   - Situation → 时间线/对比表
   - Complication → SWOT/矩阵
   - Question → 流程图/框架
   - Answer → 洞察框/行动建议

## 常见问题与解决方案

### Q1: 生成的图片文字模糊或中文显示不全
**原因**: DALL-E 3对中文支持有限

**解决方案**:
1. 在slide_prompt中用引号明确标注中文内容
2. 关键文字使用"大号字体"、"bold"等描述
3. 考虑后期使用脚本叠加清晰文字层

### Q2: 页面风格不一致
**原因**: 每页的slide_prompt描述差异过大

**解决方案**:
1. 确保metadata.master_template定义完整
2. 使用统一的meta-prompt生成所有页面
3. 运行质量验证脚本检查一致性

### Q3: 图表类型选择不当
**原因**: AI未能正确理解内容逻辑

**解决方案**:
1. 先运行`0-analyze_page_types.py`获取推荐
2. 在JSON中手动添加`suggested_charts`字段
3. 修改meta-prompt,明确指定图表类型

### Q4: 信息密度不够,页面显得空洞
**原因**: slide_prompt过于简化

**解决方案**:
1. 参考`consulting_chart_templates.md`中的模板
2. 确保每页包含:主图表 + 辅助元素 + 结论框
3. 使用"spanning 3 columns"充分利用空间

## 进阶技巧

### 1. 批量优化特定类型页面
```bash
# 只重新生成所有"对比分析"类型的页面
# 需要先在JSON中标注page_type
uv run scripts/1-generate_slide_prompts.py \
  --pages $(jq -r '.slides[] | select(.page_type=="comparison") | .page' data/slides.json | tr '\n' ',')
```

### 2. A/B测试不同meta-prompt
```bash
# 生成两个版本对比
uv run scripts/1-generate_slide_prompts.py \
  --meta-prompt-file docs/prompts/version_a.md \
  --json-file data/slides.json \
  --pages 10

uv run scripts/1-generate_slide_prompts.py \
  --meta-prompt-file docs/prompts/version_b.md \
  --json-file data/slides_v2.json \
  --pages 10

# 对比生成的图片,选择更好的版本
```

### 3. 自定义图表模板
在`consulting_chart_templates.md`中添加你的行业专用图表:

```markdown
### 金融风控矩阵
\```
middle-center: 2x2风控矩阵,横轴"风险等级",纵轴"影响范围",
四象限标注("低风险低影响|高风险低影响|低风险高影响|高风险高影响"),
散点标注具体风险项,#2E9B6F标注已缓解项,#FF6B6B标注待处理项
\```
```

## 性能优化建议

### 生成速度优化
- 使用`--workers 4`并发生成(40页约10-15分钟)
- 先用`--first-n 3`测试效果,再批量生成
- 利用`--overwrite`选择性重新生成问题页面

### 成本优化
- 使用`validate_slide_quality.py`避免重复生成
- 优化meta-prompt减少token消耗
- 考虑使用更便宜的模型生成slide_prompt(如gpt-4o-mini)

### 质量优化
- 建立自己的图表模板库
- 定期review生成效果,迭代meta-prompt
- 使用质量验证脚本建立CI/CD流程

## 下一步计划

### 短期(已完成)
- ✅ 咨询图表模板库
- ✅ 页面类型分析脚本
- ✅ 质量验证脚本
- ✅ 咨询专用meta-prompt

### 中期(建议实现)
- [ ] 图片后处理脚本(叠加清晰文字层)
- [ ] 自动化版式检查(确保母版一致性)
- [ ] 多风格切换系统(McKinsey/BCG/Bain风格)
- [ ] 交互式图表编辑器

### 长期(探索方向)
- [ ] 基于Claude Computer Use的自动PPT组装
- [ ] 实时预览系统
- [ ] 协同编辑功能
- [ ] 模板市场

---

**核心理念**: 咨询报告PPT的本质是"用视觉语言讲述商业逻辑",每一页都应该是一个独立的论证单元,而不是装饰性的展示。

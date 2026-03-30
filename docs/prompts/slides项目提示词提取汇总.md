# slides 项目提示词提取汇总

- 源仓库: https://github.com/AAAAAAAJ/slides
- 提取时间: 2026-03-27
- 提取范围: `PROMPTS.md`、`prompts/content-generator.md`、`styles/*.json`、`demos/yc-intro/README.md`、`scripts/extract-colors.py`
- 说明: 为了覆盖“项目中的每个提示词”，下方保留了项目里出现的完整 Prompt、模板 Prompt、Negative Prompt，以及示例 Prompt。存在重复或同风格变体时，按来源分别保留。

## 1. PROMPTS.md 中的 11 个完整风格 Prompt

### 1. Retro Pop Art (复古波普)
来源: `PROMPTS.md`
```text
Retro pop art style PPT slide, 1970s magazine aesthetic, flat design with thick black outlines, cream beige background, bold title text, subtitle below, key statistics displayed as cards, Salmon pink #FF6B6B, sky blue #4ECDC4, mustard yellow #FFD93D, mint green #6BCB77 accents, Geometric decorations: quarter circles, concentric rings, star bursts, Bold sans-serif typography, Professional presentation design, 16:9
```

### 2. Minimalist Clean (极简主义)
来源: `PROMPTS.md`
```text
Minimalist clean design PPT slide, White background, generous whitespace, centered title text, subtitle below, key stats in simple cards, Subtle gray and blue accents, Thin elegant lines, Inter Helvetica font, Professional corporate presentation, Simple elegant layout, 16:9
```

### 3. Cyberpunk Neon (赛博朋克)
来源: `PROMPTS.md`
```text
Cyberpunk neon style PPT slide, Dark charcoal background, title text with neon glow effect, subtitle below, Neon colors: magenta #FF00FF, cyan #00FFFF, yellow #FFFF00, Tech grid patterns, circuit decorations, Holographic data panels, glow effects, Futuristic UI elements, Digital presentation, 16:9
```

### 4. Neo-Brutalism (新粗野主义)
来源: `PROMPTS.md`
```text
Neo-brutalism style PPT slide, raw design, Cream background, bold title text, subtitle below, key stats displayed, Bold primary colors: red #FF4D4D, blue #4D94FF, yellow #FFD93D, Thick 4px black outlines, hard shadows, Brutalist frames, bold typography, Stark contrast, 16:9
```

### 5. Acid Graphics Y2K (酸性设计)
来源: `PROMPTS.md`
```text
Acid graphics Y2K style PPT slide, Light gray background, title text, subtitle below, key stats in stylized cards, Metallic chrome elements, holographic accents, Colors: purple #B185FF, pink #FF6EC7, mint #7BFFCB, gold #FFD700, Liquid shapes, star sparkles, mesh gradients, Y2K aesthetic, futuristic design, 16:9
```

### 6. Modern Minimal Pop (现代极简波普)
来源: `PROMPTS.md`
```text
Modern minimal pop art PPT slide, Instagram aesthetic, Pastel background, title text, subtitle below, key stats displayed, Pastel colors: mint #A8E6C8, cream #FFF4BD, coral #FF8B7A, purple #8B7AFF, Star burst graphics, thin line circles, Tilted color blocks, small arrows, Clean sans-serif typography, Swiss design influence, 16:9
```

### 7. Swiss International (瑞士国际主义)
来源: `PROMPTS.md`
```text
Swiss international style PPT slide, brutalist graphic design, Light gray background, bold title text, subtitle with diagonal layout, key stats in geometric blocks, High saturation colors: blue #007AFF, green #00994D, yellow #FFF066, purple #9966FF, pink #FF3399, orange #FF8800, Helvetica font, Asymmetric composition, 16:9
```

### 8. Dark Editorial (暗黑编辑出版)
来源: `PROMPTS.md`
```text
Dark editorial PPT slide, New York Times Sunday Review style, Black background with white dot grid pattern, title text in white, subtitle below, white text, orange accent #E85D2A, Minimalist wireframe illustrations, Serif typography, Dramatic negative space, Newspaper aesthetic, 16:9
```

### 9. Design Blueprint (设计蓝图)
来源: `PROMPTS.md`
```text
Design blueprint PPT slide, Figma documentation style, White background with cyan grid lines #66B8CC, title text, subtitle below, Figma selection boxes with control points, Annotation lines, numbered labels, Technical UI mockup aesthetic, Clean sans-serif Inter font, 16:9
```

### 10. Neo-Brutalist UI (粗野主义 UI)
来源: `PROMPTS.md`
```text
Neo-brutalist UI PPT slide, dashboard interface design, Cream background, title text, subtitle below, stats in cards, Pastel panels: mint #A8E4CF, yellow #FFD93D, lavender #E5B3FF, Thick 3px black outlines, Card-based layout, flat colors, Bold typography, Contemporary SaaS dashboard aesthetic, 16:9
```

### 11. Y2K Pixel Retro (Y2K 像素复古)
来源: `PROMPTS.md`
```text
Y2K pixel retro PPT slide, 1990s aesthetic, Dark background with noise texture, title text in pixel font, subtitle below, Bright colors: yellow #FFD700, orange #FF8C00, green #4A7C4E, Pixel art computer icons, CRT monitor graphics, Isometric tech illustrations, VT323 pixel font style, Vintage 1990s design, 16:9
```

## 2. styles/*.json 中的风格模板 Prompt

### Acid Graphics (`acid-graphics`)
来源: `styles/acid-graphics.json`

正向模板:
```text
Acid graphics style, Y2K aesthetic, metallic chrome elements, {background} background, {palette} colors, liquid shapes, holographic accents, mesh gradients, star sparkles, futuristic, --ar {aspect_ratio} --style raw --v 6
```

负向模板:
```text
vintage, retro, rustic, natural, organic, minimalist, brutalist, earth tones, muted colors, traditional
```

### Cyberpunk Neon (`cyberpunk-neon`)
来源: `styles/cyberpunk.json`

正向模板:
```text
Cyberpunk style, neon lights, dark background {background}, vibrant colors {palette}, glow effects, tech grids, futuristic UI elements, scanlines, holographic accents, --ar {aspect_ratio} --style raw --q 2
```

负向模板:
```text
bright background, pastel colors, vintage, retro, rustic, natural, organic, hand-drawn, watercolor, minimalist
```

### Dark Editorial Minimalism (`dark-editorial`)
来源: `styles/dark-editorial.json`

正向模板:
```text
Dark editorial design, New York Times style, black background {background} with white dot grid pattern, minimalist line art illustration, white outline wireframe, {palette} accent, dramatic negative space, clean serif typography, sophisticated intellectual aesthetic, --ar {aspect_ratio} --style raw --v 6
```

负向模板:
```text
bright background, colorful, gradients, drop shadows, 3D, casual, playful, sans-serif, brutalist
```

### Design Blueprint (`design-blueprint`)
来源: `styles/design-blueprint.json`

正向模板:
```text
Design process documentation, Figma blueprint style, white background, cyan grid lines #66B8CC, selection boxes with control points, numbered labels, technical annotation style, UI/UX design mockup aesthetic, clean sans-serif typography, blurred content placeholders, --ar {aspect_ratio} --style raw --v 6
```

负向模板:
```text
photorealistic, decorative, vintage, grunge, shadows, gradients, artistic
```

### Minimalist Clean (`minimalist-clean`)
来源: `styles/minimal.json`

正向模板:
```text
Minimalist design, clean aesthetic, white background {background}, subtle shadows, {palette} accent colors, thin lines, sans-serif typography, generous whitespace, professional layout, --ar {aspect_ratio} --style raw
```

负向模板:
```text
gradients, heavy shadows, cluttered, ornate, decorative, vintage, retro, colorful, neon, thick borders
```

### Modern Minimal Pop (`modern-minimal-pop`)
来源: `styles/modern-minimal-pop.json`

正向模板:
```text
Modern minimal pop art style, Instagram post template, {background} background, pastel colors {palette}, star burst graphics, thin line circles, tilted color blocks, small arrows, minimalist icons, clean sans-serif typography, flat design, Swiss design influence, contemporary aesthetic, --ar {aspect_ratio} --style raw
```

负向模板:
```text
gradients, drop shadows, 3D effects, bevels, photorealistic, vintage, grunge, cluttered, thick black outlines, retro textures
```

### Neo-Brutalism (`neo-brutalism`)
来源: `styles/neo-brutalism.json`

正向模板:
```text
Neo-brutalism style, raw design, bold typography, {background} background, primary colors {palette}, thick {outline_width} black outlines, hard shadows, stark contrast, unpolished aesthetic, --ar {aspect_ratio} --style raw
```

负向模板:
```text
gradients, soft shadows, polished, refined, elegant, delicate, ornate, vintage, subtle, pastel
```

### Neo-Brutalist UI (`neo-brutalist-ui`)
来源: `styles/neo-brutalist-ui.json`

正向模板:
```text
Neo-brutalist web UI design, dashboard interface, cream background {background}, pastel color panels {palette}, thick 3px black outlines, card-based layout, flat colors, bold sans-serif typography, contemporary SaaS aesthetic, --ar {aspect_ratio} --style raw --v 6
```

负向模板:
```text
gradients, soft shadows, skeuomorphic, realistic, serif fonts, delicate, ornate, vintage
```

### Retro Pop Art (`retro-pop-art`)
来源: `styles/retro-pop.json`

正向模板:
```text
Retro pop art style, 1970s aesthetic, flat design with thick {outline_width} black outlines, background: {background}, accent colors: {palette}, geometric decorative elements, clean grid layout, no gradients, no shadows, high contrast, bold typography, --ar {aspect_ratio} --style raw
```

负向模板:
```text
gradients, shadows, 3d effects, realistic, photorealistic, blurry, low contrast, pastel colors, neon colors, cluttered layout, thin fonts
```

### Swiss International Style (`swiss-international`)
来源: `styles/swiss-international.json`

正向模板:
```text
Swiss international style poster, brutalist graphic design, bold geometric shapes, diagonal typography layout, high saturation primary colors, {palette}, light gray background {background}, clean sans-serif typography, asymmetric composition, --ar {aspect_ratio} --style raw --v 6
```

负向模板:
```text
gradients, shadows, decorative, ornate, serif fonts, vintage textures, rustic
```

### Y2K Pixel Retro (`y2k-pixel-retro`)
来源: `styles/y2k-pixel-retro.json`

正向模板:
```text
Retro Y2K style design, pixel art aesthetic, dark textured background {background}, bright color blocks {palette}, isometric pixel art computers, 1990s CRT monitor, noise and grain texture, bold condensed typography, memphis design influence, --ar {aspect_ratio} --style raw --v 6
```

负向模板:
```text
modern, clean, minimal, smooth, gradient, photorealistic, 2020s, corporate, sans-serif only
```

## 3. content-generator 内容生成提示词

### 模板
来源: `prompts/content-generator.md`
```markdown
你是一位 [领域] 专家，请根据以下要求生成 PPT 内容：

【主题】[输入你的主题]
【受众】[目标受众描述]
【页数】[期望页数]

要求：
1. 每页必须包含至少 3 个具体数据点
2. 采用「问题 - 分析 - 解决方案」结构
3. 关键结论用粗体标注
4. 复杂概念用类比解释

输出格式：
- 页码
- 页面类型（封面/数据/时间线/要点）
- 标题
- 内容要点（带数据）
- 建议配图
```

### 示例 1：Business Strategy
来源: `prompts/content-generator.md`
```markdown
【主题】如何制定有效的市场进入策略
【受众】初创公司创始人、市场总监
【页数】8 页

要求：
1. 每页必须包含至少 3 个具体数据点
2. 采用「问题 - 分析 - 解决方案」结构
3. 关键结论用粗体标注
```

### 示例 2：Personal Finance
来源: `prompts/content-generator.md`
```markdown
【主题】年轻人理财的第一堂课
【受众】22-30 岁职场新人
【页数】6 页

要求：
1. 每页必须包含至少 3 个具体数据点
2. 用对比数据展示复利效应
3. 关键结论用粗体标注
```

## 4. demos/yc-intro/README.md 中的 11 个演示 Prompt

### 1. Retro Pop Art (复古波普)
来源: `demos/yc-intro/README.md`
```text
Retro pop art style PPT slide, 1970s magazine aesthetic,
flat design with thick 3px black outlines,
cream beige background #F5F0E6,
Title: "What is Y Combinator",
Subtitle: "The World's Most Famous Startup Accelerator",
Stats: "2005" "4000+" "$600B+",
Salmon pink #FF6B6B, sky blue #4ECDC4, mustard yellow #FFD93D, mint green #6BCB77,
Geometric decorations: quarter circles, concentric rings, star bursts,
Bold sans-serif typography, --ar 16:9 --style raw
```

### 2. Minimalist Clean (极简主义)
来源: `demos/yc-intro/README.md`
```text
Minimalist clean design PPT slide,
White background #FFFFFF, generous whitespace,
Title: "What is Y Combinator",
Subtitle: "The World's Most Famous Startup Accelerator",
Stats: "2005 • 4000+ • $600B+",
Subtle gray #F8F9FA, #343A40, blue #007BFF accents,
Thin 1px lines, Inter/Helvetica typography,
Professional corporate aesthetic, --ar 16:9 --style raw
```

### 3. Cyberpunk Neon (赛博朋克)
来源: `demos/yc-intro/README.md`
```text
Cyberpunk neon style PPT slide,
Dark background #0D0D1A,
Title: "What is Y Combinator",
Neon glow text effects,
Neon colors: magenta #FF00FF, cyan #00FFFF, yellow #FFFF00,
Tech grid patterns, circuit decorations,
Holographic data panels, glow effects, scanlines,
Futuristic UI aesthetic, --ar 16:9 --style raw
```

### 4. Neo-Brutalism (新粗野主义)
来源: `demos/yc-intro/README.md`
```text
Neo-brutalism style PPT slide, raw design,
Cream background #FFF8E7,
Title: "What is Y Combinator",
Bold primary colors: red #FF4D4D, blue #4D94FF, yellow #FFD93D,
Thick 4px black outlines, hard shadows,
Brutalist frames, Archivo Black typography,
Stark contrast, unpolished aesthetic, --ar 16:9 --style raw
```

### 5. Acid Graphics Y2K (酸性设计)
来源: `demos/yc-intro/README.md`
```text
Acid graphics Y2K style PPT slide,
Light gray background #E8E8E8,
Title: "What is Y Combinator",
Metallic chrome elements, holographic accents,
Colors: purple #B185FF, pink #FF6EC7, mint #7BFFCB, gold #FFD700,
Liquid shapes, star sparkles, mesh gradients,
Y2K aesthetic, futuristic design, --ar 16:9 --style raw
```

### 6. Modern Minimal Pop (现代极简波普)
来源: `demos/yc-intro/README.md`
```text
Modern minimal pop art PPT slide, Instagram aesthetic,
Pastel background,
Title: "What is Y Combinator",
Pastel colors: mint #A8E6C8, cream #FFF4BD, coral #FF8B7A, purple #8B7AFF,
Star burst graphics, thin line circles,
Tilted color blocks, small L-shaped arrows,
Clean sans-serif typography, Swiss design influence, --ar 16:9 --style raw
```

### 7. Swiss International (瑞士国际主义)
来源: `demos/yc-intro/README.md`
```text
Swiss international style PPT slide, brutalist graphic design,
Light gray background #E5E5E5,
Title: "What is Y Combinator",
Bold geometric color blocks, diagonal typography,
High saturation: blue #007AFF, green #00994D, yellow #FFF066, purple #9966FF, pink #FF3399, orange #FF8800,
Helvetica typography, asymmetric composition,
Japanese contemporary design, --ar 16:9 --style raw
```

### 8. Dark Editorial (暗黑 Editorial)
来源: `demos/yc-intro/README.md`
```text
Dark editorial PPT slide, NY Times Sunday Review style,
Black background #0A0A0F with white dot grid pattern,
Title: "What is Y Combinator",
White text, orange accent #E85D2A,
Minimalist wireframe illustrations,
Serif typography (Georgia style),
Dramatic negative space, sophisticated aesthetic, --ar 16:9 --style raw
```

### 9. Design Blueprint (设计蓝图)
来源: `demos/yc-intro/README.md`
```text
Design blueprint PPT slide, Figma documentation style,
White background, cyan grid lines #66B8CC,
Title: "What is Y Combinator",
Figma selection boxes with control points,
Annotation lines, numbered labels,
Technical UI/UX mockup aesthetic,
Inter font style, --ar 16:9 --style raw
```

### 10. Neo-Brutalist UI (粗野主义 UI)
来源: `demos/yc-intro/README.md`
```text
Neo-brutalist UI PPT slide, dashboard interface,
Cream background #F5F0E6,
Title: "What is Y Combinator",
Pastel panels: mint #A8E4CF, yellow #FFD93D, lavender #E5B3FF,
Thick 3px black outlines #1A1A1A,
Card-based layout, flat colors,
Bold typography, stat cards,
Contemporary SaaS dashboard aesthetic, --ar 16:9 --style raw
```

### 11. Y2K Pixel Retro (Y2K 像素复古)
来源: `demos/yc-intro/README.md`
```text
Y2K pixel retro PPT slide, 90s aesthetic,
Dark background #2D2D2D with noise texture,
Title: "What is Y Combinator",
Bright colors: yellow #FFD700, orange #FF8C00, green #4A7C4E,
Pixel art computer icons, CRT monitor graphics,
Isometric tech illustrations,
VT323/pixel font style, vintage 1990s design, --ar 16:9 --style raw
```

### 手动生成示例中的 CLI Prompt
来源: `demos/yc-intro/README.md`
```text
Retro pop art style PPT slide, 1970s magazine aesthetic, flat design with thick 3px black outlines, cream beige background, Title: What is Y Combinator, Subtitle: The Worlds Most Famous Startup Accelerator, Stats: 2005 4000+ $600B+, salmon pink sky blue mustard yellow accents, geometric decorations, bold typography, --ar 16:9 --style raw
```

## 5. scripts/extract-colors.py 中的自动生成 Prompt

### AI Image Generation Prompt
来源: `scripts/extract-colors.py`
```text
Retro pop art style, 1970s aesthetic,
flat design with thick black outlines,
background: {result["background"]},
accent colors: {" ".join(result["palette"])},
geometric decorative elements,
clean grid layout,
no gradients, no shadows,
high contrast, bold typography,
--ar 16:9 --style raw
```

### Negative Prompt
来源: `scripts/extract-colors.py`
```text
gradients, shadows, 3d effects, realistic,
photorealistic, blurry, low contrast,
pastel colors, neon colors,
cluttered layout, thin fonts
```

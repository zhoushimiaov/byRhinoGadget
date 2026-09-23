# byRhino Gadget · 橙皮书完全参考手册
### The Complete Technical Reference Manual for Rhinoceros 7 & 8

[![Rhino Version](https://img.shields.io/badge/Rhino-7%20%7C%208%20Windows-000000.svg)](https://www.rhino3d.com/)
[![Edition](https://img.shields.io/badge/Edition-v2%20典范版-EA580C.svg)]()
[![Editorial](https://img.shields.io/badge/Editorial-中文版%20edit%20by%20有物建筑%20MeansGroup-000000.svg)](https://means.group)
[![Official Docs](https://img.shields.io/badge/Official-byRhino3D-gray.svg)](https://www.byrhino3d.com/byRhinoGadget/help/index.html)

---

## 📖 项目简介 (Overview)

**byRhino Gadget** 是韩国前沿计算设计与工业设计机构 **PlusPlastic (플러스플라스틱)** 团队打造的官方效能增强插件。该插件沉淀了十余年工业级产品造型与参数化教学经验，旨在补全日常高频建模中繁琐、易错且原生 Rhino 缺失的关键断点。

本书由 **有物建筑（MeansGroup）** 深度编译与策划制作，提供完备的版本迭代矩阵：
- **《byRhino Gadget · 橙皮书》v2 典范版**：**【最新推荐 · v2 典范版 (145 页)】** 建筑专著全版透光流体橙皮封底面、经典 Axon 轴测方盒子线框、超清无噪点（No Grain）流体光焦底色渗透、纯正专业 NURBS 术语体系、全书 472 幅操作图解全量配图步骤说明（步骤 1/2/3 徽章与命令指令）、经典序言《设计工具的克制与效率重构》、全书 372 条交互超链接直达、以及精准对齐实体印刷的物理页码双向检索体系（P. 01 ~ P. 145）。
- **《byRhino Gadget 101》**：【归档探索版 (139 页)】保留探索版排版。
- **《byRhino Gadget 橙皮书（白底经典版）》**：【原版保留 (119 页)】性冷淡极简留白风格，便于办公室黑白双面激光打印。

全书完整囊括官方 **93 个专题页面、472 幅高清操作图解（每图独享步骤说明）与全量 116 条高频增强命令**，提供完备的「功能定义 → 操作步骤 → 参数选项 → 核心要点 → 配图步骤范例 → 关联命令」全维参考，并总结提炼出六大典型高阶工程工作流。

---

## 📂 核心交付文件清单 (File Directory)

| 文件路径 | 格式与规格 | 大小 | 说明 |
| :--- | :--- | :--- | :--- |
| [**byRhinoGadget_Orange_Book_v2.pdf**](./byRhinoGadget_Orange_Book_v2.pdf) | **PDF 矢量印制版 (145 页)** | **17.8 MB** | **【最新主推 · v2 典范版】** 半透流体橙皮封面封底、经典 Axon 方盒子、设计工具克制与效率重构序言、472 图每图配置步骤指令、实体物理页码索引、372 条无损活链接。 |
| [**byRhinoGadget_Orange_Book_v2.html**](./byRhinoGadget_Orange_Book_v2.html) | **HTML 单页排版源码** | **367 KB** | v2 交互排版网页，可在任何浏览器中点击导航跳转，亦可直接通过 Ctrl+P 导出 PDF。 |
| [build_orange_book_v2.py](./build_orange_book_v2.py) | Python 重构管线 | 80 KB | v2 双阶段编译、图表步骤配文注入、实体页码提取注入与 Edge 打印导出脚本。 |
| [byRhinoGadget_101.pdf](./byRhinoGadget_101.pdf) | PDF 矢量版 (139 页) | 17.2 MB | 【探索保留】 101 探索版。 |
| [byRhinoGadget_Orange_Book.pdf](./byRhinoGadget_Orange_Book.pdf) | PDF 矢量版 (119 页) | 10.2 MB | 【原版保留】 白底经典版，极简留白风格。 |
| [assets/cover_bg_nograin.png](./assets/cover_bg_nograin.png) | 封面背景纹理 | 816 KB | 无噪点（No Grain）超清流体光焦底图。 |
| [assets/icons/](./assets/icons/) | PNG 图标目录 | 116+ 项 | 官方 32×32 像素彩色工具栏图标。 |
| [assets/images/](./assets/images/) | PNG 图解目录 | 472 项 | 官方原版高清操作演示与模型案例图。 |
| [help_pages/](./help_pages/) | HTML 原版归档 | 95 篇 | 抓取并完整归档的官方韩文原版技术帮助网页。 |

---

## 🏛 知识体系架构 (Contents Matrix)

全书划分为 **15 个正文章节** 与 **3 大附录**：

1. **第一章 · 插件概述 (Overview & Background)**
   - 官方背景、核心定位、研发团队与支持版本。
2. **第二章 · 设计理念与交互约定 (Design Philosophy & Conventions)**
   - 交互模式约定（Command-first / Auto-preview / Escape）、命名与快捷键哲学。
3. **第三章 · 全局命令体系总览矩阵 (Global Command Matrix)**
   - 11 大功能领域、116 条命令全景对照速查表（101 版支持全表超链接直达对应词条）。
4. **第四章 · 控制点编辑 (Point Edit Tools - 11 条)**
   - PointsDistribute, ControlPointsFlatten, Points2Polyline, ControlPointsRound 等。
5. **第五章 · 曲线工具 (Curve Tools - 17 条)**
   - ExtendCurveDouble, FilletCornersBatch, FlowMulti, SelectClosedCurves 等。
6. **第六章 · 曲面工具 (Surface Tools - 3 条)**
   - FilletSrfMultiple, SurfaceIsoparmToggle, Sweep1Advanced 等。
7. **第七章 · 实体建模 (Solid Modeling - 5 条)**
   - BooleanDifferenceBatch, CapMultiple, ShellInteractive 等。
8. **第八章 · 标注与出图 (Annotation & Layout - 12 条)**
   - AddCallouts, CircleCenterPoints, DimBoundingBox, DotZ, ThirdAngleLayout 等。
9. **第九章 · 文件与图层管理 (File & Layer Tools - 6 条)**
   - ExportEachLayer, ImportFilesInFolder, ExplodeBlockInSameLayer, MergeLayers 等（独立起始页排版）。
10. **第十章 · 空间变换 (Transform Tools - 14 条)**
    - ArrayOnSurfaceNormal, Orient3PtBatch, TwistWithAxis, Scale1DZero 等。
11. **第十一章 · 建模与造型细节 (Modeling & Features - 19 条)**
    - 工业设计外观高频倒角、缝隙槽线、结构特征工具。
12. **第十二章 · 视口显示与设置 (Display & Settings - 19 条)**
    - 快速切换渲染模式、隐藏锁定快捷过滤、环境照明预设。
13. **第十三章 · 物理分析与测算 (Physical Analysis - 8 条)**
    - 表面曲率分析、拔模角检查、间隙干涉碰撞、重心体积测算。
14. **第十四章 · 官方技术支持与帮助 (Help & Support - 2 条)**
    - byRhinoGadgetHelp, byRhinoGadgetVersion。
15. **第十五章 · 六大典型高阶工作流 (Typical Workflows)**
    - 工业产品分件缝隙处理、多曲线批量流动匹配、工程出图与三视图自动标高、装配体图层拆分导出等。
- **附录 A · 核心术语与参数对照表 (Glossary of Terms)**
  - 规范中文术语、以「英文 (韩文原文)」严格对照，结合工业建模实践给出工程释义。
- **附录 B · 官方技术资源与生态 (Resources & Ecosystem)**
- **附录 C · 英文命令字母序 (A–Z) 全书检索索引 (Alphabetical Index)**
  - 116 条命令字母序索引，含全量可点击页码/锚点跳转。

---

## 🛠 本地重新构建指南 (Build Instructions)

本项目内置全自动化的 HTML 渲染与 Chromium PDF 打印管线：

### 运行环境需求
- **Python 3.10+** (依赖包: `beautifulsoup4`, `requests`, `PyMuPDF`)
- **Microsoft Edge** 或 Chrome (用于调用无头打印引擎导出保真矢量 PDF)

### 重新生成 v2 典范版手册
在项目根目录下执行：
```bash
python build_orange_book_v2.py
```
该命令会自动完成：
1. 载入 93 篇韩文原版技术文档与结构化文稿，智能解析 116 条命令；
2. 注入无噪点流体光焦纹理（`assets/cover_bg_nograin.png`）通栏满版封底面，以建筑专著纯白卡纸与 Axon 轴测方盒子为视觉核心；
3. 全文规范采用专业“NURBS”标准称谓，沿用经典“byRhino Gadget 橙皮书”命名体系；
4. 构建纯 ASCII 交互锚点，全量注入 372 条原生无损超级链接（359 项内部定位直达 + 13 项外部官网直达）；
5. 运行两阶段编译，调用 PyMuPDF 逐页逆向提取正文实体印刷页码，将精准物理页号动态回填至目录、速查表和 A–Z 索引；
6. 调用 Edge 无头打印引擎生成 145 页出版级矢量 PDF。

---

## ⚖ 版权与致谢 (Credits & Legal)

- **原著研发机构**: **PlusPlastic Co., Ltd. (플러스플라스틱)**
  - 官方技术站点: [www.byrhino3d.com](https://www.byrhino3d.com)
  - 帮助文档中心: [byRhino Gadget 在线帮助](https://www.byrhino3d.com/byRhinoGadget/help/index.html)
  - 资质: Rhino Authorized Partner & Training Center (Since 2005)
  - Copyright © 2023 PlusPlastic. All rights reserved.

- **中文版策划与编译**: **中文版 edit by 有物建筑 MeansGroup**
  - 机构站点: [means.group](https://means.group)
  - 策划宗旨: 探索建筑与计算设计的深层工具逻辑，传递高品质设计工程方法论。

- **商标声明**:
  - *Rhinoceros*、*Rhino* 及其相关徽标均为 Robert McNeel & Associates 的注册商标。

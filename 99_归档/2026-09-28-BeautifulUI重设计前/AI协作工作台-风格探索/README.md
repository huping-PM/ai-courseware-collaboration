# 内容协作智能体 · 灵感工作室

当前只交付内容协作智能体，默认入口[index.html](index.html)。[原型图与核验](../../06_交付与验证/AI协作工作台UI风格方案/index.html) · [方案说明](../../03_功能设计/AI协作独立工作台-UI重构方案.md)。

## B 内容协作智能体当前结构（2026-09-28）

- 当前 B 仅显示内容协作智能体，顶部没有资源管理、智能体配置入口；第二层面包屑整栏已删除。项目上下文放在单层顶栏。
- 旧 `?style=b&page=resources`、`page=agents` 深链接归一为 `page=workspace`。A/C 保留历史页面，不是当前主方案的额外模块。
- 左侧 220px 会话记录，40px 单行：会话名称在左，AI 执行状态 SVG 图标在右。进行中使用时钟、已完成使用勾，均有 title 与 aria-label；不是业务任务状态或审核状态。
- “新增会话”加号 SVG 可打开名称输入，确认后创建独立空会话并选中，旧会话继续保留。新会话未执行时不展示状态图标；发送后的状态变化仅是预置 AI 执行反馈演示。
- 会话间隔离名称、输入草稿、引用、聊天内容、成果选择与筛选；客户沟通基础课保留完整讲稿和三类成果，其他会话没有跨用它的内容。未保存文稿切换会话时保留保存并切换、放弃修改、继续编辑三种处理。
- 底部成果条总高 94px，三类竖排筛选各 25px，成果缩略图和文档卡高 60px。筛选单选，再次点击当前类型取消；只改变清单，不改变画布。文档图标和文件名、图片纯缩略图、视频首帧与播放标识继续保留。
- 右侧对话宽 400px；参考资料、技能选择与总结经验仍在协作内操作中保留，不新增管理页面。
- 默认入口 `?style=b&page=workspace`，默认会话 `s-communication`；可追加 `session=s-opening|s-structure|s-exercise` 直达其他会话，媒体参数 `asset=image|video` 继续支持默认会话。旧 task 参数不再作为会话标识。
- 测试选择器：会话 `[data-session-id]`；新增 `#newSessionButton`、名称 `#newSessionName`、确认 `#confirmNewSession`；搜索 `#sessionSearch`；当前画布 `#documentPane[data-session-id]`；三类筛选和成果继续使用 `[data-output-filter]`、`[data-output-type]`。
- 会话隔离使用当前页面内存，文档保存仍为浏览器演示；不代表真实 AI、多人协作、后端持久化或业务任务状态更新。A/C 行为不变。


原型制作源仍保留A/C与其他模块的历史代码供追溯，不在当前预览中提供入口；旧B资源/配置深链接统一进入协作。当前出图/核验使用交付目录verify-collaboration.cjs，旧capture.cjs、verify.cjs、verify-studio.cjs仅适用历史三模块/任务栏方案，不作为当前验收脚本。

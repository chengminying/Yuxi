# 官方主线与企业定制同步

## 目标

在完整保留现有企业定制的前提下，将官方仓库 `xerrors/Yuxi` 的最新 `main` 合入本地 `deploy-main`，并将验证通过的唯一提交推送到 `chengminying/Yuxi`，供服务器后续按固定提交部署。

## 范围与约束

- 保留企业品牌、0.6.2 数据无损迁移、国内依赖镜像、MinIO 端口、Neo4j 健康等待及 MinerU 固定版本等现有定制。
- 合入官方最新安全修复、功能更新、测试与文档，不额外重构无关代码。
- 本地未跟踪的功能测试资料包属于测试数据，不纳入代码仓库。
- 合并结果以 Git commit SHA 为唯一部署基准；服务器更新前必须先备份数据库、对象存储、环境文件和持久化数据。

## 验收标准

- [x] `deploy-main` 同时包含合并前企业定制提交和最新 `upstream/main`。
- [x] 所有合并冲突均按业务语义解决，仓库中不存在冲突标记。
- [x] 企业定制相关关键文件和变更记录仍然存在。
- [x] Docker Compose 服务正常，相关单元测试、集成测试、端到端测试及变更范围 Lint 通过。
- [x] 合并提交已推送到 `chengminying/Yuxi`，远端提交与本地一致。
- [x] 提供服务器按固定提交升级、回滚和一致性验证步骤。

## 验证结果

- 后端单元测试：`1205 passed, 1 skipped`。
- 真实 API 集成测试：`195 passed, 5 skipped`；跳过项依赖未配置的可选外部能力。
- MCP 安全、文件系统和个人 Skill Agent 关键 E2E：`6 passed`。
- 前端单元测试：`10 passed`；前端 ESLint 通过。
- 本次变更及最新上游变更涉及的 Python 文件 Ruff 通过，`git diff --check` 通过。
- API 健康检查返回 HTTP 200；所有一次性测试管理员均已删除，残留数为 0。

## 服务器固定提交升级与回滚

以下命令在服务器仓库目录执行，将 `<FINAL_COMMIT>` 替换为 GitHub `main` 最终确认的完整 SHA。

1. 记录旧提交并创建独立备份目录，备份 `.env`、Compose 文件、PostgreSQL 和 `docker/volumes`。
2. 从 `chengminying/Yuxi` 获取代码，检出 `<FINAL_COMMIT>`，使用 `git rev-parse HEAD` 核对固定提交。
3. 执行 `docker compose up -d --build`，再检查 `docker compose ps`、API 健康接口和 API/worker/web 日志。
4. 若升级失败，重新检出备份中记录的旧提交并执行 `docker compose up -d --build`；若数据库迁移已经发生，则先停应用服务，再恢复与旧提交同一时间点的 PostgreSQL 和持久化数据备份。

服务器不应直接部署未固定的浮动分支；GitHub `main` 用于获取代码，实际部署以经验证的完整 commit SHA 为准。



## 获取和使用数据

当前分支的数据使用普通 Git 保存，不需要 Git LFS。小于 100,000,000 字节的原数据、面板表、结果表和 PDF 直接按原路径跟踪。较大 CSV 按原始字节拆成分片，每片最多 95,000,000 字节；清单位于 `data_parts/manifest.json`。

克隆本分支后，在仓库根目录执行：

```bash
python3 scripts/data_parts.py restore
```

命令会校验分片并在原路径重建 CSV。重建后的文件与原文件的字节数和 SHA256 一致，编码、BOM、表头、引号和换行均保留，原有 Stata/Python/R 读取路径不需要修改。已有且校验一致的 CSV 会跳过；已有但内容不同的文件会保留并报错，避免覆盖修改。

这些分片是二进制片段，不能各自作为完整 CSV 读取，也不要用 pandas.concat 直接拼接分片。恢复后的大 CSV 已按精确路径加入忽略规则；提交的是分片与清单。

仅验证分片而不生成 CSV：

```bash
python3 scripts/data_parts.py verify
```

## 数据更新与提交

修改大 CSV 后，先将旧 `data_parts/manifest.json` 备份到仓库外（工具默认拒绝覆盖不同版本的清单），再使用 `scripts/data_parts.py split --source-root . --paths-json <清单.json>` 重新生成分片。输入为 JSON 列表，每项包含 `path`、`size` 和 `sha256`，应填写修改后文件的实际大小和哈希；输出清单和分片仍保存在 `data_parts/`。提交新清单和新分片，不提交重建的大 CSV。旧清单不再引用的分片应在核对后移除，避免保留重复数据。

安装本仓库的提交检查：

```bash
git config core.hooksPath .githooks
```

也可以随时手动检查暂存区：

```bash
python3 scripts/sync_git_lfs_by_size.py --check
```

检查会拒绝残留 LFS 指针、大小达到 100,000,000 字节的 Git 文件，以及未解决的合并冲突；不会自动修改数据或暂存区。脚本名称为兼容原有工作流保留。

## 历史版本

这次迁移仅改变新提交的保存方式，不改写既有提交。旧提交中的 LFS 对象和远程 LFS 用量仍然保留；检出旧版本时可能仍需要 Git LFS。
